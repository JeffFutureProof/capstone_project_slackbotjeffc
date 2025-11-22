# PandasAI v3 Integration Guide

This document explains how PandasAI v3 is integrated with the semantic layer to enable automatic natural language query processing.

## Overview

PandasAI v3 automatically converts natural language questions into SQL queries using your semantic layer YAML files. This eliminates the need for most manual SQL branches in the codebase.

## Architecture

```
User Question (Slack)
    ↓
Router (identifies dataset)
    ↓
pandas_agent.run_data_question()
    ↓
pandasai_service.query_with_pandasai()  ← Uses semantic layer
    ↓
PandasAI v3 (generates SQL from semantic layer)
    ↓
PostgreSQL (executes query)
    ↓
Formatted Response (Slack)
```

## Setup

### 1. Install Dependencies

```bash
poetry install
```

This installs:
- `pandasai` - PandasAI v3 core library
- `pandasai-litellm` - LiteLLM integration for LLM providers

### 2. Configure LLM API Key

Add to your `.env` file:

```env
# Required for PandasAI
OPENAI_API_KEY=your-openai-api-key-here

# Optional: specify model (defaults to gpt-4o-mini)
LLM_MODEL=gpt-4o-mini
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Semantic Layer

The semantic layer YAML files in `semantic_layer/` are automatically used by PandasAI:
- `users.yml`
- `subscriptions.yml`
- `payments.yml`
- `sessions.yml`
- `semantic_layer.yml` (main configuration)

## How It Works

### Natural Language Processing

1. **User asks a question**: "What is the total revenue from payments in the EU last quarter?"

2. **Router identifies dataset**: `payments`

3. **PandasAI service**:
   - Loads PostgreSQL connector
   - Loads semantic layer from YAML files
   - Uses LLM to understand the question
   - Generates SQL using semantic layer definitions
   - Executes query
   - Returns formatted result

### Semantic Layer Benefits

The semantic layer YAML files provide:
- **Table relationships**: Foreign keys and joins
- **Dimensions**: Filterable attributes (country, plan, etc.)
- **Measures**: Aggregations (total_revenue, churn_rate, etc.)
- **Golden queries**: Example SQL patterns

PandasAI uses this information to:
- Generate accurate SQL queries
- Understand business terminology
- Handle complex joins automatically
- Respect data relationships

## Fallback Behavior

If PandasAI is not configured or fails:
- The bot automatically falls back to manual SQL queries
- Existing functionality continues to work
- No breaking changes for users

## Example Queries

With PandasAI enabled, users can ask:

- "What is the total revenue from payments in the EU last quarter?"
- "Show me active subscriptions grouped by plan and country"
- "Which users have the highest lifetime value?"
- "What's the average session duration by activity type?"
- "How many new subscriptions did we get last month by country?"

PandasAI will automatically:
1. Understand the question
2. Identify relevant tables from semantic layer
3. Generate appropriate SQL
4. Execute and return results

## Code Structure

### `core/services/pandasai_service.py`

Main PandasAI integration:
- `query_with_pandasai()` - Main query function
- `_initialize_pandasai()` - LLM setup
- `_get_postgres_connector()` - Database connection
- `_load_semantic_layer()` - Semantic layer loading

### `core/subsystem_2/pandas_agent.py`

Updated to use PandasAI:
- `run_data_question()` - Tries PandasAI first, falls back to manual SQL
- Maintains backward compatibility

## Troubleshooting

### "Configuration Error" - Missing API Key

**Solution**: Add `OPENAI_API_KEY` to your `.env` file

### PandasAI API Errors

**Solution**: Check PandasAI v3 documentation at https://docs.pandas-ai.com/v3
- API may have changed
- Check connector syntax
- Verify semantic layer format

### Fallback to Manual SQL

If PandasAI fails, the bot automatically uses manual SQL queries. Check:
- API key is valid
- Database connection works
- Semantic layer YAML files are valid

## References

- [PandasAI v3 Documentation](https://docs.pandas-ai.com/v3/introduction)
- [Semantic Layer Documentation](./semantic_layer/README.md)
- [Project Context](./PROJECT_CONTEXT.md)

