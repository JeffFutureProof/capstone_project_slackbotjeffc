from dataclasses import dataclass
from typing import Literal

Intent = Literal["help", "small_talk", "data_question", "prediction", "sql_query", "list_queries", "generate_sql", "unknown"]
Dataset = Literal["users", "payments", "subscriptions", "sessions", "none"]


@dataclass
class RouteDecision:
    intent: Intent
    dataset: Dataset
    reason: str


HELP_KEYWORDS = ["help", "how do i", "what can you do", "commands"]
SMALL_TALK_KEYWORDS = ["hi", "hello", "hey", "thanks", "thank you", "yo"]

# Dataset-related keywords
USERS_KEYWORDS = ["user", "users", "signup", "signups", "country", "region", "cohort"]
PAYMENTS_KEYWORDS = [
    "payment", "payments", "revenue", "income", "gmv",
    "sales", "sale", "orders", "order", "transactions", "transaction",
    "spend", "spending"
]
SUBSCRIPTIONS_KEYWORDS = ["subscription", "subscriptions", "plan", "plans", "churn", "cancel", "renewal"]
SESSIONS_KEYWORDS = ["session", "sessions", "engagement", "activity", "usage", "visit", "visits"]

# Prediction-related keywords
PREDICTION_KEYWORDS = ["predict", "forecast", "future", "estimate", "projection", "next year", "will be", "going to"]

# SQL query detection keywords
SQL_KEYWORDS = ["select", "with", "show", "explain", "describe"]
SQL_QUERY_INDICATORS = ["sql:", "query:", "run sql", "execute sql", "run query"]

# Golden queries listing keywords
LIST_QUERIES_KEYWORDS = ["list queries", "show queries", "available queries", "golden queries", "what queries", "query examples"]

# SQL generation keywords
GENERATE_SQL_KEYWORDS = ["create sql", "generate sql", "make sql", "write sql", "build sql", "sql query for", "create me sql", "generate me sql"]

# Generic “analysis-y” phrases that indicate a data question
DATA_PHRASES = [
    "how many", "what is", "what are", "show me",
    "trend", "average", "total", "sum", "by country",
    "by region", "by product", "over time", "segment"
]

# Holiday / sales context – default to payments if we see these
HOLIDAY_KEYWORDS = [
    "holiday", "black friday", "cyber monday",
    "christmas", "xmas", "new year", "q4"
]


def route_message(text: str) -> RouteDecision:
    """
    Router for Slack messages:
    - intent: help / small_talk / data_question / prediction / sql_query / list_queries / unknown
    - dataset: users / payments / subscriptions / sessions / none
    """
    lower = text.lower().strip()

    # 1) Help wins
    if any(k in lower for k in HELP_KEYWORDS):
        return RouteDecision(
            intent="help",
            dataset="none",
            reason="Matched help keywords",
        )

    # 1.5) Check for generate SQL request (before list queries to catch "create sql query for...")
    if any(k in lower for k in GENERATE_SQL_KEYWORDS):
        # Try to identify dataset for context
        dataset: Dataset = "none"
        if any(k in lower for k in USERS_KEYWORDS):
            dataset = "users"
        if any(k in lower for k in PAYMENTS_KEYWORDS):
            dataset = "payments"
        if any(k in lower for k in SUBSCRIPTIONS_KEYWORDS):
            dataset = "subscriptions"
        if any(k in lower for k in SESSIONS_KEYWORDS):
            dataset = "sessions"
        
        return RouteDecision(
            intent="generate_sql",
            dataset=dataset,
            reason="Matched generate SQL keywords",
        )

    # 1.6) Check for list queries request
    if any(k in lower for k in LIST_QUERIES_KEYWORDS):
        return RouteDecision(
            intent="list_queries",
            dataset="none",
            reason="Matched list queries keywords",
        )

    # 1.7) Check for SQL queries - detect SQL syntax or explicit SQL indicators
    is_sql_query = (
        any(text.strip().lower().startswith(k) for k in SQL_KEYWORDS) or
        any(indicator in lower for indicator in SQL_QUERY_INDICATORS) or
        ("select" in lower and ("from" in lower or "where" in lower))
    )
    
    if is_sql_query:
        return RouteDecision(
            intent="sql_query",
            dataset="none",
            reason="Detected SQL query syntax",
        )

    # 2) Try to identify dataset first
    dataset: Dataset = "none"

    if any(k in lower for k in USERS_KEYWORDS):
        dataset = "users"
    if any(k in lower for k in PAYMENTS_KEYWORDS):
        dataset = "payments"
    if any(k in lower for k in SUBSCRIPTIONS_KEYWORDS):
        dataset = "subscriptions"
    if any(k in lower for k in SESSIONS_KEYWORDS):
        dataset = "sessions"

    # 2.5) Check for prediction keywords - if subscriptions + prediction keywords, it's a prediction
    mentions_prediction = any(k in lower for k in PREDICTION_KEYWORDS)
    if mentions_prediction and dataset == "subscriptions":
        return RouteDecision(
            intent="prediction",
            dataset="subscriptions",
            reason="Matched prediction keywords with subscriptions dataset",
        )

    # 3) If we see explicit analysis phrases or holiday words, it's a data question
    looks_like_data_question = any(p in lower for p in DATA_PHRASES)

    # Holiday questions should default to payments unless something else is very clear
    mentions_holiday = any(k in lower for k in HOLIDAY_KEYWORDS)
    if mentions_holiday and dataset == "none":
        dataset = "payments"

    if dataset != "none" or looks_like_data_question or mentions_holiday:
        # If we didn't pick a dataset but clearly looks like data analysis,
        # treat it as data_question with dataset="none" (your agent can decide later).
        final_dataset: Dataset = dataset if dataset != "none" else "none"
        return RouteDecision(
            intent="data_question",
            dataset=final_dataset,
            reason=f"Looks like a data question (dataset={final_dataset})",
        )

    # 4) Small talk only if short and no data signals
    if len(lower.split()) <= 4 and any(k in lower for k in SMALL_TALK_KEYWORDS):
        return RouteDecision(
            intent="small_talk",
            dataset="none",
            reason="Matched small-talk keywords on short message",
        )

    # 5) Fallback
    return RouteDecision(
        intent="unknown",
        dataset="none",
        reason="No keyword or pattern matched",
    )
