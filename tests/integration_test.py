"""Live Week 2 integration test.

Start all three services, then run:
    python tests/integration_test.py
"""

import asyncio
import os
from uuid import uuid4

import httpx

PROMPT_URL = os.getenv("PROMPT_SERVICE_URL", "http://localhost:8000")
REVIEW_URL = os.getenv("REVIEW_SERVICE_URL", "http://localhost:8001")
LLM_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")


async def checked(client, method, url, **kwargs):
    response = await client.request(method, url, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(
            f"{method} {url} failed with {response.status_code}: "
            f"{response.text[:500]}"
        )
    return response.json()


async def main():
    timeout = httpx.Timeout(connect=5, read=180, write=30, pool=5)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await checked(client, "GET", f"{PROMPT_URL}/")
        await checked(client, "GET", f"{REVIEW_URL}/")
        llm_health = await checked(client, "GET", f"{LLM_URL}/health")
        if not llm_health["api_key_configured"]:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        prompt = None
        chat = None
        review = None
        try:
            marker = uuid4().hex[:8]
            prompt = await checked(
                client,
                "POST",
                f"{PROMPT_URL}/prompts/",
                json={
                    "name": f"Week 2 integration {marker}",
                    "description": "Temporary end-to-end test prompt",
                    "content": "Reply with exactly two friendly words.",
                    "tags": "integration-test",
                },
            )
            chat = await checked(
                client,
                "POST",
                f"{PROMPT_URL}/prompts/{prompt['id']}/execute",
                json={},
            )
            assert len(chat["messages"]) == 2

            chat = await checked(
                client,
                "POST",
                f"{PROMPT_URL}/chats/{chat['id']}/messages",
                json={"content": "Now reply with one friendly word."},
            )
            assert len(chat["messages"]) == 4

            summary = await checked(
                client,
                "POST",
                f"{PROMPT_URL}/chats/{chat['id']}/summary",
            )
            assert summary["summary"]

            review = await checked(
                client,
                "POST",
                f"{REVIEW_URL}/reviews/",
                json={
                    "target_type": "chat",
                    "chat_id": chat["id"],
                    "reviewer_name": "Integration Test",
                    "score": 5,
                    "feedback": "End-to-end flow completed.",
                },
            )
            assert review["snapshot"]["id"] == chat["id"]
            print("PASS: create → execute → chat → summarize → review")
        finally:
            if review:
                await client.delete(f"{REVIEW_URL}/reviews/{review['id']}")
            if chat:
                await client.delete(f"{PROMPT_URL}/chats/{chat['id']}")
            if prompt:
                await client.delete(f"{PROMPT_URL}/prompts/{prompt['id']}")


if __name__ == "__main__":
    asyncio.run(main())
