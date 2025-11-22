
Cursor must NOT break this organization.

### Slack Interface Layer
- Must use `slack_bolt` (Socket Mode).
- Only handles: receiving messages, calling the router, and sending responses.
- No SQL, no analysis, no business logic belongs here.

### Router
- Must classify user messages into:
  - small_talk
  - unknown
  - users
  - payments
  - sessions
  - subscriptions

Router returns a simple, typed response object used by `main.py`.

### Data Agent Layer
- Implements SQL access using **psycopg2**.
- Must read DB credentials from environment variables:
  - `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`
- Must NOT call Slack directly.
- SQL must match the existing Postgres schema defined in the Semantic Layer YAMLs.

---

## 2. PandasAI Rules

Cursor must always use **PandasAI v3 syntax**.  
Do NOT generate code using legacy PandasAI v1/v2 APIs.

- Use `pandasai.SemanticLayer`
- Use `pai.load()` instead of deprecated functions
- Do NOT generate code with `.run()` or `.chat()` unless documented for v3

If unsure, Cursor must always check:
https://docs.pandas-ai.com/v3

---

## 3. Coding Rules

### General
- All functions must include docstrings.
- Avoid circular imports.
- Think carefully about subsystem boundaries.
- Never hard-code absolute file paths.

### SQL
- Must use RealDictCursor
- Must sanitize dynamic parameters with `%s`
- Must close connections with `finally: conn.close()`

### Error Handling
- Never crash the bot in Slack.
- All raised errors must be caught and returned as safe messages using:
  ```python
  return f"Internal error: {e}"
