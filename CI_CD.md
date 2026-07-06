# Dockerization, Networking, ngrok Integration & CI/CD Pipeline

## Overview

The Prompt Manager project follows a microservice architecture where every service is containerized independently using Docker. Each service is responsible for a single business capability and communicates over an isolated Docker network. An Nginx reverse proxy exposes all services through a single endpoint, while ngrok provides secure public access during development and demonstration. A GitHub Actions workflow automates image building and publishing to Docker Hub with incrementing version tags.

---

# System Architecture

```
                    Internet
                        │
                        ▼
                 ngrok Tunnel
                        │
                        ▼
                 Nginx Reverse Proxy
                        │
 ┌──────────────┬──────────────┬──────────────┬──────────────┐
 │              │              │              │              │
 ▼              ▼              ▼              ▼              ▼
Frontend   Prompt Service  Review Service  LLM Service  File Service
                        │
                        ▼
                    PostgreSQL
```

---

# Dockerized Services

Every service has its own Dockerfile.

| Service | Purpose |
|----------|----------|
| Frontend | React application |
| Prompt Service | Prompt CRUD APIs |
| Review Service | Review management |
| LLM Service | OpenRouter AI communication |
| File Service | File upload and document parsing |
| PostgreSQL | Persistent database |
| Nginx | Reverse proxy and API gateway |
| ngrok | Public tunnel |

Each service is independently buildable and deployable.

---

# Why Each Port Was Assigned

| Service | Internal Port | Reason |
|----------|--------------|--------|
| Frontend | 80 | Default Nginx web server |
| Prompt Service | 8000 | FastAPI default service |
| Review Service | 8001 | Independent API |
| LLM Service | 8002 | AI processing |
| File Service | 8003 | File upload API |
| PostgreSQL | 5432 | PostgreSQL default |
| Nginx | 80 (mapped to 8080) | Single gateway |
| ngrok | 4040 | Local inspection dashboard |

Each backend service uses a dedicated port to prevent conflicts while keeping routing simple.

---

# Why Nginx Uses Port 8080

Internally Nginx listens on port 80.

Docker maps

```
8080 → 80
```

This avoids conflicts with Windows or another local web server already using port 80.

---

# Environment Variables

Configuration is stored outside the application code using environment variables.

The project contains:

```
.env
.env.example
```

## Why?

Separating configuration from code follows the Twelve-Factor App methodology.

Benefits:

- Environment-specific configuration
- No hardcoded secrets
- Easy deployment
- Secure credential management
- Different settings for development and production

Example:

```env
DATABASE_URL=...
OPENROUTER_API_KEY=...
NGROK_AUTHTOKEN=...
```

GitHub Actions automatically creates a temporary `.env` during CI using `.env.example`.

---

# Why a Single Docker Network Was Used

All containers are connected using one bridge network.

```
prompt-network
```

Benefits:

- Automatic DNS resolution
- Container-to-container communication
- Network isolation
- Simplified service discovery

Instead of

```
localhost:8000
```

containers communicate using

```
http://prompt-service:8000
```

Docker automatically resolves container names.

---

# Service Communication

Communication occurs over Docker's internal network.

Example:

```
Frontend
      │
      ▼
Nginx
      │
      ▼
Prompt Service
```

No service communicates through localhost.

Instead:

```
prompt-service
review-service
llm-service
file-service
postgres
```

are used as hostnames.

---

# Why Docker Compose Was Used

Docker Compose provides one command to manage the complete system.

```
docker compose up
```

automatically

- Creates network
- Creates volumes
- Builds services
- Starts PostgreSQL
- Starts backend services
- Starts frontend
- Starts Nginx
- Starts ngrok

Stopping everything:

```
docker compose down
```

---

# Why Nginx Was Added

Instead of exposing every service individually,

```
8000
8001
8002
8003
```

only one endpoint is exposed.

Nginx acts as an API Gateway.

Routing example:

```
/api/prompts
        │
        ▼
Prompt Service

/api/reviews
        │
        ▼
Review Service

/api/files
        │
        ▼
File Service
```

Benefits:

- Single entry point
- Cleaner URLs
- Easier deployment
- Easier HTTPS configuration
- Better scalability

---

# ngrok Integration

## Purpose

ngrok exposes the locally running Docker application to the Internet.

Instead of exposing every service individually,

ngrok tunnels only Nginx.

```
Internet
      │
      ▼
ngrok
      │
      ▼
Nginx
```

Therefore the user receives a single public URL.

Example

```
https://xxxx.ngrok-free.app
```

This URL automatically routes all frontend and backend requests.

---

# Can ngrok Be Used Inside Docker Compose?

Yes.

A dedicated ngrok container is added to Docker Compose.

Example:

```yaml
ngrok:
  image: ngrok/ngrok:latest
  command: http http://nginx:80
```

Benefits:

- Starts automatically
- No manual ngrok commands
- Fully reproducible
- Works with one Docker command

---

# One Command Deployment

After Docker installation, the complete application starts using

```
docker compose up -d
```

This performs:

1. Builds all services
2. Starts PostgreSQL
3. Starts backend services
4. Starts frontend
5. Starts Nginx
6. Starts ngrok

No manual startup is required.

---

# Docker Hub Release

Every service is published to Docker Hub.

Published images:

- prompt-service
- review-service
- llm-service
- file-service
- frontend

Each image receives two tags.

Example

```
v15
latest
```

---

# CI/CD Workflow

GitHub Actions automates image publishing.

Pipeline:

```
Push
 │
 ▼
Checkout
 │
 ▼
Create .env
 │
 ▼
Validate Docker Compose
 │
 ▼
Compile Python
 │
 ▼
Build Images
 │
 ▼
Publish Images
```

---

# Incrementing Version Tags

Instead of manually managing versions,

GitHub Actions uses

```
github.run_number
```

Result

```
v1
v2
v3
v4
...
```

Every successful push generates a new version automatically.

---

# Preventing Broken Releases

The workflow contains two jobs.

```
verify
publish
```

The publish job depends on verify.

```
publish

needs: verify

if: success()
```

Meaning:

If

- Docker Compose validation fails
- Python compilation fails
- Docker build fails

then

```
Publish Job

SKIPPED
```

No image is uploaded to Docker Hub.

This ensures only verified builds become releases.

---

# Verification Performed

The workflow automatically performs:

- Repository checkout
- Environment creation
- Docker Compose validation
- Python syntax validation
- Docker image build verification
- Docker Hub authentication
- Image publishing

Only successful builds are published.

---

# Docker Volumes

Two Docker volumes are used.

## PostgreSQL Volume

```
postgres_data
```

Purpose:

Persist database even after containers are removed.

## File Upload Volume

```
file_uploads
```

Purpose:

Persist uploaded files independently of containers.

---

# Advantages of the Architecture

- Independent microservices
- Container isolation
- Reproducible deployment
- Single command startup
- Automatic versioned releases
- Secure environment management
- Public accessibility through ngrok
- Centralized routing using Nginx
- Automated CI/CD pipeline
- Easy scalability for future services

---

# Conclusion

The project successfully implements a complete containerized microservice architecture. Every service is independently dockerized, connected through a shared Docker bridge network, routed via Nginx, publicly accessible through ngrok, and automatically built and released using GitHub Actions. The CI/CD pipeline validates the project before publishing Docker images, ensuring that only verified builds are released with incrementing version numbers.