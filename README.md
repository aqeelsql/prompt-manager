# Prompt Manager

Prompt Manager is a multi-service application for creating reusable prompts, running them through an LLM, continuing multi-turn conversations, chatting with PDF or DOCX documents, tracking token usage, and reviewing prompts or complete chats.

The project uses React, FastAPI, PostgreSQL, local filesystem storage, and OpenRouter. It preserves the existing PostgreSQL database and stores uploaded document files separately on the machine running the File Service.

## Features

- Create, edit, list, execute, and delete reusable prompts.
- Treat the first message of every executed saved prompt as a system prompt.
- General multi-turn AI chat with persistent chat history.
- Upload PDF and DOCX files from the chat composer.
- Extract document text and provide it to the LLM as reference context.
- Display uploaded files beside the user message.
- Reopen files from chat history: PDFs open in a browser tab and DOCX files download.
- Render Markdown, tables, code blocks, GitHub-flavored Markdown, and KaTeX mathematics in LLM responses.
- Store prompt, completion, and total token usage for assistant messages.
- Generate conversation summaries.
- Review either a prompt or a complete chat snapshot.
- Automatically retry with a fallback OpenRouter model when the primary model fails.
- Serve the application through one Vite/Nginx URL and optionally expose it with ngrok.

## Architecture

```mermaid
flowchart LR
    UI[React + Vite :5173]
    PS[Prompt Service :8000]
    RS[Review Service :8001]
    LS[LLM Service :8002]
    FS[File Service :8003]
    OR[OpenRouter]
    DB[(PostgreSQL)]
    DISK[(Local uploads)]

    UI -->|prompts and chats| PS
    UI -->|reviews| RS
    UI -->|documents| FS
    PS -->|generate and summarize| LS
    PS -->|retrieve extracted text| FS
    RS -->|prompt or chat snapshot| PS
    LS -->|chat completions| OR
    PS --> DB
    RS --> DB
    FS --> DISK
```

The frontend uses relative `/api/...` URLs. During development, Vite proxies those requests to the correct service. The included Nginx configuration provides equivalent production routes.

## Services and ports

| Component | Default port | Responsibility |
| --- | ---: | --- |
| Prompt Service | 8000 | Prompt CRUD, chats, messages, summaries |
| Review Service | 8001 | Prompt/chat reviews and review summaries |
| LLM Service | 8002 | OpenRouter generation, fallback, usage parsing |
| File Service | 8003 | Upload, validation, extraction, storage, file serving |
| React/Vite frontend | 5173 | Browser UI and development API gateway |





FastAPI documentation is available at:

- `http://localhost:8000/docs`
- `http://localhost:8001/docs`
- `http://localhost:8002/docs`
- `http://localhost:8003/docs`

## Project structure

```text
prompt-manager-full/
|-- frontend/                 React and Vite application
|   |-- src/App.jsx           Main UI and chat interface
|   |-- src/App.css           Application styling
|   |-- src/api.js            Frontend API client
|   `-- vite.config.js        Development reverse proxies
|-- prompt_service/           Prompts, chats, messages, summaries
|-- review_service/           Prompt and chat reviews
|-- llm_service/              OpenRouter client and fallback logic
|-- file_service/             Upload, extraction, and local storage
|   `-- uploads/              Runtime files; ignored by Git
|-- tests/                    Unit and live integration tests
|-- nginx.conf                Single-origin production proxy
|-- requirements.txt          Python dependencies
|-- .env.example              Configuration template
`-- README.md
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- PostgreSQL
- An OpenRouter API key
- Optional: Nginx
- Optional: ngrok

## Configuration

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Configure at least:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/prompt_manager
OPENROUTER_API_KEY=replace_with_your_key
DEFAULT_MODEL=provider/primary-model
FALLBACK_MODEL=provider/fallback-model
```

Available variables:

| Variable | Default/example | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL URL | Shared PostgreSQL connection |
| `PROMPT_SERVICE_PORT` | `8000` | Prompt Service port reference |
| `REVIEW_SERVICE_PORT` | `8001` | Review Service port reference |
| `LLM_SERVICE_PORT` | `8002` | LLM Service port reference |
| `FILE_SERVICE_PORT` | `8003` | File Service port reference |
| `PROMPT_SERVICE_URL` | `http://localhost:8000` | Review-to-prompt calls |
| `REVIEW_SERVICE_URL` | `http://localhost:8001` | Review Service base URL |
| `LLM_SERVICE_URL` | `http://localhost:8002` | Prompt-to-LLM calls |
| `FILE_SERVICE_URL` | `http://localhost:8003` | Prompt-to-file calls |
| `OPENROUTER_API_KEY` | required | OpenRouter credential |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base |
| `DEFAULT_MODEL` | model ID | Primary model |
| `FALLBACK_MODEL` | model ID | Silent retry model |
| `LLM_CONNECT_TIMEOUT` | `5` | Prompt-to-LLM connect timeout |
| `LLM_READ_TIMEOUT` | `120` | Prompt-to-LLM response timeout |
| `OPENROUTER_CONNECT_TIMEOUT` | `5` | LLM-to-OpenRouter connect timeout |
| `OPENROUTER_READ_TIMEOUT` | `50` | OpenRouter response timeout |
| `PROMPT_CONNECT_TIMEOUT` | `5` | Review-to-prompt connect timeout |
| `PROMPT_READ_TIMEOUT` | `30` | Review-to-prompt response timeout |
| `FILE_STORAGE_DIR` | `file_service/uploads` | Local document directory |
| `MAX_FILE_SIZE_MB` | `15` | Upload size limit |
| `MAX_DOCUMENT_CONTEXT_CHARS` | `100000` | Maximum document text sent per request |
| `FILE_CONNECT_TIMEOUT` | `5` | Prompt-to-file connect timeout |
| `FILE_READ_TIMEOUT` | `30` | Prompt-to-file response timeout |

Environment values are loaded when services start. Restart the affected service after editing `.env`. Use `GET http://localhost:8002/health` to verify the active primary and fallback model IDs.

## Database setup

Create the database if it does not already exist:

```sql
CREATE DATABASE prompt_manager;
```

The application retains PostgreSQL and does not reset existing rows. Service startup performs only compatible initialization:

- Prompt Service creates `prompts`, `chats`, and `messages` when missing.
- Review Service creates `reviews` when missing.
- Review Service adds `target_type` and `chat_id` when missing.
- Supporting indexes are created with `IF NOT EXISTS`.

Main tables:

| Table | Stored data |
| --- | --- |
| `prompts` | Prompt name, description, content, timestamps |
| `chats` | Prompt reference, title, token total, summary |
| `messages` | Role, content, position, per-response token usage |
| `reviews` | Target, snapshot, reviewer, score, feedback |

Uploaded files are not placed in PostgreSQL. They are stored under `FILE_STORAGE_DIR`.

## Installation

From the project root:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install frontend packages:

```powershell
cd frontend
npm install
cd ..
```

Python packages include FastAPI, Uvicorn, HTTPX, psycopg2, pypdf, python-docx, and multipart upload support.

## Running locally

Start PostgreSQL, then open five terminals at the project root.

Terminal 1 - Prompt Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn prompt_service.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 - Review Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn review_service.main:app --reload --host 127.0.0.1 --port 8001
```

Terminal 3 - LLM Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn llm_service.main:app --reload --host 127.0.0.1 --port 8002
```

Terminal 4 - File Service:

```powershell
.\venv\Scripts\python.exe -m uvicorn file_service.main:app --reload --host 127.0.0.1 --port 8003
```

Terminal 5 - Frontend:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`.

Quick health checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8001/
Invoke-RestMethod http://127.0.0.1:8002/health
Invoke-RestMethod http://127.0.0.1:8003/health
```

## Application workflow

### Prompt workspace

1. Create a prompt with a name, optional description, and content. This only
   saves the prompt; it does not create a chat or call the LLM.
2. Select **Use prompt** when you are ready to start a conversation.
3. Prompt Service creates and opens a chat containing only the prompt content
   as its system message. The description remains metadata.
4. The LLM remains idle and token usage stays at zero until the user sends the
   first conversation message.
5. Prompt Service then sends the system prompt plus the user's message to LLM
   Service and OpenRouter.
6. The assistant response and usage are stored.
7. Selecting **Use prompt** again starts another system-only chat from the same
   saved prompt.
8. Continue the conversation, summarize it, or submit it for review.

### General and document chat

1. Start a general chat or attach a PDF/DOCX in the composer.
2. The frontend uploads the file to File Service.
3. File Service validates the extension and size.
4. The original file is saved locally.
5. Text is extracted and stored as `extracted.txt`.
6. The frontend sends the question with the document UUID.
7. Prompt Service retrieves the extracted text from File Service.
8. The document text is inserted as a system reference message.
9. LLM Service sends the prepared message list to OpenRouter.
10. The file card remains attached to the user message in chat history.

The model receives extracted text, not the binary PDF/DOCX file.

## Local document storage

Each upload receives a UUID directory:

```text
file_service/uploads/
`-- DOCUMENT_UUID/
    |-- source.pdf          Original PDF, or source.docx
    |-- extracted.txt      Extracted plain text
    `-- metadata.json      ID, filename, type, size, character count
```

PDF extraction uses `pypdf`. DOCX extraction uses `python-docx`, including paragraphs and table cells.

Current limitations:

- Only PDF and DOCX are supported.
- Scanned image-only PDFs require OCR, which is not currently included.
- Password-protected PDFs may fail if they cannot be opened without a password.
- Document context is truncated at `MAX_DOCUMENT_CONTEXT_CHARS`.
- Local uploads disappear if `FILE_STORAGE_DIR` is removed.

Document text is treated as untrusted reference content. Prompt Service adds instructions telling the model not to follow instructions embedded inside the document that attempt to override the conversation.

## Model selection and fallback

Normal prompt and chat requests use `DEFAULT_MODEL` from `.env`.

LLM Service attempts generation in this order:

1. `DEFAULT_MODEL`
2. `FALLBACK_MODEL`, when configured and different

Fallback occurs silently for upstream status errors, timeouts, connection errors, invalid model responses, or empty completions. The frontend receives the successful fallback response without being told that a retry occurred. If both models fail, LLM Service returns the final error.

The fallback cannot bypass an account-wide OpenRouter quota. If the account's free-model allowance is exhausted, both free models may fail until the quota resets or the account receives credits.

## Token accounting

OpenRouter performs model-specific tokenization and returns:

```json
{
  "prompt_tokens": 10910,
  "completion_tokens": 511,
  "total_tokens": 11421
}
```

- Prompt tokens include system instructions, document text, conversation history, and the current question.
- Completion tokens are the generated answer.
- Total tokens normally equal prompt plus completion tokens.
- Chat total is the sum of response totals stored for that conversation.

`character_count` shown on a file card is not a token count. It is the number of extracted text characters.

## API reference

### Prompt Service - port 8000

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/prompts/` | Create prompt without starting a chat |
| `GET` | `/prompts/?tag=&limit=` | List prompts |
| `GET` | `/prompts/{prompt_id}` | Retrieve prompt |
| `PUT` | `/prompts/{prompt_id}` | Update prompt |
| `DELETE` | `/prompts/{prompt_id}` | Delete prompt and related chats |
| `GET` | `/prompts/{prompt_id}/exists` | Check prompt existence |
| `POST` | `/prompts/{prompt_id}/execute` | Start a system-prompt chat without generation |
| `POST` | `/document-chats` | Start general/document chat |
| `GET` | `/chats?prompt_id=` | List chats |
| `GET` | `/chats/{chat_id}` | Retrieve complete chat |
| `POST` | `/chats/{chat_id}/messages` | Add follow-up message |
| `POST` | `/chats/{chat_id}/summary` | Generate chat summary |
| `DELETE` | `/chats/{chat_id}` | Delete chat and messages |

Start a chat:

```json
{
  "content": "Explain this document in simple terms.",
  "document_id": "OPTIONAL_DOCUMENT_UUID"
}
```

Add a message:

```json
{
  "content": "Show a Python implementation.",
  "document_id": "OPTIONAL_DOCUMENT_UUID"
}
```

### Review Service - port 8001

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/reviews/` | Create prompt/chat review |
| `GET` | `/reviews/?prompt_id=&chat_id=` | List or filter reviews |
| `GET` | `/reviews/{review_id}` | Retrieve review |
| `DELETE` | `/reviews/{review_id}` | Delete review |
| `GET` | `/reviews/{prompt_id}/summary` | Prompt review summary |
| `GET` | `/reviews/chat/{chat_id}/summary` | Chat review summary |

Prompt review:

```json
{
  "target_type": "prompt",
  "prompt_id": "PROMPT_UUID",
  "reviewer_name": "Evaluator",
  "score": 5,
  "feedback": "Clear and useful."
}
```

Chat review:

```json
{
  "target_type": "chat",
  "chat_id": "CHAT_UUID",
  "reviewer_name": "Evaluator",
  "score": 5,
  "feedback": "The complete conversation stayed on task."
}
```

Chat reviews store a complete snapshot so the evaluator can inspect the full prompt and conversation later.

### LLM Service - port 8002

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/generate` | Generate a response |
| `POST` | `/summarize` | Summarize messages |
| `GET` | `/models` | List OpenRouter models |
| `GET` | `/health` | Verify key and active model configuration |

LLM Service is stateless. Prompt Service owns chat persistence.

### File Service - port 8003

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/documents` | Upload multipart PDF/DOCX |
| `GET` | `/documents` | List document metadata |
| `GET` | `/documents/{document_id}` | Metadata plus extracted text |
| `GET` | `/documents/{document_id}/text` | Extracted text only |
| `GET` | `/documents/{document_id}/file` | Open/download original file |
| `DELETE` | `/documents/{document_id}` | Delete local document |
| `GET` | `/health` | File Service status and limits |

PDF responses use inline content disposition. DOCX responses use attachment content disposition.

## Frontend proxy routes

Vite and Nginx expose a single application origin:

| Frontend path | Target |
| --- | --- |
| `/api/prompts...` | Prompt Service |
| `/api/chats...` | Prompt Service |
| `/api/document-chats...` | Prompt Service |
| `/api/reviews...` | Review Service |
| `/api/documents...` | File Service |

This is why ngrok only needs one frontend/gateway tunnel.

## Testing

Unit tests for extraction, file serving, validation, and attachment metadata:

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
.\venv\Scripts\python.exe -m unittest tests.document_service_test tests.message_attachment_test
```

Live integration test:

```powershell
.\venv\Scripts\python.exe tests\integration_test.py
```

The live test requires Prompt, Review, and LLM services, PostgreSQL, a valid OpenRouter key, and available quota. It performs:

```text
create prompt -> load system chat -> first user message -> summarize -> review -> cleanup
```

Build the frontend:

```powershell
cd frontend
npm run build
```

Production files are generated in `frontend/dist`.

## Sharing through one ngrok link

For development, keep all services and Vite running, then:

```powershell
ngrok config add-authtoken YOUR_NGROK_TOKEN
ngrok http 5173
```

Share the HTTPS forwarding URL printed by ngrok. The Vite proxy makes the frontend and all APIs available through that single URL. Do not commit or share the ngrok authentication token.

## Nginx deployment

`nginx.conf` serves the frontend and proxies all API paths. The provided static root is `/usr/share/nginx/html`.

For a Linux/container deployment:

1. Run `npm run build` in `frontend`.
2. Copy the contents of `frontend/dist` into `/usr/share/nginx/html`.
3. Start the four FastAPI services.
4. Start Nginx with the included configuration.
5. Open port 80 or run `ngrok http 80`.

For native Windows Nginx, change the `root` directive to the absolute forward-slash path of `frontend/dist`.

## Troubleshooting

### `502 Bad Gateway`

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
Invoke-RestMethod http://127.0.0.1:8003/health
```

Common causes:

- LLM or File Service is not running.
- Invalid OpenRouter key.
- Invalid or unavailable model ID.
- OpenRouter free-model quota exhausted.
- OpenRouter timeout.
- Unsupported or unreadable document.

### Model changes are not active

Restart LLM Service after changing `.env`, then inspect:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
```

### `[WinError 10013]` when starting Uvicorn

The selected port is blocked, reserved, or already in use. Inspect it:

```powershell
Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue
```

Stop the matching process or use a different port and update the related URL and frontend proxy.

### Document uploads fail

- Confirm File Service is running on port 8003.
- Use PDF or DOCX only.
- Keep the file below `MAX_FILE_SIZE_MB`.
- Scanned PDFs need OCR and may return no extractable text.
- Confirm `FILE_STORAGE_DIR` is writable.

### Public ngrok page is unavailable

- Keep all four backend services running.
- Keep Vite or Nginx running.
- Keep the ngrok process running.
- Free ngrok URLs may change after restarting the tunnel.

## Security notes

- `.env` is ignored by Git.
- `file_service/uploads` is ignored by Git.
- Never commit database passwords, OpenRouter keys, or ngrok tokens.
- Uploaded documents are stored unencrypted on the service machine.
- The current application has no user authentication.
- An ngrok link makes the application publicly reachable while the tunnel is active; do not upload sensitive documents during public evaluation.
- Stop ngrok when sharing is no longer required.