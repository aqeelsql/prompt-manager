# Prompt Manager System — Week 2

The Week 1 FastAPI/PostgreSQL project now supports live LLM execution,
multi-turn chats, token accounting, summaries, and reviews of complete
conversations

PostgreSQL has intentionally been retained. The existing `DATABASE_URL`,
`prompts` table, `reviews` table, and stored rows are preserved. Startup adds
the Week 2 `chats` and `messages` tables and two backward-compatible columns
to `reviews` (`target_type` and `chat_id`).

## Architecture

```mermaid
flowchart LR
    UI[React frontend]
    PS[prompt-service :8000]
    LS[llm-service :8002]
    OR[OpenRouter API]
    RS[review-service :8001]
    DB[(Existing PostgreSQL)]

    UI -->|prompts, chats| PS
    PS -->|async generate / summarize| LS
    LS -->|async chat completions| OR
    UI -->|reviews| RS
    RS -->|async prompt/chat snapshot| PS
    PS -->|owns prompts, chats, messages| DB
    RS -->|owns reviews| DB
```

There is no API gateway between services. The Vite/Nginx routes are frontend
reverse proxies only. Review-service obtains prompt and chat data over HTTP;
it never queries prompt-service tables directly.

## What Week 2 adds

- A stateless `llm-service` with shared `httpx.AsyncClient` access to
  OpenRouter.
- Async prompt execution, follow-up messages, and conversation summaries.
- Per-assistant-message token usage plus a running chat total.
- Full chat snapshots for reviews while keeping prompt reviews compatible.
- Explicit 502/503/504 handling for upstream, connection, and timeout errors.
- `asyncio.to_thread` around database work inside async request flows.
- A React conversation UI with loading states, token counts, summaries, and
  prompt/chat review selection.

## Setup

1. Create the existing PostgreSQL database if it does not already exist:

   ```sql
   CREATE DATABASE prompt_manager;
   ```

2. Copy `.env.example` to `.env` and fill in your existing PostgreSQL
   connection, OpenRouter key, and chosen OpenRouter model:

   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/prompt_manager
   OPENROUTER_API_KEY=replace_with_your_key
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   DEFAULT_MODEL=your-provider/your-model
   PROMPT_SERVICE_URL=http://localhost:8000
   REVIEW_SERVICE_URL=http://localhost:8001
   LLM_SERVICE_URL=http://localhost:8002
   ```

3. Install dependencies:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   cd frontend
   npm install
   ```

## Run all services

Open four terminals at the project root:

```powershell
.\venv\Scripts\python.exe -m uvicorn prompt_service.main:app --reload --port 8000
```

```powershell
.\venv\Scripts\python.exe -m uvicorn review_service.main:app --reload --port 8001
```

```powershell
.\venv\Scripts\python.exe -m uvicorn llm_service.main:app --reload --port 8002
```

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. Interactive API documentation is available at
ports 8000, 8001, and 8002 under `/docs`.

## Week 2 endpoints

### prompt-service

- `POST /prompts/{id}/execute`
- `GET /chats?prompt_id=`
- `GET /chats/{chat_id}`
- `POST /chats/{chat_id}/messages`
- `POST /chats/{chat_id}/summary`
- `DELETE /chats/{chat_id}`

All Week 1 prompt CRUD endpoints remain available.

### llm-service

- `POST /generate`
- `POST /summarize`
- `GET /models`
- `GET /health`

### review-service

- `POST /reviews/` with `target_type: "prompt" | "chat"`
- `GET /reviews/?prompt_id=&chat_id=`
- `GET /reviews/{review_id}`
- `GET /reviews/{prompt_id}/summary`
- `GET /reviews/chat/{chat_id}/summary`

The original prompt-review request remains valid:

```json
{
  "prompt_id": "PROMPT_UUID",
  "reviewer_name": "Reviewer",
  "score": 5,
  "feedback": "Clear and useful."
}
```

A chat review uses:

```json
{
  "target_type": "chat",
  "chat_id": "CHAT_UUID",
  "reviewer_name": "Reviewer",
  "score": 5,
  "feedback": "The full exchange stayed on task."
}
```

## Live integration test

With all three services running and a valid OpenRouter key configured:

```powershell
.\venv\Scripts\python.exe tests\integration_test.py
```

The test performs `create → execute → follow-up → summarize → review` and
cleans up its temporary records.

## Secret handling

`.env` is ignored and `.env.example` contains placeholders only. Never commit
an OpenRouter key or database password.
