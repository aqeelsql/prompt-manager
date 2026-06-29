const PROMPT_API = "/api/prompts";
const REVIEW_API = "/api/reviews";

export async function getPrompts() {
  const response = await fetch(`${PROMPT_API}/`);
  return response.json();
}


export async function getPromptById(id) {
  const response = await fetch(
    `${PROMPT_API}/${id}`
  );

  return response.json();
}

export async function checkPromptExists(id) {
  const response = await fetch(
    `${PROMPT_API}/${id}/exists`
  );

  return response.json();
}

export async function createPrompt(data) {
  const response = await fetch(`${PROMPT_API}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return response.json();
}

export async function updatePrompt(id, data) {
  const response = await fetch(`${PROMPT_API}/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return response.json();
}

export async function deletePrompt(id) {
  const response = await fetch(`${PROMPT_API}/${id}`, {
    method: "DELETE"
  });

  return response.json();
}

export async function getReviews() {
  const response = await fetch(`${REVIEW_API}/`);
  return response.json();
}

export async function createReview(data) {
  const response = await fetch(`${REVIEW_API}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return response.json();
}

export async function getReviewSummary(promptId) {
  const response = await fetch(
    `${REVIEW_API}/${promptId}/summary`
  );

  return response.json();
}

export async function getReviewById(id) {
  const response = await fetch(
    `${REVIEW_API}/${id}`
  );

  return response.json();
}