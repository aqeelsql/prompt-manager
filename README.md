# Prompt Manager

Prompt Manager is a full-stack, multi-service LLM application for creating reusable prompts, starting agent-like chats from those prompts, chatting with PDF/DOCX documents, tracking usage, summarizing conversations, and saving evaluator reviews.

The project uses React, FastAPI microservices, PostgreSQL, OpenRouter, local filesystem document storage, Docker Compose, NGINX, and optional ngrok sharing.

## Main features

- Create, edit, list, use, and delete reusable prompts.
- Use a saved prompt as hidden system context for a chat.
- Start normal ChatGPT/Claude-style chats from the main chat screen.
- Upload PDF or DOCX files directly inside chat.
- Extract text from uploaded documents and pass it to the LLM as context.
- Store uploaded files locally and allow users to reopen/download them from chat history.
- Render Markdown, tables, code blocks, GitHub-flavored Markdown, and KaTeX math.
- Track prompt, completion, and total token usage returned by OpenRouter.
- Generate conversation summaries.
- Create reviews for either prompts or complete chat snapshots.
- Retry silently with a fallback model when the primary model fails.
- Run locally with separate services or run the whole stack with Docker Compose.
- Serve everything through one NGINX gateway URL and expose it with ngrok.

## Architecture

```mermaid
flowchart LR
    Browser[Browser]
    Vite[React/Vite dev server :5173]
    Gateway[NGINX gateway :8080]
    Frontend[Frontend container NGINX :80]
    Prompt[Prompt Service :8000]
    Review[Review Service :8001]
    LLM[LLM Service :8002]
    File[File Service :8003]
    DB[(PostgreSQL :5432)]
    Uploads[(Local / Docker volume uploads)]
    OpenRouter[OpenRouter API]
    Ngrok[ngrok public URL]

    Browser -->|local dev| Vite
    Browser -->|Docker| Gateway
    Ngrok --> Gateway
    Gateway --> Frontend
    Vite -->|/api/prompts /api/chats /api/document-chats| Prompt
    Vite -->|/api/reviews| Review
    Vite -->|/api/documents| File
    Gateway -->|/api/prompts /api/chats /api/document-chats| Prompt
    Gateway -->|/api/reviews| Review
    Gateway -->|/api/documents| File
    Prompt --> DB
    Review --> DB
    Review -->|fetch prompt/chat snapshots| Prompt
    Prompt -->|generate/summarize| LLM
    Prompt -->|fetch extracted document text| File
    File --> Uploads
    LLM --> OpenRouter
```

### Request flow

For a normal prompt chat:

```text
Browser -> Frontend -> Prompt Service -> LLM Service -> OpenRouter
                         |
                         +-> PostgreSQL
```

For a document chat:

```text
Browser -> File Service -> local upload storage
Browser -> Prompt Service -> File Service extracted text
Prompt Service -> LLM Service -> OpenRouter
```

For a review:

```text
Browser -> Review Service -> Prompt Service snapshot lookup
Review Service -> PostgreSQL
```

## Services and ports

| Service | Port | Responsibility |
| --- | ---: | --- |
| Frontend dev server | 5173 | React UI during local development |
| Prompt Service | 8000 | Prompt CRUD, chats, messages, summaries |
| Review Service | 8001 | Reviews for prompts and chats |
| LLM Service | 8002 | OpenRouter requests, model fallback, usage parsing |
| File Service | 8003 | PDF/DOCX upload, extraction, local file serving |
| PostgreSQL | 5432 | Prompt/chat/review persistence |
| Docker NGINX gateway | 8080 | Single URL for frontend and APIs |
| ngrok inspector | 4040 | Local ngrok tunnel inspection/API |

FastAPI docs:

- `http://localhost:8000/docs` - Prompt Service
- `http://localhost:8001/docs` - Review Service
- `http://localhost:8002/docs` - LLM Service
- `http://localhost:8003/docs` - File Service

## Project structure

```text
prompt-manager-full/
|-- frontend/                  React/Vite UI
|   |-- src/App.jsx            Main application UI and chat workspace
|   |-- src/api.js             Frontend API client using /api routes
|   |-- src/App.css            Styling
|   |-- vite.config.js         Local dev proxy to FastAPI services
|   |-- Dockerfile             Builds static frontend image
|   `-- dist/                  Production build output
|-- prompt_service/            Prompt CRUD, chats, messages, summaries
|   |-- controllers/
|   |-- models/
|   |-- schemas/
|   |-- views/
|   |-- database.py            Prompt/chat schema initialization
|   `-- Dockerfile
|-- review_service/            Review creation and summaries
|   |-- controllers/
|   |-- models/
|   |-- schemas/
|   |-- views/
|   |-- database.py            Review schema initialization
|   `-- Dockerfile
|-- llm_service/               OpenRouter integration and fallback model logic
|   |-- main.py
|   |-- schemas.py
|   |-- config.py
|   `-- Dockerfile
|-- file_service/              Document upload, extraction, file retrieval
|   |-- main.py
|   |-- storage.py
|   |-- schemas.py
|   |-- uploads/               Local runtime uploads; ignored by Git
|   `-- Dockerfile
|-- tests/                     Unit and integration tests
|-- .github/workflows/         Docker image build/publish workflow
|-- docker-compose.yml         Full Docker stack
|-- nginx.conf                 Docker gateway reverse proxy
|-- requirements.txt           Python dependencies
|-- .env.example               Safe local env template
|-- .dockerignore              Docker build exclusions
`-- README.md
```

## Local vs Docker configuration

The project intentionally uses different hostnames in local mode and Docker mode.

Local services run on Windows/host machine, so `.env` uses `localhost`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/prompt_manager
PROMPT_SERVICE_URL=http://localhost:8000
REVIEW_SERVICE_URL=http://localhost:8001
LLM_SERVICE_URL=http://localhost:8002
FILE_SERVICE_URL=http://localhost:8003
```

Docker containers talk to each other using Docker service names. `docker-compose.yml` overrides those values inside containers:

```yaml
DATABASE_URL: postgresql://postgres:12345@postgres:5432/prompt_manager
PROMPT_SERVICE_URL: http://prompt-service:8000
REVIEW_SERVICE_URL: http://review-service:8001
LLM_SERVICE_URL: http://llm-service:8002
FILE_SERVICE_URL: http://file-service:8003
```

This lets the same code run locally and inside Docker without changing the database schema.

## Environment variables

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Set at least:

```env
DATABASE_URL=postgresql://postgres:12345@localhost:5432/prompt_manager
OPENROUTER_API_KEY=your_openrouter_key
DEFAULT_MODEL=openai/gpt-oss-20b
FALLBACK_MODEL=openai/gpt-4o-mini
NGROK_AUTHTOKEN=your_ngrok_token_if_using_ngrok
```

Important variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `PROMPT_SERVICE_PORT` | Prompt Service port reference |
| `REVIEW_SERVICE_PORT` | Review Service port reference |
| `LLM_SERVICE_PORT` | LLM Service port reference |
| `FILE_SERVICE_PORT` | File Service port reference |
| `PROMPT_SERVICE_URL` | Base URL used for prompt-service calls |
| `REVIEW_SERVICE_URL` | Review service URL reference |
| `LLM_SERVICE_URL` | Prompt Service -> LLM Service URL |
| `FILE_SERVICE_URL` | Prompt Service -> File Service URL |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL |
| `DEFAULT_MODEL` | Primary model ID |
| `FALLBACK_MODEL` | Silent fallback model ID |
| `OPENROUTER_CONNECT_TIMEOUT` | LLM Service -> OpenRouter connect timeout |
| `OPENROUTER_READ_TIMEOUT` | LLM Service -> OpenRouter read timeout |
| `LLM_CONNECT_TIMEOUT` | Prompt Service -> LLM Service connect timeout |
| `LLM_READ_TIMEOUT` | Prompt Service -> LLM Service read timeout |
| `PROMPT_CONNECT_TIMEOUT` | Review Service -> Prompt Service connect timeout |
| `PROMPT_READ_TIMEOUT` | Review Service -> Prompt Service read timeout |
| `FILE_CONNECT_TIMEOUT` | Prompt Service -> File Service connect timeout |
| `FILE_READ_TIMEOUT` | Prompt Service -> File Service read timeout |
| `FILE_STORAGE_DIR` | Local document storage folder |
| `MAX_FILE_SIZE_MB` | Upload size limit |
| `MAX_DOCUMENT_CONTEXT_CHARS` | Max extracted document text sent to LLM |
| `NGROK_AUTHTOKEN` | Token used by the ngrok Docker container |

Never commit a real `.env` file.

## Database and persistence

The project uses PostgreSQL for prompts, chats, messages, and reviews.

Tables initialized by Prompt Service:

| Table | Data |
| --- | --- |
| `prompts` | Prompt name, description, content, tags, optional target model, timestamps |
| `chats` | Prompt reference, title, selected model, total tokens, summary, timestamps |
| `messages` | Chat messages, role, content, position, token usage |

Tables initialized by Review Service:

| Table | Data |
| --- | --- |
| `reviews` | Prompt/chat target, frozen snapshot, reviewer, score, feedback |

The app does not reset or drop existing data on startup. It uses `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, and `CREATE INDEX IF NOT EXISTS`.

Document files are not stored in PostgreSQL. They are stored on disk by File Service.

## Hidden system prompt behavior

Saved prompt execution works like this:

1. The user creates a prompt in Workspace.
2. Creating the prompt only saves it. It does not call the LLM.
3. The user clicks **Use prompt**.
4. Prompt Service creates a chat whose first internal message is the saved prompt content.
5. That first message is marked with `llm_role: "system"`.
6. The frontend filters out system messages, so the prompt does not appear in the chat box.
7. The LLM still does not reply until the user sends the first real chat message.
8. When the user sends a message, Prompt Service sends this to LLM Service:

```text
system: saved prompt content
user: user's message
```

This makes every saved prompt act like a different agent/system instruction.

Implementation detail: the database `messages.role` column only allows `user` and `assistant`, so system-role metadata is stored inside the message content using an internal marker. This avoids changing the existing database schema.

## Document upload and chat behavior

The chat composer supports PDF and DOCX uploads.

Flow:

1. User attaches a PDF or DOCX file.
2. Frontend uploads it to File Service.
3. File Service validates the filename, extension, and size.
4. File Service saves the original file locally.
5. File Service extracts text using:
   - `pypdf` for PDF
   - `python-docx` for DOCX
6. Extracted text is saved as `extracted.txt`.
7. When the user sends a chat message, Prompt Service retrieves the extracted text by document ID.
8. Prompt Service inserts the extracted text as system reference context.
9. LLM Service sends the prepared messages to OpenRouter.
10. The frontend shows the file card beside the user message.

Storage layout:

```text
file_service/uploads/
`-- DOCUMENT_UUID/
    |-- source.pdf or source.docx
    |-- extracted.txt
    `-- metadata.json
```

Limitations:

- Only `.pdf` and `.docx` are supported.
- Scanned image-only PDFs need OCR, which is not included.
- Password-protected PDFs may fail.
- Large extracted documents are truncated at `MAX_DOCUMENT_CONTEXT_CHARS`.
- Local files are unencrypted on disk.

## LLM service and fallback model

LLM Service is stateless. Prompt Service owns chat storage.

Generation order:

1. Try `DEFAULT_MODEL`.
2. If it fails, silently retry `FALLBACK_MODEL` when configured and different.
3. Return the successful response to the frontend.
4. If both fail, return an error.

Fallback is attempted for upstream errors, timeouts, connection errors, empty completions, invalid model responses, and other generation failures.

Fallback cannot bypass account-level OpenRouter limits. If the API key has no quota, both models can fail.

LLM Service also exposes:

- `GET /health` - shows API key status and configured model IDs.
- `GET /models` - fetches available models from OpenRouter.

The model getter exists in the backend only. The frontend does not currently show a model picker.

## Token accounting

Token counts come from OpenRouter's response usage object:

```json
{
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "total_tokens": 150
}
```

Prompt tokens include system messages, document context, chat history, and the current user message. Completion tokens are the assistant output. Chat total is accumulated from stored assistant responses.

A document's `character_count` is not a token count. It is only the number of extracted text characters.

## Running locally

### 1. Install Python dependencies

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### 3. Start PostgreSQL

You can use a normal local PostgreSQL installation, or only start the Docker PostgreSQL service:

```powershell
docker compose up -d postgres
```

The local `.env` should point to `localhost:5432`.

### 4. Start backend services

Open separate terminals from the project root.

Prompt Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn prompt_service.main:app --reload --host 127.0.0.1 --port 8000
```

Review Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn review_service.main:app --reload --host 127.0.0.1 --port 8001
```

LLM Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn llm_service.main:app --reload --host 127.0.0.1 --port 8002
```

File Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn file_service.main:app --reload --host 127.0.0.1 --port 8003
```

### 5. Start frontend

```powershell
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

## Running with Docker Compose

Docker Compose starts the full stack:

- PostgreSQL
- Prompt Service
- Review Service
- LLM Service
- File Service
- Frontend static server
- NGINX gateway
- ngrok tunnel container

Run:

```powershell
docker compose up --build
```

Open the Docker gateway:

```text
http://localhost:8080
```

Docker Compose uses a single Docker bridge network named `prompt-network`. This allows containers to call each other by service name, for example `http://prompt-service:8000` and `postgres:5432`.

PostgreSQL data is stored in the Docker volume `postgres_data`. Uploaded documents are stored in the Docker volume `file_uploads` mounted at `/app/file_service/uploads`.

### Docker build authentication issue

If Docker build fails with:

```text
401 Unauthorized: incorrect username or password
```

The issue is Docker Hub authentication, usually while pulling `node:20-alpine`, `python:3.11-slim`, or another base image.

Fix:

```powershell
docker logout
docker login
docker pull node:20-alpine
docker compose up --build
```

If Docker keeps using stale app behavior, rebuild without cache:

```powershell
docker compose down
docker compose build --no-cache
docker compose up
```

## NGINX and single-link routing

The frontend uses relative `/api/...` paths. Both Vite and NGINX route those paths to the correct backend service.

| Public path | Service target |
| --- | --- |
| `/` | Frontend app |
| `/api/prompts/...` | Prompt Service `/prompts/...` |
| `/api/chats...` | Prompt Service `/chats...` |
| `/api/document-chats...` | Prompt Service `/document-chats...` |
| `/api/reviews/...` | Review Service `/reviews/...` |
| `/api/documents...` | File Service `/documents...` |

In Docker, the gateway is `nginx` service on port 80 inside the Docker network and port 8080 on the host.

## Sharing with ngrok

The Docker Compose stack includes an ngrok container. It tunnels the NGINX gateway:

```text
ngrok -> http://nginx:80 -> frontend and APIs
```

Set `NGROK_AUTHTOKEN` in `.env`, then run:

```powershell
docker compose up --build
```

Get the public URL from the ngrok local API:

```powershell
Invoke-RestMethod http://localhost:4040/api/tunnels
```

Share the HTTPS forwarding URL.

If the ngrok page shows old behavior, rebuild the Docker images. Ngrok exposes the Docker stack; it does not expose your local Vite dev server.

## API reference

### Prompt Service - port 8000

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service status |
| `POST` | `/prompts/` | Create prompt |
| `GET` | `/prompts/?tag=&limit=` | List prompts |
| `GET` | `/prompts/{prompt_id}` | Get prompt |
| `PUT` | `/prompts/{prompt_id}` | Update prompt |
| `DELETE` | `/prompts/{prompt_id}` | Delete prompt |
| `GET` | `/prompts/{prompt_id}/exists` | Check prompt existence |
| `POST` | `/prompts/{prompt_id}/execute` | Create hidden system-prompt chat without generation |
| `POST` | `/document-chats` | Start a general/document chat |
| `GET` | `/chats?prompt_id=` | List chats |
| `GET` | `/chats/{chat_id}` | Get full chat |
| `POST` | `/chats/{chat_id}/messages` | Add chat message and generate response |
| `POST` | `/chats/{chat_id}/summary` | Generate/update summary |
| `DELETE` | `/chats/{chat_id}` | Delete chat |

Create prompt body:

```json
{
  "name": "Python tutor",
  "description": "Answers as a concise coding helper",
  "content": "You are a Python tutor. Keep answers short and practical.",
  "tags": "coding,python",
  "model_target": null
}
```

Start chat body:

```json
{
  "content": "Explain this file.",
  "document_id": "optional-document-uuid"
}
```

Add message body:

```json
{
  "content": "Now generate the code.",
  "document_id": "optional-document-uuid"
}
```

### Review Service - port 8001

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service status |
| `POST` | `/reviews/` | Create review |
| `GET` | `/reviews/?prompt_id=&chat_id=` | List/filter reviews |
| `GET` | `/reviews/{review_id}` | Get review |
| `DELETE` | `/reviews/{review_id}` | Delete review |
| `GET` | `/reviews/{prompt_id}/summary` | Prompt review summary |
| `GET` | `/reviews/chat/{chat_id}/summary` | Chat review summary |

Prompt review body:

```json
{
  "target_type": "prompt",
  "prompt_id": "prompt-uuid",
  "reviewer_name": "Evaluator",
  "score": 5,
  "feedback": "Clear prompt."
}
```

Chat review body:

```json
{
  "target_type": "chat",
  "chat_id": "chat-uuid",
  "reviewer_name": "Evaluator",
  "score": 5,
  "feedback": "Conversation followed the file context."
}
```

### LLM Service - port 8002

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API key and model configuration status |
| `GET` | `/models` | Get OpenRouter model list |
| `POST` | `/generate` | Generate assistant response |
| `POST` | `/summarize` | Summarize a conversation |

Generate body:

```json
{
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Say hello."}
  ],
  "temperature": 0.2,
  "max_tokens": 300
}
```

### File Service - port 8003

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service status |
| `GET` | `/health` | Supported formats and limits |
| `POST` | `/documents` | Upload PDF/DOCX multipart file |
| `GET` | `/documents` | List documents |
| `GET` | `/documents/{document_id}` | Metadata plus extracted text |
| `GET` | `/documents/{document_id}/text` | Extracted text only |
| `GET` | `/documents/{document_id}/file` | Open/download original file |
| `DELETE` | `/documents/{document_id}` | Delete document |

## Testing

Run local unit tests:

```powershell
.\venv\Scripts\python.exe -m unittest tests.document_service_test tests.message_attachment_test tests.prompt_system_flow_test
```

Run the live integration test after services are running:

```powershell
.\venv\Scripts\python.exe tests\integration_test.py
```

The integration test performs:

```text
create prompt -> Use prompt -> hidden system chat -> first user message -> summarize -> review -> cleanup
```

Build frontend locally:

```powershell
cd frontend
npm run build
```

Validate Docker Compose:

```powershell
docker compose config --quiet
```

## CI/CD workflow

The repository includes `.github/workflows/docker.yaml`.

On push to `main`, the workflow:

1. Checks out the repository.
2. Creates `.env` from `.env.example`.
3. Validates Docker Compose.
4. Compiles each Python service.
5. Builds all Docker images.
6. Logs in to Docker Hub using repository secrets.
7. Pushes five images:
   - `prompt-service`
   - `review-service`
   - `llm-service`
   - `file-service`
   - `frontend`
8. Tags each image with:
   - `v${{ github.run_number }}`
   - `latest`

Required GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password or access token |

## Troubleshooting

### Docker build returns `401 Unauthorized`

Cause: Docker Hub login is missing, expired, or incorrect.

Fix:

```powershell
docker logout
docker login
docker pull node:20-alpine
docker compose up --build
```

### Local services fail with `could not translate host name "postgres"`

Cause: `.env` is using Docker hostnames while running locally.

Fix local `.env`:

```env
DATABASE_URL=postgresql://postgres:12345@localhost:5432/prompt_manager
```

Docker Compose already overrides this back to `postgres` inside containers.

### Prompt Service or Review Service cannot connect to PostgreSQL

Check that PostgreSQL is running and reachable:

```powershell
docker compose up -d postgres
```

or verify your local PostgreSQL installation is listening on port 5432.

### `502 Bad Gateway` in the frontend

Common causes:

- LLM Service is not running.
- File Service is not running.
- OpenRouter key is missing or invalid.
- Model ID is invalid or unavailable.
- OpenRouter quota is exhausted.
- Docker/ngrok is serving stale images.

Check:

```powershell
Invoke-RestMethod http://localhost:8002/health
Invoke-RestMethod http://localhost:8003/health
```

### Model changes are not active

Restart LLM Service after changing `.env`, then check:

```powershell
Invoke-RestMethod http://localhost:8002/health
```

### ngrok shows old frontend behavior

Ngrok exposes Docker NGINX, not your local dev server. Rebuild containers:

```powershell
docker compose down
docker compose build --no-cache
docker compose up
```

Then hard-refresh the browser or use an incognito window.

### Uploaded PDF/DOCX fails

Common causes:

- Unsupported file type.
- File exceeds `MAX_FILE_SIZE_MB`.
- PDF is scanned/image-only and has no extractable text.
- PDF is password protected.
- `FILE_STORAGE_DIR` is not writable.

### `[WinError 10013]` when starting Uvicorn

The port is already used or blocked. Check the port:

```powershell
Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue
```

Use a free port or stop the process using it.

## Security notes

- `.env` is ignored by Git and must never be committed.
- Do not commit OpenRouter keys, Docker Hub credentials, database passwords, or ngrok tokens.
- Uploaded documents are stored unencrypted on disk.
- The current application has no authentication layer.
- A public ngrok URL exposes the app while the tunnel is active.
- Do not upload sensitive private documents during public evaluation.

## Quick command reference

Local frontend:

```powershell
cd frontend
npm run dev
```

Full Docker stack:

```powershell
docker compose up --build
```

Docker gateway:

```text
http://localhost:8080
```

ngrok tunnel list:

```powershell
Invoke-RestMethod http://localhost:4040/api/tunnels
```

LLM health:

```powershell
Invoke-RestMethod http://localhost:8002/health
```