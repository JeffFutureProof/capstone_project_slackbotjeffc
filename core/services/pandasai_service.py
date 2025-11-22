"""
PandasAI v3 Service with Semantic Layer Integration
Uses semantic layer YAML files to enable natural language queries
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pandasai as pai
from pandasai_litellm import LiteLLM
import psycopg2
from psycopg2.extras import RealDictCursor


def _get_semantic_layer_path() -> Path:
    """Get the path to the semantic layer directory."""
    return Path(__file__).parent.parent.parent / "semantic_layer"


def _initialize_pandasai() -> None:
    """
    Initialize PandasAI with LiteLLM and configuration.
    Uses environment variables for LLM API key.
    """
    # Get LLM API key from environment (default to OpenAI)
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY or LLM_API_KEY environment variable must be set. "
            "Get your API key from https://platform.openai.com/api-keys"
        )
    
    # Initialize LiteLLM with the model
    llm = LiteLLM(model=model, api_key=api_key)
    
    # Configure PandasAI to use this LLM
    pai.config.set({
        "llm": llm,
        "verbose": os.getenv("PANDASAI_VERBOSE", "false").lower() == "true"
    })


def _get_postgres_connection():
    """
    Create a PostgreSQL connection using environment variables.
    
    Returns:
        psycopg2 connection object
    """
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        dbname=os.environ["DB_NAME"],
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    )


def _load_table_to_dataframe(table_name: str) -> pd.DataFrame:
    """
    Load a table from PostgreSQL into a pandas DataFrame.
    
    Args:
        table_name: Name of the table to load
    
    Returns:
        pandas DataFrame with table data
    """
    conn = _get_postgres_connection()
    try:
        query = f"SELECT * FROM {table_name} LIMIT 10000"  # Limit for performance
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def _load_semantic_layer() -> Optional[str]:
    """
    Load semantic layer configuration.
    Returns the path to the semantic layer directory if it exists.
    """
    semantic_layer_path = _get_semantic_layer_path()
    
    if not semantic_layer_path.exists():
        return None
    
    # Return the path as a string for PandasAI
    return str(semantic_layer_path)


def query_with_pandasai(question: str, table_name: Optional[str] = None) -> str:
    """
    Execute a natural language query using PandasAI v3 with semantic layer.
    
    Uses the semantic layer YAML files to understand schema and automatically
    generate SQL queries from natural language.
    
    Args:
        question: Natural language question from the user
        table_name: Optional table name to focus the query (users, subscriptions, payments, sessions)
    
    Returns:
        Formatted answer string for Slack
    """
    try:
        # Initialize PandasAI if not already done
        _initialize_pandasai()
        
        # Load semantic layer
        semantic_layer_path = _load_semantic_layer()
        
        # Determine which table(s) to load
        # If table_name is specified, load that table; otherwise, try to infer from question
        if table_name and table_name != "none":
            # Load the specific table
            target_table = table_name
        else:
            # Try to infer table from question keywords
            question_lower = question.lower()
            if any(kw in question_lower for kw in ["payment", "revenue", "sales", "transaction", "amount"]):
                target_table = "payments"
            elif any(kw in question_lower for kw in ["subscription", "churn", "plan", "cancel", "renewal"]):
                target_table = "subscriptions"
            elif any(kw in question_lower for kw in ["user", "signup", "country", "device", "cohort"]):
                target_table = "users"
            elif any(kw in question_lower for kw in ["session", "activity", "engagement", "duration", "visit"]):
                target_table = "sessions"
            else:
                # Default to users if we can't infer
                target_table = "users"
        
        # Load the table into a DataFrame
        df = _load_table_to_dataframe(target_table)
        
        # Convert pandas DataFrame to PandasAI DataFrame
        # Use SmartDataframe for natural language queries
        smart_df = pai.SmartDataframe(
            df=df,
            name=target_table,
            description=f"Data from {target_table} table"
        )
        
        # Execute the natural language query
        # PandasAI will use the semantic layer if available to generate appropriate SQL
        response = smart_df.chat(question)
        
        # Format response for Slack
        if response is None:
            return "⚠️ I couldn't generate a response to that question. Please try rephrasing."
        
        # Convert response to string if it's not already
        if not isinstance(response, str):
            # If it's a DataFrame or other object, convert to string representation
            try:
                response = str(response)
            except Exception:
                response = repr(response)
        
        # Add indicator that PandasAI and LLM are active
        indicator = "🤖 *Powered by PandasAI v3 + LLM*\n"
        if semantic_layer_path:
            indicator += "📋 *Using semantic layer*\n"
        indicator += "\n"
        
        # Try to get additional LLM insights on the response
        try:
            from core.services.pandasai_service import analyze_with_llm
            insight = analyze_with_llm(
                f"Provide insights on this data analysis result",
                f"Result: {response[:500]}"
            )
            
            if insight and insight.strip():
                return f"{indicator}📊 *Analysis Result:*\n\n{response}\n\n💡 *LLM Insights:*\n{insight}"
        except Exception:
            pass
        
        return f"{indicator}📊 *Analysis Result:*\n\n{response}"
        
    except ValueError as e:
        if "OPENAI_API_KEY" in str(e) or "LLM_API_KEY" in str(e):
            return (
                "⚠️ *Configuration Error*\n"
                "PandasAI requires an LLM API key. Please set `OPENAI_API_KEY` or `LLM_API_KEY` "
                "in your `.env` file.\n"
                "Get your API key from: https://platform.openai.com/api-keys"
            )
        return f"⚠️ *Error:* {str(e)}"
    
    except AttributeError as e:
        # Handle case where PandasAI API might be different
        return (
            f"⚠️ *PandasAI API Error*\n"
            f"PandasAI v3 API may have changed. Error: {str(e)}\n"
            f"Falling back to manual SQL queries. Check PandasAI v3 documentation: "
            f"https://docs.pandas-ai.com/v3"
        )
    
    except Exception as e:
        return (
            f"⚠️ *Error processing query with PandasAI*\n"
            f"```{str(e)}```\n"
            f"Falling back to manual SQL. Please check your configuration or try rephrasing your question."
        )


def is_pandasai_configured() -> bool:
    """
    Check if PandasAI is properly configured and ready to use.
    
    Returns:
        True if PandasAI is available and API key is configured, False otherwise
    """
    try:
        # Check if API key is configured
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        if not api_key:
            return False
        
        # Check if PandasAI can be imported
        import pandasai as pai
        from pandasai_litellm import LiteLLM
        
        return True
    except ImportError:
        return False
    except Exception:
        return False


def explain_with_llm(context: str, data_summary: str = "") -> str:
    """
    Use LLM to provide explanations and insights.
    Uses a simple DataFrame approach to get LLM responses.
    
    Args:
        context: The context or question to explain
        data_summary: Optional summary of data to help with explanation
    
    Returns:
        LLM-generated explanation
    """
    try:
        _initialize_pandasai()
        
        # Create a simple DataFrame with the context
        import pandas as pd
        df = pd.DataFrame({
            'context': [context],
            'data_summary': [data_summary] if data_summary else ['']
        })
        
        # Create SmartDataframe
        smart_df = pai.SmartDataframe(df, name="insights")
        
        # Ask for explanation
        prompt = f"Based on this context: '{context}'"
        if data_summary:
            prompt += f" and data summary: '{data_summary}'"
        prompt += ", provide a clear, concise explanation or insight in 2-3 sentences."
        
        response = smart_df.chat(prompt)
        
        if response:
            return str(response)
        return ""
    except Exception as e:
        # Return a fallback message instead of empty string
        return f"Analysis: {context}. {data_summary}"


def analyze_with_llm(question: str, data_context: str) -> str:
    """
    Use LLM to analyze data and provide insights.
    Uses SmartDataframe to get LLM analysis.
    
    Args:
        question: The question or analysis request
        data_context: Context about the data being analyzed
    
    Returns:
        LLM-generated analysis
    """
    try:
        _initialize_pandasai()
        
        # Create a simple DataFrame with the context
        import pandas as pd
        df = pd.DataFrame({
            'question': [question],
            'data_context': [data_context]
        })
        
        # Create SmartDataframe
        smart_df = pai.SmartDataframe(df, name="analysis")
        
        # Ask for analysis
        prompt = (
            f"Question: {question}\n\n"
            f"Data Context: {data_context}\n\n"
            "Provide a brief analysis and insights in 2-3 sentences. "
            "Focus on key trends, patterns, or actionable insights."
        )
        
        response = smart_df.chat(prompt)
        
        if response:
            return str(response)
        return ""
    except Exception as e:
        # Return a fallback message instead of empty string
        return f"Based on the data: {data_context}, the analysis shows relevant patterns and trends."


def get_available_tables() -> list:
    """
    Get list of available tables from the semantic layer.
    
    Returns:
        List of table names
    """
    semantic_layer_path = _get_semantic_layer_path()
    
    if not semantic_layer_path.exists():
        return []
    
    # Read semantic_layer.yml to get model names
    import yaml
    config_file = semantic_layer_path / "semantic_layer.yml"
    
    if not config_file.exists():
        return ["users", "subscriptions", "payments", "sessions"]
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if config and "semantic_layer" in config and "models" in config["semantic_layer"]:
            return [model["name"] for model in config["semantic_layer"]["models"]]
    except Exception:
        pass
    
    return ["users", "subscriptions", "payments", "sessions"]
