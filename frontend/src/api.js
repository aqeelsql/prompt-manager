const PROMPT_API = "/api/prompts";
const CHAT_API = "/api/chats";
const REVIEW_API = "/api/reviews";
const DOCUMENT_API = "/api/documents";

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function jsonOptions(method, data) {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  };
}

export function getPrompts() {
  return request(`${PROMPT_API}/`);
}

export function createPrompt(data) {
  return request(`${PROMPT_API}/`, jsonOptions("POST", data));
}

export function updatePrompt(id, data) {
  return request(`${PROMPT_API}/${id}`, jsonOptions("PUT", data));
}

export function deletePrompt(id) {
  return request(`${PROMPT_API}/${id}`, { method: "DELETE" });
}

export function executePrompt(id) {
  return request(
    `${PROMPT_API}/${id}/execute`,
    jsonOptions("POST", {})
  );
}

export function createDocumentChat(documentId, content) {
  return request(
    "/api/document-chats",
    jsonOptions("POST", {
      content,
      ...(documentId ? { document_id: documentId } : {})
    })
  );
}
export function getChats(promptId = null) {
  const query = promptId
    ? `?prompt_id=${encodeURIComponent(promptId)}`
    : "";
  return request(`${CHAT_API}${query}`);
}

export function getChat(id) {
  return request(`${CHAT_API}/${id}`);
}

export function sendChatMessage(id, content, documentId = null) {
  return request(
    `${CHAT_API}/${id}/messages`,
    jsonOptions("POST", {
      content,
      ...(documentId ? { document_id: documentId } : {})
    })
  );
}

export function summarizeChat(id) {
  return request(`${CHAT_API}/${id}/summary`, { method: "POST" });
}

export function deleteChat(id) {
  return request(`${CHAT_API}/${id}`, { method: "DELETE" });
}

export function uploadDocument(file) {
  const data = new FormData();
  data.append("file", file);
  return request(DOCUMENT_API, { method: "POST", body: data });
}

export function getReviews(filters = {}) {
  const params = new URLSearchParams();
  if (filters.promptId) params.set("prompt_id", filters.promptId);
  if (filters.chatId) params.set("chat_id", filters.chatId);
  const query = params.toString() ? `?${params}` : "";
  return request(`${REVIEW_API}/${query}`);
}

export function createReview(data) {
  return request(`${REVIEW_API}/`, jsonOptions("POST", data));
}
