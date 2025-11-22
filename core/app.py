import os
from slack_bolt import App
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

# Initialize your app
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Basic event handler
@app.event("message")
def handle_message_events(body, say):
    user = body["event"].get("user")
    text = body["event"].get("text", "")

    # Ignore bot messages
    if user is None:
        return

    say(f"Hey Jeff 👋, I received your message: '{text}'")


