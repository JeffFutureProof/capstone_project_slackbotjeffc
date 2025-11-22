import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


from project_name.subsystem_1.router import route_message
from project_name.subsystem_2.pandas_agent import run_data_question, run_subscription_prediction

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
            "👋 I'm your analyst agent.\n\n"
            "You can ask me things like:\n"
            "• *Which regions had the most users last month?*\n"
            "• *What products drove the most revenue last holiday season?*\n"
            "• *What is churn rate by plan?*\n"
            "• *Predict new subscriptions for next year?*"
        )
        return

    if decision.intent == "data_question":
        try:
            answer = run_data_question(decision.dataset, text)
            say(f"🧠 *Answer from `{decision.dataset}` data:*\n{answer}")
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
