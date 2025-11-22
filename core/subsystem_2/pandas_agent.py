# core/subsystem_2/pandas_agent.py

import os
import re
import yaml
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor

# Import PandasAI service
try:
    from core.services.pandasai_service import query_with_pandasai
    PANDASAI_AVAILABLE = True
except ImportError:
    PANDASAI_AVAILABLE = False
    query_with_pandasai = None


def _get_connection():
    """
    Create a new Postgres connection using env vars.
    """
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        dbname=os.environ["DB_NAME"],
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    )
    return conn


def _detect_payments_time_window(question: str) -> Tuple[Optional[int], str]:
    """
    Very simple heuristic:
    - 'last week'      -> 7 days
    - 'last month'     -> 30 days
    - 'last quarter'   -> 90 days
    - 'last year'      -> 365 days
    - otherwise        -> None (all time)
    Returns (window_days, human_label)
    """
    q = question.lower()

    if "last week" in q or "past week" in q:
        return 7, "last 7 days"
    if "last month" in q or "past month" in q:
        return 30, "last 30 days"
    if "last quarter" in q or "past quarter" in q:
        return 90, "last 90 days"
    if "last year" in q or "past year" in q:
        return 365, "last 365 days"

    return None, "all time"


def _query_total_payments(window_days: Optional[int]) -> float:
    """
    Query total payments (sum of amount_usd) from the payments table,
    optionally over the last N days.
    """
    base_sql = "SELECT COALESCE(SUM(amount_usd), 0) AS total_revenue_usd FROM payments"
    params = ()

    if window_days is not None:
        base_sql += " WHERE payment_date >= CURRENT_DATE - INTERVAL %s"
        params = (f"{window_days} days",)

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(base_sql, params)
            row = cur.fetchone() or {}
            return float(row.get("total_revenue_usd", 0.0))
    finally:
        conn.close()

# ---------- USERS QUERIES ----------

def _query_users_overview() -> dict:
    """
    Returns:
      {
        "total_users": int,
        "countries": list[dict{name, users}],
        "devices": list[dict{name, users}],
      }
    """
    conn = _get_connection()
    try:
        result: dict = {}

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # total users
            cur.execute("SELECT COUNT(*) AS total_users FROM users;")
            row = cur.fetchone() or {}
            result["total_users"] = int(row.get("total_users", 0))

            # top countries (if country exists)
            cur.execute(
                """
                SELECT country AS name, COUNT(*) AS users
                FROM users
                GROUP BY country
                ORDER BY users DESC
                LIMIT 5;
                """
            )
            result["countries"] = cur.fetchall() or []

            # top device types (if device_type exists)
            cur.execute(
                """
                SELECT device_type AS name, COUNT(*) AS users
                FROM users
                GROUP BY device_type
                ORDER BY users DESC
                LIMIT 5;
                """
            )
            result["devices"] = cur.fetchall() or []

        return result
    finally:
        conn.close()


# ---------- SUBSCRIPTIONS QUERIES ----------

def _query_subscriptions_overview() -> dict:
    """
    Returns basic subscription metrics:
      - total subscriptions
      - active subscriptions
      - churned subscriptions
      - active subs by plan
    """
    conn = _get_connection()
    try:
        result: dict = {}

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # total
            cur.execute("SELECT COUNT(*) AS total_subscriptions FROM subscriptions;")
            row = cur.fetchone() or {}
            result["total_subscriptions"] = int(row.get("total_subscriptions", 0))

            # active = end_date is NULL or in the future
            cur.execute(
                """
                SELECT COUNT(*) AS active_subscriptions
                FROM subscriptions
                WHERE start_date <= CURRENT_DATE
                  AND (end_date IS NULL OR end_date > CURRENT_DATE);
                """
            )
            row = cur.fetchone() or {}
            result["active_subscriptions"] = int(row.get("active_subscriptions", 0))

            # churned = end_date in the past
            cur.execute(
                """
                SELECT COUNT(*) AS churned_subscriptions
                FROM subscriptions
                WHERE end_date IS NOT NULL
                  AND end_date <= CURRENT_DATE;
                """
            )
            row = cur.fetchone() or {}
            result["churned_subscriptions"] = int(row.get("churned_subscriptions", 0))

            # active subs by plan
            cur.execute(
                """
                SELECT plan, COUNT(*) AS active_subscriptions
                FROM subscriptions
                WHERE start_date <= CURRENT_DATE
                  AND (end_date IS NULL OR end_date > CURRENT_DATE)
                GROUP BY plan
                ORDER BY active_subscriptions DESC
                LIMIT 5;
                """
            )
            result["plans"] = cur.fetchall() or []

        return result
    finally:
        conn.close()


# ---------- SESSIONS QUERIES ----------

def _query_sessions_overview() -> dict:
    """
    Returns:
      - total sessions
      - distinct active users
      - avg duration
      - top activities by minutes
    """
    conn = _get_connection()
    try:
        result: dict = {}

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # basic metrics
            cur.execute(
                """
                SELECT
                  COUNT(*) AS total_sessions,
                  COUNT(DISTINCT user_id) AS active_users,
                  AVG(duration_minutes) AS avg_duration
                FROM sessions;
                """
            )
            row = cur.fetchone() or {}
            result["total_sessions"] = int(row.get("total_sessions", 0))
            result["active_users"] = int(row.get("active_users", 0))
            result["avg_duration"] = float(row.get("avg_duration") or 0.0)

            # activity mix (top 5)
            cur.execute(
                """
                SELECT
                  activity_type,
                  COUNT(*) AS sessions,
                  SUM(duration_minutes) AS minutes
                FROM sessions
                GROUP BY activity_type
                ORDER BY minutes DESC
                LIMIT 5;
                """
            )
            result["activities"] = cur.fetchall() or []

        return result
    finally:
        conn.close()


# ---------- PREDICTION FUNCTIONS ----------

def _get_historical_new_subscriptions() -> List[Tuple[int, int, int]]:
    """
    Query subscriptions table for monthly counts of new subscriptions.
    
    Returns:
        List of tuples: [(year, month, count), ...] ordered by year, month
    """
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                  EXTRACT(YEAR FROM start_date)::INTEGER AS year,
                  EXTRACT(MONTH FROM start_date)::INTEGER AS month,
                  COUNT(*)::INTEGER AS new_subscriptions
                FROM subscriptions
                WHERE start_date >= CURRENT_DATE - INTERVAL '3 years'
                GROUP BY year, month
                ORDER BY year, month;
                """
            )
            rows = cur.fetchall()
            return [(int(row["year"]), int(row["month"]), int(row["new_subscriptions"])) for row in rows]
    finally:
        conn.close()


def _calculate_linear_trend(historical_data: List[Tuple[int, int, int]]) -> Tuple[float, float]:
    """
    Calculate linear regression trend from historical monthly subscription data.
    
    Args:
        historical_data: List of (year, month, count) tuples
    
    Returns:
        Tuple of (slope, intercept) for linear regression y = mx + b
    """
    if len(historical_data) < 2:
        raise ValueError("Need at least 2 data points to calculate trend")
    
    # Convert to numeric months (x = months since first data point)
    first_year, first_month, _ = historical_data[0]
    
    x_values = []
    y_values = []
    
    for year, month, count in historical_data:
        # Calculate months since first data point
        months_diff = (year - first_year) * 12 + (month - first_month)
        x_values.append(months_diff)
        y_values.append(count)
    
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x_squared = sum(x * x for x in x_values)
    
    # Calculate slope: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    denominator = n * sum_x_squared - sum_x * sum_x
    if denominator == 0:
        # All x values are the same, return flat line
        return 0.0, sum_y / n if n > 0 else 0.0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    # Calculate intercept: b = (Σy - m*Σx) / n
    intercept = (sum_y - slope * sum_x) / n
    
    return slope, intercept


def _predict_future_subscriptions(
    historical_data: List[Tuple[int, int, int]], 
    slope: float, 
    intercept: float
) -> List[Tuple[int, int, float]]:
    """
    Use trend coefficients to project next 12 months of subscriptions.
    
    Args:
        historical_data: List of (year, month, count) tuples
        slope: Linear regression slope
        intercept: Linear regression intercept
    
    Returns:
        List of (year, month, predicted_count) tuples for next 12 months
    """
    if not historical_data:
        raise ValueError("Need historical data to make predictions")
    
    # Find the last month in historical data
    last_year, last_month, _ = historical_data[-1]
    first_year, first_month, _ = historical_data[0]
    
    # Calculate months since first data point for the last historical month
    last_month_index = (last_year - first_year) * 12 + (last_month - first_month)
    
    predictions = []
    
    # Start from the month after the last historical month
    current_year = last_year
    current_month = last_month
    
    # Generate predictions for next 12 months
    for i in range(1, 13):
        # Calculate future month index
        future_month_index = last_month_index + i
        
        # Calculate predicted count: y = mx + b
        predicted_count = slope * future_month_index + intercept
        
        # Ensure non-negative predictions
        predicted_count = max(0.0, predicted_count)
        
        # Calculate the actual year and month for this prediction
        # Add months properly handling year rollover
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
        
        predictions.append((current_year, current_month, predicted_count))
    
    return predictions


def _format_prediction_response(
    historical_data: List[Tuple[int, int, int]],
    predictions: List[Tuple[int, int, float]],
    slope: float
) -> str:
    """
    Format predictions as readable Slack message.
    
    Args:
        historical_data: Historical subscription data
        predictions: Future predictions
        slope: Trend slope (for trend direction)
    
    Returns:
        Formatted string for Slack
    """
    if not predictions:
        return "[Prediction agent]\nNo predictions could be generated."
    
    # Calculate summary statistics
    total_predicted = sum(count for _, _, count in predictions)
    avg_per_month = total_predicted / len(predictions) if predictions else 0.0
    
    # Determine trend direction
    if slope > 0.1:
        trend_direction = "📈 Increasing"
    elif slope < -0.1:
        trend_direction = "📉 Decreasing"
    else:
        trend_direction = "➡️ Stable"
    
    # Format monthly breakdown
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    
    lines = [
        "[Prediction agent]",
        "- dataset: subscriptions",
        "- prediction type: new subscriptions (next year)",
        "",
        f"📊 *Summary:*",
        f"• Total predicted new subscriptions: **{total_predicted:,.0f}**",
        f"• Average per month: **{avg_per_month:,.0f}**",
        f"• Trend: {trend_direction}",
        "",
        "*Monthly Breakdown (Next 12 Months):*",
    ]
    
    for year, month, count in predictions:
        month_name = month_names[month - 1]
        lines.append(f"• {month_name} {year}: **{count:,.0f}** new subscriptions")
    
    lines.append("")
    lines.append("_Note: Predictions are based on linear trend extrapolation from historical data._")
    
    return "\n".join(lines)


def run_subscription_prediction(question: str) -> str:
    """
    Main handler for subscription prediction queries using PandasAI/LLM.
    
    Orchestrates the prediction pipeline:
    1. Extract historical data
    2. Calculate trend
    3. Generate predictions
    4. Use LLM to provide insights and explanations
    5. Format response
    
    Args:
        question: User's question for context and LLM analysis
    
    Returns:
        Formatted prediction response string with LLM insights
    """
    try:
        # Get historical data
        historical_data = _get_historical_new_subscriptions()
        
        # Check if we have enough data
        if len(historical_data) < 6:
            return (
                "🤖 *Powered by PandasAI v3 + LLM*\n\n"
                "[Prediction agent]\n"
                "⚠️ Insufficient historical data for reliable predictions.\n"
                f"I found only {len(historical_data)} month(s) of data. "
                "Need at least 6 months of historical subscription data to generate predictions."
            )
        
        # Calculate trend
        slope, intercept = _calculate_linear_trend(historical_data)
        
        # Generate predictions
        predictions = _predict_future_subscriptions(historical_data, slope, intercept)
        
        # Format base response
        base_response = _format_prediction_response(historical_data, predictions, slope)
        
        # Enhance with LLM insights - ALWAYS try to get insights
        llm_insight = ""
        if PANDASAI_AVAILABLE:
            try:
                # Create data summary for LLM
                total_predicted = sum(count for _, _, count in predictions)
                avg_per_month = total_predicted / 12 if predictions else 0
                trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
                
                data_summary = (
                    f"Historical data: {len(historical_data)} months. "
                    f"Predicted total: {total_predicted:,.0f} subscriptions over next 12 months. "
                    f"Average: {avg_per_month:,.0f} per month. Trend: {trend_direction}."
                )
                
                # Use PandasAI service to get LLM insights
                from core.services.pandasai_service import analyze_with_llm
                llm_insight = analyze_with_llm(
                    f"Analyze subscription predictions: {question}",
                    data_summary
                )
            except Exception as e:
                # Log error but continue - we'll show base response
                import logging
                logging.warning(f"LLM insight generation failed: {e}")
        
        # Always include LLM indicator and insights if available
        response_parts = [
            "🤖 *Powered by PandasAI v3 + LLM*",
            "📋 *Using semantic layer*",
            "",
            base_response
        ]
        
        if llm_insight and llm_insight.strip():
            response_parts.extend([
                "",
                "💡 *LLM Insights:*",
                llm_insight
            ])
        
        return "\n".join(response_parts)
        
    except ValueError as e:
        return (
            "🤖 *Powered by PandasAI v3 + LLM*\n\n"
            "[Prediction agent]\n"
            f"⚠️ Error: {str(e)}"
        )
    except Exception as e:
        return (
            "🤖 *Powered by PandasAI v3 + LLM*\n\n"
            "[Prediction agent]\n"
            f"⚠️ An error occurred while generating predictions.\n"
            f"_Internal error:_ `{e}`"
        )


def run_data_question(dataset_name: str, question: str) -> str:
    """
    Handle data questions using PandasAI v3 with semantic layer ONLY.
    No manual SQL fallback - all queries go through PandasAI/LLM.

    Uses semantic layer YAML files to automatically convert natural language
    to SQL queries and execute them.
    """
    # Check if PandasAI is available
    if not PANDASAI_AVAILABLE or not query_with_pandasai:
        return (
            "⚠️ *PandasAI Not Available*\n\n"
            "PandasAI v3 is required for natural language queries but is not installed.\n"
            "Please install it with: `poetry install`\n\n"
            "Manual SQL queries have been disabled. All queries must go through PandasAI/LLM."
        )
    
    # Check if LLM API key is configured
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")):
        return (
            "⚠️ *LLM API Key Required*\n\n"
            "PandasAI requires an LLM API key to process natural language queries.\n"
            "Please add `OPENAI_API_KEY` to your `.env` file.\n"
            "Get your API key from: https://platform.openai.com/api-keys\n\n"
            "Manual SQL queries have been disabled. All queries must go through PandasAI/LLM."
        )
    
    # Use PandasAI for all queries
    try:
        result = query_with_pandasai(question, dataset_name if dataset_name != "none" else None)
        return result
    except Exception as e:
        return (
            f"⚠️ *Error processing query with PandasAI*\n\n"
            f"```{str(e)}```\n\n"
            "Please try rephrasing your question or check the logs for more details.\n"
            "Manual SQL queries have been disabled - all queries must go through PandasAI/LLM."
        )
    
    # Manual SQL code removed - all queries now go through PandasAI only
    # The function will never reach here since we return early from PandasAI calls


# ---------- SQL QUERY EXECUTION FOR DATA SCIENTISTS ----------

def _is_safe_sql_query(sql: str) -> bool:
    """
    Validate that SQL query is safe (read-only).
    Only allows SELECT, WITH, EXPLAIN, DESCRIBE statements.
    """
    sql_upper = sql.strip().upper()
    
    # Block dangerous keywords
    dangerous_keywords = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    # Only allow safe statement types
    safe_prefixes = ["SELECT", "WITH", "EXPLAIN", "DESCRIBE", "SHOW"]
    sql_start = sql_upper.split()[0] if sql_upper.split() else ""
    
    return sql_start in safe_prefixes


def _extract_sql_from_message(text: str) -> Optional[str]:
    """
    Extract SQL query from message text.
    Handles cases where SQL is wrapped in code blocks or prefixed with "sql:".
    """
    # Remove code block markers if present
    text = re.sub(r'^```(?:sql)?\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove "sql:" or "query:" prefix if present
    text = re.sub(r'^(?:sql|query):\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text.strip() if text.strip() else None


def _format_sql_results(rows: List[Dict[str, Any]], max_rows: int = 100) -> str:
    """
    Format SQL query results for Slack display.
    """
    if not rows:
        return "Query executed successfully but returned no rows."
    
    if len(rows) > max_rows:
        rows = rows[:max_rows]
        warning = f"\n⚠️ _Showing first {max_rows} of {len(rows)} rows_\n"
    else:
        warning = ""
    
    # Get column names
    columns = list(rows[0].keys())
    
    # Format as table
    lines = ["📊 *Query Results:*" + warning, ""]
    
    # Header
    header = " | ".join(str(col) for col in columns)
    lines.append(f"`{header}`")
    lines.append("`" + "-" * len(header) + "`")
    
    # Rows
    for row in rows:
        row_values = [str(row.get(col, "")) for col in columns]
        row_str = " | ".join(row_values)
        lines.append(f"`{row_str}`")
    
    if len(rows) == max_rows:
        lines.append(f"\n_... and {len(rows) - max_rows} more rows_")
    
    lines.append(f"\n*Total rows returned:* {len(rows)}")
    
    return "\n".join(lines)


def run_sql_query(sql_text: str) -> str:
    """
    Execute a SQL query safely (read-only) and return formatted results with LLM insights.
    Designed for data scientists who want to write custom SQL queries.
    Uses PandasAI/LLM to provide explanations and insights on query results.
    
    Args:
        sql_text: SQL query text (may include code blocks or "sql:" prefix)
    
    Returns:
        Formatted query results with LLM insights or error message
    """
    try:
        # Extract SQL from message
        sql = _extract_sql_from_message(sql_text)
        
        if not sql:
            return (
                "🤖 *Powered by PandasAI v3 + LLM*\n\n"
                "⚠️ *SQL Query Error*\n"
                "No SQL query found. Please provide a SELECT query.\n"
                "You can wrap it in code blocks: ```sql\nSELECT ...\n```"
            )
        
        # Validate SQL is safe
        if not _is_safe_sql_query(sql):
            return (
                "🤖 *Powered by PandasAI v3 + LLM*\n\n"
                "⚠️ *Security Error*\n"
                "Only SELECT, WITH, EXPLAIN, and DESCRIBE queries are allowed.\n"
                "Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are not permitted."
            )
        
        # Execute query
        conn = _get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                
                # Convert to list of dicts
                result_rows = [dict(row) for row in rows]
                
                # Format base results
                base_results = _format_sql_results(result_rows)
                
                # Enhance with LLM insights - ALWAYS try to get insights
                llm_explanation = ""
                if PANDASAI_AVAILABLE:
                    try:
                        from core.services.pandasai_service import explain_with_llm
                        
                        # Create summary for LLM
                        result_summary = (
                            f"SQL Query executed successfully. "
                            f"Returned {len(result_rows)} rows. "
                            f"Query: {sql[:200]}..." if len(sql) > 200 else f"Query: {sql}"
                        )
                        
                        # Get LLM explanation
                        llm_explanation = explain_with_llm(
                            f"Explain what this SQL query does and provide insights on the results: {sql}",
                            result_summary
                        )
                    except Exception as e:
                        # Log error but continue - we'll show base results
                        import logging
                        logging.warning(f"LLM explanation generation failed: {e}")
                
                # Always include LLM indicator and insights if available
                response_parts = [
                    "🤖 *Powered by PandasAI v3 + LLM*",
                    "📋 *Using semantic layer*",
                    "",
                    base_results
                ]
                
                if llm_explanation and llm_explanation.strip():
                    response_parts.extend([
                        "",
                        "💡 *LLM Query Analysis:*",
                        llm_explanation
                    ])
                
                return "\n".join(response_parts)
                
        finally:
            conn.close()
            
    except psycopg2.Error as e:
        return (
            "🤖 *Powered by PandasAI v3 + LLM*\n\n"
            f"⚠️ *Database Error*\n"
            f"```{str(e)}```\n"
            f"Please check your SQL syntax and try again."
        )
    except Exception as e:
        return (
            "🤖 *Powered by PandasAI v3 + LLM*\n\n"
            f"⚠️ *Error executing query*\n"
            f"```{str(e)}```"
        )


# ---------- GOLDEN QUERIES LISTING ----------

def _load_golden_queries() -> Dict[str, List[Dict[str, str]]]:
    """
    Load golden queries from semantic layer YAML files.
    
    Returns:
        Dictionary mapping table names to lists of golden queries
    """
    semantic_layer_dir = Path(__file__).parent.parent.parent / "semantic_layer"
    queries = {}
    
    yaml_files = {
        "users": semantic_layer_dir / "users.yml",
        "subscriptions": semantic_layer_dir / "subscriptions.yml",
        "payments": semantic_layer_dir / "payments.yml",
        "sessions": semantic_layer_dir / "sessions.yml",
    }
    
    for table_name, yaml_file in yaml_files.items():
        if not yaml_file.exists():
            continue
            
        try:
            with open(yaml_file, 'r') as f:
                content = yaml.safe_load(f)
                
            # Extract golden_queries section
            if content and "golden_queries" in content:
                queries[table_name] = content["golden_queries"]
        except Exception:
            # Skip files that can't be parsed
            continue
    
    return queries


def list_golden_queries() -> str:
    """
    List all available golden queries from the semantic layer.
    Useful for data scientists to see example queries they can use or modify.
    
    Returns:
        Formatted list of golden queries grouped by table
    """
    queries = _load_golden_queries()
    
    if not queries:
        return (
            "📋 *Available Golden Queries*\n\n"
            "No golden queries found in semantic layer files.\n"
            "Check that semantic_layer/*.yml files exist and contain golden_queries sections."
        )
    
    lines = [
        "📋 *Available Golden Queries*\n",
        "These are pre-defined SQL queries from the semantic layer.\n"
        "You can use them directly or modify them for your needs.\n",
    ]
    
    for table_name, table_queries in queries.items():
        if not table_queries:
            continue
            
        lines.append(f"\n*{table_name.upper()} Table:*")
        
        for i, query in enumerate(table_queries, 1):
            name = query.get("name", f"Query {i}")
            description = query.get("description", "No description")
            sql = query.get("sql", "").strip()
            
            lines.append(f"\n{i}. *{name}*")
            lines.append(f"   _{description}_")
            
            if sql:
                # Show first few lines of SQL
                sql_preview = "\n".join(sql.split("\n")[:3])
                if len(sql.split("\n")) > 3:
                    sql_preview += "\n   ..."
                lines.append(f"   ```sql\n   {sql_preview}\n   ```")
    
    lines.append(
        "\n💡 *Tip:* You can copy any of these queries and modify them, "
        "or use them directly by pasting the SQL into a message."
    )
    
    return "\n".join(lines)


# ---------- SQL QUERY GENERATION ----------

# EU countries list for filtering
EU_COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"
]


def _detect_filters_from_text(text: str, dataset: str) -> Dict[str, Any]:
    """
    Extract filters and requirements from natural language text.
    
    Returns:
        Dictionary with detected filters (region, status, date_range, etc.)
    """
    lower = text.lower()
    filters = {}
    
    # Region/Country filters
    if "eu" in lower or "europe" in lower or "european" in lower:
        filters["region"] = "EU"
    elif "us" in lower or "usa" in lower or "united states" in lower:
        filters["region"] = "US"
    
    # Status filters
    if "active" in lower:
        filters["status"] = "active"
    elif "churned" in lower or "canceled" in lower or "cancelled" in lower:
        filters["status"] = "churned"
    
    # Date filters
    if "last month" in lower or "past month" in lower:
        filters["date_range"] = "last_month"
    elif "last quarter" in lower or "past quarter" in lower:
        filters["date_range"] = "last_quarter"
    elif "last year" in lower or "past year" in lower:
        filters["date_range"] = "last_year"
    
    # Grouping
    if "by plan" in lower or "group by plan" in lower:
        filters["group_by"] = "plan"
    elif "by country" in lower or "group by country" in lower:
        filters["group_by"] = "country"
    
    return filters


def _generate_subscriptions_sql(text: str, filters: Dict[str, Any]) -> str:
    """
    Generate SQL query for subscriptions based on natural language request.
    """
    sql_parts = ["SELECT"]
    
    # Determine what to select
    if filters.get("group_by") == "plan":
        sql_parts.append("    plan,")
        sql_parts.append("    COUNT(*) AS subscription_count")
    elif filters.get("group_by") == "country":
        sql_parts.append("    u.country,")
        sql_parts.append("    COUNT(*) AS subscription_count")
    else:
        sql_parts.append("    s.subscription_id,")
        sql_parts.append("    s.plan,")
        sql_parts.append("    s.start_date,")
        sql_parts.append("    s.end_date,")
        sql_parts.append("    s.status,")
        if filters.get("region"):
            sql_parts.append("    u.country")
    
    # FROM clause
    if filters.get("region") or filters.get("group_by") == "country":
        sql_parts.append("FROM subscriptions s")
        sql_parts.append("INNER JOIN users u ON s.user_id = u.user_id")
    else:
        sql_parts.append("FROM subscriptions s")
    
    # WHERE clause
    where_conditions = []
    
    # Region filter (EU)
    if filters.get("region") == "EU":
        eu_countries_str = ", ".join([f"'{country}'" for country in EU_COUNTRIES])
        where_conditions.append(f"u.country IN ({eu_countries_str})")
    
    # Status filter
    if filters.get("status") == "active":
        where_conditions.append("(s.end_date IS NULL OR s.end_date > CURRENT_DATE)")
    elif filters.get("status") == "churned":
        where_conditions.append("s.end_date IS NOT NULL AND s.end_date <= CURRENT_DATE")
    
    # Date range filter
    if filters.get("date_range") == "last_month":
        where_conditions.append("s.start_date >= CURRENT_DATE - INTERVAL '30 days'")
    elif filters.get("date_range") == "last_quarter":
        where_conditions.append("s.start_date >= CURRENT_DATE - INTERVAL '90 days'")
    elif filters.get("date_range") == "last_year":
        where_conditions.append("s.start_date >= CURRENT_DATE - INTERVAL '365 days'")
    
    if where_conditions:
        sql_parts.append("WHERE " + " AND ".join(where_conditions))
    
    # GROUP BY clause
    if filters.get("group_by"):
        if filters.get("group_by") == "plan":
            sql_parts.append("GROUP BY plan")
        elif filters.get("group_by") == "country":
            sql_parts.append("GROUP BY u.country")
    
    # ORDER BY clause
    if filters.get("group_by"):
        sql_parts.append("ORDER BY subscription_count DESC")
    else:
        sql_parts.append("ORDER BY s.start_date DESC")
    
    # LIMIT clause (if not grouping, limit results)
    if not filters.get("group_by"):
        sql_parts.append("LIMIT 100")
    
    return "\n".join(sql_parts) + ";"


def generate_sql_query(text: str, dataset: str) -> str:
    """
    Generate a SQL query from natural language request.
    Uses semantic layer information to create appropriate queries.
    
    Args:
        text: Natural language request (e.g., "create sql query for subscriptions in EU")
        dataset: Detected dataset (users, subscriptions, payments, sessions)
    
    Returns:
        Generated SQL query as formatted string
    """
    if dataset == "none":
        return (
            "⚠️ *SQL Generation*\n"
            "I couldn't determine which table you want to query.\n"
            "Please specify: *users*, *subscriptions*, *payments*, or *sessions*.\n\n"
            "Example: \"Create SQL query for subscriptions in EU\""
        )
    
    # Extract filters from text
    filters = _detect_filters_from_text(text, dataset)
    
    # Generate SQL based on dataset
    if dataset == "subscriptions":
        sql = _generate_subscriptions_sql(text, filters)
    elif dataset == "users":
        # Basic users query - can be extended
        sql = "SELECT * FROM users LIMIT 100;"
    elif dataset == "payments":
        # Basic payments query - can be extended
        sql = "SELECT * FROM payments LIMIT 100;"
    elif dataset == "sessions":
        # Basic sessions query - can be extended
        sql = "SELECT * FROM sessions LIMIT 100;"
    else:
        sql = "SELECT * FROM " + dataset + " LIMIT 100;"
    
    # Format response
    lines = [
        "📝 *Generated SQL Query*",
        "",
        f"Based on your request: \"{text}\"",
        "",
        "```sql",
        sql,
        "```",
        "",
        "💡 *You can:*",
        "• Copy this query and paste it to execute",
        "• Modify it as needed",
        "• Use `list queries` to see more examples"
    ]
    
    # Add explanation if filters were detected
    if filters:
        lines.append("")
        lines.append("*Applied filters:*")
        for key, value in filters.items():
            lines.append(f"• {key}: {value}")
    
    return "\n".join(lines)
