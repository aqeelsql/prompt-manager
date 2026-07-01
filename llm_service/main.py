import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request

from llm_service.config import (
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_CONNECT_TIMEOUT,
    OPENROUTER_READ_TIMEOUT,
)
from llm_service.schemas import (
    GenerateRequest,
    GenerateResponse,
    SummarizeRequest,
    TokenUsage,
)

logger = logging.getLogger("llm_service")

SUMMARY_SYSTEM_PROMPT = (
    "Summarize the following conversation in one concise paragraph. "
    "Capture the user's goal, the important response details, and any "
    "unresolved issue. Do not add facts that are not in the conversation."
)


class GenerationAttemptError(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(
        connect=OPENROUTER_CONNECT_TIMEOUT,
        read=OPENROUTER_READ_TIMEOUT,
        write=30.0,
        pool=5.0,
    )
    headers = {"Content-Type": "application/json"}
    if OPENROUTER_API_KEY:
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"
    app.state.openrouter_client = httpx.AsyncClient(
        base_url=f"{OPENROUTER_BASE_URL.rstrip('/')}/",
        headers=headers,
        timeout=timeout,
    )
    try:
        yield
    finally:
        await app.state.openrouter_client.aclose()


app = FastAPI(title="LLM Service", lifespan=lifespan)


def _error_message(response):
    try:
        body = response.json()
    except ValueError:
        return response.text[:300] or "Unknown OpenRouter error"
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)[:300]
        if error:
            return str(error)[:300]
    return "Unknown OpenRouter error"


def _content_from_choice(choice):
    if not isinstance(choice, dict):
        return None
    message = choice.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    if not isinstance(content, str):
        return None
    return content.replace("<pad>", "").strip()


def _parse_completion(response, payload):
    try:
        body = response.json()
    except ValueError as exc:
        raise GenerationAttemptError(
            502, "OpenRouter returned non-JSON data"
        ) from exc

    choices = body.get("choices") if isinstance(body, dict) else None
    if not isinstance(choices, list) or not choices:
        error = body.get("error") if isinstance(body, dict) else None
        detail = (
            error.get("message")
            if isinstance(error, dict)
            else error or "response contained no choices"
        )
        raise GenerationAttemptError(
            502,
            f"OpenRouter returned no completion: {str(detail)[:300]}",
        )

    choice = choices[0]
    content = _content_from_choice(choice)
    if not content:
        finish_reason = (
            choice.get("finish_reason")
            if isinstance(choice, dict)
            else "unknown"
        )
        raise GenerationAttemptError(
            502,
            "OpenRouter returned an empty completion "
            f"(finish_reason={finish_reason})",
        )

    usage = body.get("usage") or {}
    return GenerateResponse(
        content=content,
        model=body.get("model") or payload["model"],
        usage=TokenUsage(
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
        ),
        finish_reason=choice.get("finish_reason") or "unknown",
    )


async def _attempt_generation(request, payload):
    try:
        response = await request.app.state.openrouter_client.post(
            "chat/completions", json=payload
        )
    except httpx.ReadTimeout as exc:
        raise GenerationAttemptError(
            504, "OpenRouter generation timed out"
        ) from exc
    except httpx.RequestError as exc:
        raise GenerationAttemptError(
            503, "OpenRouter is unreachable"
        ) from exc

    if response.status_code >= 400:
        raise GenerationAttemptError(
            502,
            f"OpenRouter error: {_error_message(response)}",
        )

    return _parse_completion(response, payload)


async def _generate(request: Request, payload):
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured",
        )

    primary_model = payload["model"]
    models = [primary_model]
    if FALLBACK_MODEL and FALLBACK_MODEL != primary_model:
        models.append(FALLBACK_MODEL)

    last_error = None
    for index, model in enumerate(models):
        attempt_payload = {**payload, "model": model}
        try:
            return await _attempt_generation(request, attempt_payload)
        except GenerationAttemptError as exc:
            last_error = exc
        except Exception:
            logger.exception("Unexpected generation failure for %s", model)
            last_error = GenerationAttemptError(
                502, "Unexpected model response"
            )

        if index < len(models) - 1:
            logger.warning(
                "Model %s failed (%s); retrying silently with fallback",
                model,
                last_error.detail,
            )

    raise HTTPException(
        status_code=last_error.status_code,
        detail=f"LLM generation failed after retry: {last_error.detail}",
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(data: GenerateRequest, request: Request):
    payload = {
        "model": data.model or DEFAULT_MODEL,
        "messages": [
            message.model_dump() for message in data.messages
        ],
    }
    if data.temperature is not None:
        payload["temperature"] = data.temperature
    if data.max_tokens is not None:
        payload["max_tokens"] = data.max_tokens
    return await _generate(request, payload)


@app.post("/summarize", response_model=GenerateResponse)
async def summarize(data: SummarizeRequest, request: Request):
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            *[message.model_dump() for message in data.messages],
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }
    return await _generate(request, payload)


@app.get("/models")
async def models(request: Request):
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured",
        )
    try:
        response = await request.app.state.openrouter_client.get("models")
    except httpx.ReadTimeout as exc:
        raise HTTPException(
            status_code=504, detail="OpenRouter request timed out"
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="OpenRouter is unreachable"
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter error: {_error_message(response)}",
        )
    return response.json()


@app.get("/health")
def health():
    return {
        "status": "ready" if OPENROUTER_API_KEY else "not_ready",
        "api_key_configured": bool(OPENROUTER_API_KEY),
        "default_model": DEFAULT_MODEL,
        "fallback_model": FALLBACK_MODEL,
    }
