# AURA Backend

Minimal FastAPI service for the AURA mobile app.

## Endpoints

- `POST /chat` — accepts `{conversationId, message}`, returns `{reply}`
- `GET /context` — returns recent conversations (stub until persistence is added)
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

The API will be available at `http://localhost:8000`.

## Testing the API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"conversationId": "local", "message": "Hello AURA"}'
```

## Deployment

The included `Dockerfile` works on most container platforms.

### Railway / Render / Fly.io

1. Push this repo to GitHub
2. Create a new service and point it at the `backend/` directory
3. Set environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional)
4. Expose port `8000`

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `AURA_SYSTEM_PROMPT` | No | Override the assistant persona |

## Next steps

- Add real conversation persistence (SQLite/Postgres)
- Add SSE or WebSocket streaming for `/chat`
- Add authentication for mobile clients
- Implement `GET /context` with real data
