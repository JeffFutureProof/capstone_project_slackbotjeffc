# project_name/subsystem_2/pandas_agent.py

import os
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor


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
    Main handler for subscription prediction queries.
    
    Orchestrates the prediction pipeline:
    1. Extract historical data
    2. Calculate trend
    3. Generate predictions
    4. Format response
    
    Args:
        question: User's question (for context, not currently used)
    
    Returns:
        Formatted prediction response string
    """
    try:
        # Get historical data
        historical_data = _get_historical_new_subscriptions()
        
        # Check if we have enough data
        if len(historical_data) < 6:
            return (
                "[Prediction agent]\n"
                "⚠️ Insufficient historical data for reliable predictions.\n"
                f"I found only {len(historical_data)} month(s) of data. "
                "Need at least 6 months of historical subscription data to generate predictions."
            )
        
        # Calculate trend
        slope, intercept = _calculate_linear_trend(historical_data)
        
        # Generate predictions
        predictions = _predict_future_subscriptions(historical_data, slope, intercept)
        
        # Format and return response
        return _format_prediction_response(historical_data, predictions, slope)
        
    except ValueError as e:
        return (
            "[Prediction agent]\n"
            f"⚠️ Error: {str(e)}"
        )
    except Exception as e:
        return (
            "[Prediction agent]\n"
            f"⚠️ An error occurred while generating predictions.\n"
            f"_Internal error:_ `{e}`"
        )


def run_data_question(dataset_name: str, question: str) -> str:
    """
    Handle data questions using direct SQL.

    Currently:
      - payments: total revenue over optional time windows
      - users: overview by country/channel/device
      - subscriptions: active/churn + plan breakdown
      - sessions: activity & engagement overview
    """
    q = question.lower()

    # ---- PAYMENTS ----
    if dataset_name == "payments":
        keywords = ["payment", "payments", "revenue", "sales", "amount", "gmv", "transaction", "transactions"]
        if any(k in q for k in keywords):
            window_days, label = _detect_payments_time_window(q)
            total = _query_total_payments(window_days)

            return (
                "[SQL data agent]\n"
                "- dataset: payments\n"
                f"- window: {label}\n\n"
                f"Estimated total payments / revenue: **${total:,.2f} USD**"
            )

        return (
            "[SQL data agent]\n"
            "I recognise this as a payments question, but I don't yet have "
            "a canned SQL query for this type of analysis.\n"
            "Try asking about *total payments*, *revenue*, or *sales* "
            "optionally with a time window like 'last month' or 'last quarter'."
        )

    # ---- USERS ----
    if dataset_name == "users":
        overview = _query_users_overview()
        lines = [
            "[SQL data agent]",
            "- dataset: users",
            "",
            f"Total users: **{overview['total_users']:,}**",
            "",
            "Top countries:",
        ]
        for row in overview["countries"]:
            lines.append(f"• {row['name']}: {row['users']:,} users")

        lines.append("")
        lines.append("Top device types:")
        for row in overview["devices"]:
            lines.append(f"• {row['name']}: {row['users']:,} users")

        lines.append("")
        lines.append("Top device types:")
        for row in overview["devices"]:
            lines.append(f"• {row['name']}: {row['users']:,} users")

        return "\n".join(lines)

    # ---- SUBSCRIPTIONS ----
    if dataset_name == "subscriptions":
        overview = _query_subscriptions_overview()
        total = overview["total_subscriptions"]
        active = overview["active_subscriptions"]
        churned = overview["churned_subscriptions"]
        churn_rate = (churned / total * 100.0) if total > 0 else 0.0

        lines = [
            "[SQL data agent]",
            "- dataset: subscriptions",
            "",
            f"Total subscriptions: **{total:,}**",
            f"Active subscriptions: **{active:,}**",
            f"Churned subscriptions: **{churned:,}** "
            f"({churn_rate:.2f}% of all subscriptions)",
            "",
            "Top plans by active subscriptions:",
        ]
        for row in overview["plans"]:
            lines.append(f"• {row['plan']}: {row['active_subscriptions']:,} active subs")

        return "\n".join(lines)

    # ---- SESSIONS ----
    if dataset_name == "sessions":
        overview = _query_sessions_overview()
        total = overview["total_sessions"]
        active_users = overview["active_users"]
        avg_duration = overview["avg_duration"]

        lines = [
            "[SQL data agent]",
            "- dataset: sessions",
            "",
            f"Total sessions: **{total:,}**",
            f"Active users (with at least one session): **{active_users:,}**",
            f"Average session duration: **{avg_duration:.2f} minutes**",
            "",
            "Top activities by total minutes:",
        ]
        for row in overview["activities"]:
            lines.append(
                f"• {row['activity_type']}: {row['minutes']:,} minutes across {row['sessions']:,} sessions"
            )

        return "\n".join(lines)

    # ---- fallback when dataset_name is unknown or 'none' ----
    return (
        "[SQL data agent]\n"
        f"I couldn't confidently map this question to users/payments/subscriptions/sessions.\n"
        f"Router gave dataset='{dataset_name}'. Try mentioning one of those explicitly "
        "or rephrasing your question."
    )
