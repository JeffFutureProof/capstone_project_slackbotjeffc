# Semantic Layer Documentation

This directory contains semantic layer definitions for the Talk-to-Your-Data Slackbot. The semantic layer provides a business-friendly abstraction over the database schema, defining dimensions, measures, and relationships that enable natural language queries.

## Overview

The semantic layer consists of YAML files that define:
- **Models**: Data tables and their structure
- **Dimensions**: Attributes for filtering and grouping (e.g., country, plan, activity_type)
- **Measures**: Metrics and aggregations (e.g., total_users, revenue, churn_rate)
- **Relationships**: Foreign key relationships between tables

## Files

### `users.yml`
Defines the users data model with:
- **Dimensions**: country, device_type, signup_date
- **Measures**: total_users, users_by_country, users_by_device
- **Relationships**: One-to-many with subscriptions, payments, and sessions

### `subscriptions.yml`
Defines the subscriptions data model with:
- **Dimensions**: plan, start_date, end_date, subscription_status, subscription_month
- **Measures**: total_subscriptions, active_subscriptions, churned_subscriptions, churn_rate, new_subscriptions
- **Relationships**: Many-to-one with users

### `payments.yml`
Defines the payments data model with:
- **Dimensions**: payment_date, payment_month, payment_method, payment_year
- **Measures**: total_revenue, total_payments, average_payment, revenue_by_method, revenue_by_month
- **Relationships**: Many-to-one with users (and optionally subscriptions)

### `sessions.yml`
Defines the sessions data model with:
- **Dimensions**: activity_type, session_date, session_month, session_year
- **Measures**: total_sessions, active_users, average_duration, total_duration_minutes, sessions_by_activity
- **Relationships**: Many-to-one with users

## Usage

These semantic layer definitions are used by:
1. **PandasAI v3**: For natural language query interpretation and SQL generation
2. **Router**: For understanding data relationships when routing queries
3. **Data Agent**: For generating appropriate SQL queries based on business terminology

## Schema Alignment

The semantic layer definitions align with the actual PostgreSQL database schema:
- All column names match database column names
- Foreign key relationships are properly defined
- Data types correspond to PostgreSQL types
- Measures use standard SQL aggregations (COUNT, SUM, AVG)

## Extending the Semantic Layer

To add new dimensions or measures:

1. Edit the appropriate YAML file (e.g., `users.yml`)
2. Add the dimension or measure definition following the existing pattern
3. Ensure the SQL expressions are valid for your database
4. Test with natural language queries to verify the new definitions work correctly

## Golden Queries

The semantic layer includes "golden queries" - pre-defined, validated measures that represent key business metrics:
- `total_users`: Total user count
- `churn_rate`: Percentage of churned subscriptions
- `total_revenue`: Sum of all payment amounts
- `avg_session_minutes`: Average session duration

These golden queries ensure consistent, accurate reporting across the system.

