# Talk-to-Your-Data Slackbot

A Slack bot that enables Marketing and Sales teams to ask natural-language questions about customer behavior, subscription lifecycle, payments, user growth, and engagement — all powered directly by a Postgres database.

## Overview

The **Talk-to-Your-Data Slackbot** interprets natural language questions, determines which database tables are relevant (Users, Sessions, Subscriptions, Payments), retrieves the necessary data, performs analysis, and returns clear insights directly inside Slack.

This system supports holiday-season revenue targeting, user segmentation, geo/device insights, and growth analytics **without requiring SQL knowledge** from business users.

## Features

- **Natural Language Queries**: Ask questions in plain English about your data
- **Multi-Table Support**: Automatically routes queries to relevant datasets:
  - **Users**: Signup trends, device mix, geographies
  - **Subscriptions**: Plan mix, churn, cancellations, duration
  - **Payments**: Revenue, payment method mix, lifetime value
  - **Sessions**: Activity type, session length, engagement metrics
- **Time Window Analysis**: Supports queries like "last month", "last quarter", "last year"
- **Smart Routing**: Classifies messages and routes to appropriate data handlers
- **Slack Integration**: Real-time responses directly in Slack channels and DMs

## Architecture

The system is organized into two main stages:

### Intake Stage
- **Listener & Input Analyzer**: Receives Slack messages and inquiries
- **Router**: Classifies question type and chooses relevant datasets based on keywords and semantic understanding
- **Preprocessing**: Cleans text input, strips mentions and noise from Slack messages

### Engine Stage
- **Data Access Layer**: Connects to Postgres Database, maintains semantic models
- **Query Execution**: Generates and runs SQL queries based on user questions
- **Answer Formatter**: Summarizes results for Slack output with clear formatting

## Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)
- PostgreSQL database with the following tables:
  - `users` (with columns: user_id, country, device_type, etc.)
  - `subscriptions` (with columns: subscription_id, user_id, plan, start_date, end_date, etc.)
  - `payments` (with columns: payment_id, user_id, amount_usd, payment_date, etc.)
  - `sessions` (with columns: session_id, user_id, activity_type, duration_minutes, etc.)
- Slack App with the following tokens:
  - Bot Token
  - Signing Secret
  - App Token (for Socket Mode)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Capstone_project_slackbotjeffc
   ```

2. **Install dependencies using Poetry**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root with the following variables:
   
   ```env
   # Slack Configuration
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   SLACK_APP_TOKEN=xapp-your-app-token
   
   # Database Configuration
   DB_HOST=your-db-host
   DB_PORT=5432
   DB_USER=your-db-user
   DB_PASS=your-db-password
   DB_NAME=your-db-name
   DB_SSLMODE=require
   ```

## Usage

### Running the Bot

1. **Activate the Poetry environment**
   ```bash
   poetry shell
   ```

2. **Start the Slackbot**
   ```bash
   python main.py
   ```

   You should see:
   ```
   🤖 Slackbot with router is running...
   ```

3. **Interact with the bot in Slack**
   - Mention the bot in a channel or send it a DM
   - Ask questions like:
     - "Which countries saw the highest user signup growth last month?"
     - "What is the total revenue from payments last quarter?"
     - "Show me churn rate by plan"
     - "What are the top device types for users?"

### Example Queries

- **Users**: "How many users signed up last month?", "Which countries have the most users?", "What device types do users use?"
- **Payments**: "What is total revenue last quarter?", "Show me payments for last year", "What is the total sales amount?"
- **Subscriptions**: "What is the churn rate?", "How many active subscriptions are there?", "Show me subscriptions by plan"
- **Sessions**: "What is the average session duration?", "Which activities are most popular?", "How many active users do we have?"

### Getting Help

Type `help` or "what can you do" to see available commands and example questions.

## Project Structure

```
Capstone_project_slackbotjeffc/
├── main.py                          # Main entry point, Slack app initialization
├── core/
│   ├── app.py                       # Alternative app configuration
│   ├── subsystem_1/
│   │   └── router.py                # Message routing logic
│   ├── subsystem_2/
│   │   └── pandas_agent.py          # Data query execution
│   ├── services/
│   │   └── pandasai_service.py      # PandasAI service (placeholder)
│   └── handlers/
│       ├── mention_handlers.py       # Mention event handlers
│       ├── message_handlers.py       # Message event handlers
│       └── error_handlers.py         # Error handling
├── pyproject.toml                   # Poetry dependencies
├── PROJECT_CONTEXT.md               # Detailed project documentation
├── AGENTS.md                        # Architecture and coding rules
└── README.md                        # This file
```

## How It Works

1. **Message Reception**: The bot listens for messages in Slack using Socket Mode
2. **Routing**: The router (`subsystem_1/router.py`) analyzes the message text and:
   - Identifies intent (help, small_talk, data_question, unknown)
   - Determines the relevant dataset (users, payments, subscriptions, sessions)
3. **Query Execution**: The data agent (`subsystem_2/pandas_agent.py`) executes SQL queries against the Postgres database
4. **Response Formatting**: Results are formatted and sent back to Slack

## Supported Query Types

### Payments
- Total revenue over time windows (last week, month, quarter, year)
- Payment aggregations and summaries

### Users
- Total user counts
- Top countries by user count
- Top device types by user count

### Subscriptions
- Total, active, and churned subscription counts
- Churn rate calculations
- Active subscriptions by plan

### Sessions
- Total session counts
- Active user counts
- Average session duration
- Top activities by total minutes

## Development

### Adding New Query Types

1. Add keywords to the router in `core/subsystem_1/router.py`
2. Implement query logic in `core/subsystem_2/pandas_agent.py`
3. Update the `run_data_question` function to handle new query patterns

### Testing

The project includes a `tests/` directory for unit tests. Add tests for:
- Router classification logic
- SQL query generation
- Response formatting

## Dependencies

- `slack-bolt`: Slack SDK for Python
- `slack-sdk`: Slack SDK core
- `python-dotenv`: Environment variable management
- `psycopg2-binary`: PostgreSQL adapter for Python

See `pyproject.toml` for the complete list of dependencies.

## Limitations (MVP Scope)

- Read-only access (no write-back actions)
- No multi-step workflows
- No long-term conversation memory
- No real-time streaming events

## Troubleshooting

### Bot not responding
- Verify all Slack tokens are correctly set in `.env`
- Check that Socket Mode is enabled for your Slack app
- Ensure the bot is invited to the channel or DM

### Database connection errors
- Verify database credentials in `.env`
- Check network connectivity to the database
- Ensure SSL mode matches your database configuration

### Query not recognized
- Try rephrasing with explicit keywords (users, payments, subscriptions, sessions)
- Use the `help` command to see example queries
- Check that the router keywords match your question

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Contact

[Add contact information here]
