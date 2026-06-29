# Prompt Manager System

Week 1 project using:

- FastAPI
- MVC architecture
- PostgreSQL persistence
- Two services: `prompt_service` and `review_service`
- `httpx` service-to-service communication
- Vite + React frontend
- `nginx.conf` reverse proxy config

## Project Structure

```text
prompt-manager-full/
├── .env
├── requirements.txt
├── nginx.conf
├── prompt_service/
├── review_service/
└── frontend/
```

## 1. Create PostgreSQL Database

Open PostgreSQL shell and run:

```sql
CREATE DATABASE prompt_manager;
```

If your PostgreSQL password is different, update `.env`:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/prompt_manager
```

## 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 3. Run Prompt Service

From the project root:

```bash
uvicorn prompt_service.main:app --reload --port 8000
```

Swagger:

```text
http://localhost:8000/docs
```

## 4. Run Review Service

Open another terminal from the project root:

```bash
uvicorn review_service.main:app --reload --port 8001
```

Swagger:

```text
http://localhost:8001/docs
```

## 5. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## 6. Nginx Usage

Build frontend:

```bash
cd frontend
npm run build
```

Copy `frontend/dist` contents into Nginx html folder and use the provided `nginx.conf`.

## API Endpoints

### Prompt Service

- `POST /prompts/`
- `GET /prompts/`
- `GET /prompts/{prompt_id}`
- `PUT /prompts/{prompt_id}`
- `DELETE /prompts/{prompt_id}`
- `GET /prompts/{prompt_id}/exists`

### Review Service

- `POST /reviews/`
- `GET /reviews/`
- `GET /reviews/{review_id}`
- `GET /reviews/{prompt_id}/summary`

## Suggested Granular Git Commits

```bash
git add .
git commit -m "setup project structure"

git add prompt_service
git commit -m "add prompt service mvc crud with postgres"

git add review_service
git commit -m "add review service with httpx integration"

git add frontend
git commit -m "add vite react frontend"

git add nginx.conf README.md
git commit -m "add nginx config and setup guide"
```
