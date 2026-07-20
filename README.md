# AURA Backend

FastAPI service for the AURA mobile app, with SQLite persistence via SQLModel.
All response JSON keys are camelCase to match the Flutter freezed client.

## Endpoints

- `POST /chat` — accepts `{conversationId, message}`, returns `{reply}`. Persists both messages and includes the last ~20 messages of conversation history in the LLM call. Auto-creates the conversation on first use (title = first user message, truncated to ~40 chars). Returns 500 if `OPENAI_API_KEY` is not configured, 502 on LLM failure.
- `GET /context` — conversations from the DB, most recent first: `[{id, title, preview, updatedAt}]`
- `GET /goals` — `[{id, title, isCompleted, dueDate?}]`
- `POST /goals/{id}/toggle` — flips `isCompleted`, returns the updated goal (404 for unknown id)
- `GET /calendar` — `[{id, title, start, end?, location?}]` (ISO datetimes)
- `GET /memory` — `[{id, title, description, category, timestamp, isImportant}]`, category in `event|goal|preference|note|milestone`
- `GET /briefing` — `{date, headline, summary, weather, meetings, goals, suggestions}`; headline/summary/suggestions are LLM-generated when a key is configured, otherwise a deterministic template from the day's goals/events
- `GET /summary` — `{summary}`, a "your day at a glance" sentence or two (LLM or template fallback)
- `GET /weather` — `{temperatureC, condition, highC, lowC}`; deterministic stub, see `weather.py` for where a real provider plugs in
- `GET /health` — health check

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then add your OPENAI_API_KEY
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. `.env` is loaded at
startup via python-dotenv. The SQLite database (`aura.db` by default) is
created automatically, and seeded with demo goals/events/memories on first
run. `/briefing`, `/summary`, and `/weather` work without an OpenAI key;
`/chat` requires one.

## Testing the API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"conversationId": "local", "message": "Hello AURA"}'

curl http://localhost:8000/briefing
curl -X POST http://localhost:8000/goals/1/toggle
```

## Deployment

The included `Dockerfile` works on most container platforms.

### Railway / Render / Fly.io

1. Push this repo to GitHub
2. Create a new service and point it at the `backend/` directory
3. Set environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional)
   - `AURA_DB_URL` (optional; defaults to a local SQLite file)
4. Expose port `8000`

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For `/chat` and LLM-generated briefing/summary | Your OpenAI API key |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `AURA_SYSTEM_PROMPT` | No | Override the assistant persona |
| `AURA_DB_URL` | No | SQLAlchemy URL, defaults to `sqlite:///./aura.db` |

## Next steps

- Add SSE or WebSocket streaming for `/chat`
- Add authentication for mobile clients
- Swap the weather stub for a real provider
