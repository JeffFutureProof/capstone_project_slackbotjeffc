# Project Context

## Project Overview

The **Talk-to-Your-Data Slackbot** enables Marketing and Sales teams to ask natural-language questions about customer behavior, subscription lifecycle, payments, user growth, and engagement — all powered directly by a Postgres database.

The agent interprets questions, determines which database tables are relevant (Users, Sessions, Subscriptions, Payments), retrieves the necessary data, performs analysis using PandasAI v3, and returns clear insights directly inside Slack.

This system exists to support holiday-season revenue targeting, user segmentation, geo/device insights, and growth analytics **without requiring SQL knowledge** from business users.

## System Scope

### In Scope

**Natural-language questions about:**

- **Users** (signup trends, device mix, geographies) — from Users table
- **Subscriptions** (plan mix, churn, cancellations, duration) — from Subscriptions table
- **Payments** (revenue, payment method mix, lifetime value) — from Payments table
- **Sessions / Engagement** (activity type, session length, DAU/WAU/MAU) — from Sessions table

**Core capabilities:**

- Query routing (deciding which table(s) to access based on the question)
- Generating SQL or Pandas transformations using PandasAI v3
- Returning summaries, charts, or text insights inside Slack

### Out of Scope (for MVP)

- Write-back actions (modifying database records)
- Multi-step workflows (e.g., cohort exploration sequences)
- Long-term memory of past conversations
- Real-time streaming events

## Architecture Summary

The system is organized into two main stages — **Intake** and **Engine** — plus supporting infrastructure for data access, logging, and monitoring. Responsibilities are aligned directly with the semantic-layer schema.

### Intake Stage

Handles receipt, cleaning, and routing of user queries:

1. **Listener & Input Analyzer**  
   Listens to Slack channels and DMs, receives incoming messages and inquiries.

2. **Intake & Preprocessing**  
   Cleans text input, strips mentions and noise from Slack messages to prepare queries for processing.

3. **Router & Intake Logic**  
   Classifies question type and chooses relevant datasets from: Users, Subscriptions, Payments, Sessions. Routes queries based on keywords and semantic understanding:
   - "revenue", "payments", "method" → Payments
   - "churn", "subscriptions", "plan" → Subscriptions
   - "users", "country", "device type" → Users
   - "sessions", "activity", "duration" → Sessions

### Engine Stage

Handles data access, semantic understanding, reasoning, and result formatting:

1. **Data Access & Semantic Layer**  
   Connects to Postgres Database, maintains semantic models, and handles multi-table joins via foreign keys (`user_id`, `subscription_id`). Provides structured access to Users, Subscriptions, Payments, and Sessions tables.

2. **Reasoning Engine**  
   Interprets natural language questions, generates and runs analysis over DataFrames using PandasAI v3. Leverages measures and relationships from the semantic layer, including golden queries (e.g., `total_users`, `payment_count`, `avg_session_minutes`, `churn_rate_for_period`).

3. **Answer Formatter & Guardrails**  
   Summarizes results for Slack output, formats top-N lists and bullet points using simple wording. Handles edge cases such as "no data" scenarios and ambiguous queries.

### Supporting Infrastructure

- **Postgres Database**  
   Stores data across four core tables: Users, Subscriptions, Payments, Sessions. Provides read-only access via the Data Access layer.

- **Logging & Monitoring**  
   Tracks query routing decisions, datasets used, result types, and system status for observability and debugging.

## Key Inputs and Outputs

### Inputs

- **Natural language questions from Slack**  
  (e.g., "Which countries saw the highest user signup growth last month?")

- **Query context passed to PandasAI:**
  - Selected dataset (users/subscriptions/payments/sessions)
  - Semantic-layer metadata
  - Time window (optional)

### Outputs

- Text summaries (e.g., "Top 5 countries by new users in last 30 days…")
- Aggregations (counts, sums, averages, churn rate)
- Recommended marketing segments
- Simple charts (bar charts, line charts, pie charts)

## Design Rationale

This design is simple, modular, and tightly aligned with the actual structure of the data, ensuring:

### Accuracy

Because the system relies on semantic-layer metadata, PandasAI interprets tables and relationships correctly.

### Business Relevance

Each table answers a different set of Marketing/Sales questions:

- **Users:** geography, device mix, acquisition
- **Subscriptions:** churn, plan upgrades, lifetime metrics
- **Payments:** revenue drivers, payment method mix
- **Sessions:** user engagement and activity type

### Explainability

Golden queries included in the schema (e.g., revenue by method, new starts vs cancels) set a strong foundation for validated KPI outputs.

### Extensibility

New tables or metrics can be added to the semantic layer without rewriting the agent.
