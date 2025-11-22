import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


from core.subsystem_1.router import route_message
from core.subsystem_2.pandas_agent import (
    run_data_question,
    run_subscription_prediction,
    run_sql_query,
    list_golden_queries,
    generate_sql_query,
)

# ----------------------------------------
# Load environment variables
# ----------------------------------------
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# ----------------------------------------
# Initialize Slack App
# ----------------------------------------
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
)

# ----------------------------------------
# Single message handler that uses the router
# ----------------------------------------
@app.event("message")
def handle_message_events(body, say):
    event = body.get("event", {})
    user = event.get("user")
    text = event.get("text", "")

    # Ignore bot/system messages
    if user is None or not text:
        return

    decision = route_message(text)

    if decision.intent == "help":
        say(
            "👋 I'm your analyst agent powered by PandasAI v3!\n\n"
            "*For non-technical users:*\n"
            "Ask me questions in natural language:\n"
            "• *Which regions had the most users last month?*\n"
            "• *What products drove the most revenue last holiday season?*\n"
            "• *What is churn rate by plan?*\n"
            "• *Show me subscriptions in the EU*\n"
            "• *Predict new subscriptions for next year?*\n\n"
            "*For data scientists:*\n"
            "• *List queries* - See available golden queries\n"
            "• *Create SQL query for [table] [filters]* - Generate SQL queries\n"
            "  Example: \"Create SQL query for subscriptions in EU\"\n"
            "• Paste SQL queries directly (SELECT only)\n"
            "• Use queries from semantic layer as templates\n\n"
            "*Powered by:* PandasAI v3 with semantic layer integration"
        )
        return

    if decision.intent == "data_question":
        try:
            answer = run_data_question(decision.dataset, text)
            # The answer already includes indicators (PandasAI or manual SQL)
            # so we just need to format it nicely
            if decision.dataset != "none":
                say(f"🧠 *Answer from `{decision.dataset}` data:*\n{answer}")
            else:
                say(answer)
        except Exception as e:
            say(
                "I tried to run that analysis on the data but hit an error ⚠️.\n"
                f"_Internal error:_ `{e}`"
            )
        return

    if decision.intent == "prediction":
        try:
            answer = run_subscription_prediction(text)
            say(f"🔮 *Subscription Prediction:*\n{answer}")
        except Exception as e:
            say(
                "I tried to generate predictions but hit an error ⚠️.\n"
                f"_Internal error:_ `{e}`"
            )
        return

    if decision.intent == "sql_query":
        try:
            answer = run_sql_query(text)
            say(answer)
        except Exception as e:
            say(
                "I tried to execute your SQL query but hit an error ⚠️.\n"
                f"_Internal error:_ `{e}`"
            )
        return

    if decision.intent == "list_queries":
        try:
            answer = list_golden_queries()
            say(answer)
        except Exception as e:
            say(
                "I tried to list golden queries but hit an error ⚠️.\n"
                f"_Internal error:_ `{e}`"
            )
        return

    if decision.intent == "generate_sql":
        try:
            answer = generate_sql_query(text, decision.dataset)
            say(answer)
        except Exception as e:
            say(
                "I tried to generate a SQL query but hit an error ⚠️.\n"
                f"_Internal error:_ `{e}`"
            )
        return

    # Unknown / fallback
    say(
        "Hmm, I’m not sure what to do with that yet 🤔.\n"
        "Try asking for *help* or mention *users, payments, subscriptions, or sessions*."
    )

# ----------------------------------------
# Start Socket Mode
# ----------------------------------------
if __name__ == "__main__":
    print("🤖 Slackbot with router is running...")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
