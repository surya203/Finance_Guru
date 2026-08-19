# Finance Guru

Streamlit MVP for tracking expenses, budgets, and savings goals, with AI insights stored in Supabase.

## Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in:

- `SUPABASE_URL`
- `SUPABASE_KEY` (anon or service role key)
- `OPENAI_API_KEY` (optional; the app falls back to local advice without it)

3. Start the app from the project root:

```bash
streamlit run finance_app/app.py
```

4. Create a profile in the sidebar (name, email, monthly income), then add expenses.

There is no login flow in this MVP. Pick or create a profile; every row is stored with that `user_id`.

## Project layout

```
finance_app/
  app.py                 # Streamlit entry point
  config.py
  services/db.py         # Supabase CRUD
  services/llm.py        # OpenAI client
  services/insights.py   # Snapshot + insight generation
  modules/expenses.py
  modules/budgets.py
  modules/goals.py
  modules/chat.py
  ui/                    # One screen per feature
  prompts/               # LLM templates
schema.sql               # Live table reference
```

## Data flow

User input in Streamlit → Supabase → AI service reads the same tables → insights and chat replies are written back to `ai_insights` / `chat_history` → UI reads from the database.
