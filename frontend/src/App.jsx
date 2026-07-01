import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import {
  createDocumentChat,
  createPrompt,
  createReview,
  deleteChat,
  deletePrompt,
  executePrompt,
  getChat,
  getChats,
  getPrompts,
  getReviews,
  sendChatMessage,
  summarizeChat,
  updatePrompt,
  uploadDocument
} from "./api";

const EMPTY_PROMPT = {
  name: "",
  description: "",
  content: ""
};

const EMPTY_REVIEW = {
  target_type: "prompt",
  target_id: "",
  reviewer_name: "",
  score: 5,
  feedback: ""
};

function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function FormattedContent({ content }) {
  return (
    <div className="formatted-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer" />
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function MessageAttachments({ attachments = [] }) {
  if (!attachments.length) return null;

  return (
    <div className="message-attachments">
      {attachments.map((attachment, index) => {
        const fileType = (
          attachment.file_type || attachment.filename?.split(".").pop() || "file"
        ).toUpperCase();
        return (
          <div className="message-file-card" key={attachment.id || `${attachment.filename}-${index}`}>
            <span className="message-file-icon">{fileType === "PDF" ? "PDF" : "DOC"}</span>
            <span className="message-file-copy">
              <strong>{attachment.filename || "Attached document"}</strong>
              <small>
                {fileType}
                {attachment.character_count
                  ? ` · ${Number(attachment.character_count).toLocaleString()} characters`
                  : ""}
              </small>
            </span>
          </div>
        );
      })}
    </div>
  );
}

function ReviewSnapshot({ review }) {
  const snapshot = review.snapshot ?? review.prompt_snapshot ?? "";

  if (review.target_type === "chat" && snapshot && typeof snapshot === "object") {
    const messages = Array.isArray(snapshot.messages) ? snapshot.messages : [];
    const fullPrompt = messages.find((message) => message.role === "user")?.content || "";

    return (
      <div className="review-snapshot">
        <section className="review-snapshot-section">
          <span className="kicker">Full prompt</span>
          <p className="review-snapshot-text">
            {fullPrompt || "No prompt was stored with this review."}
          </p>
        </section>
        {messages.length > 1 && (
          <section className="review-snapshot-section">
            <span className="kicker">Full conversation</span>
            <div className="review-conversation">
              {messages.map((message, index) => (
                <div className="review-snapshot-message" key={message.id || index}>
                  <strong>{message.role === "assistant" ? "Assistant" : "User"}</strong>
                  <FormattedContent content={message.content} />
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    );
  }

  const fullPrompt = typeof snapshot === "string" ? snapshot : JSON.stringify(snapshot, null, 2);

  return (
    <section className="review-snapshot-section">
      <span className="kicker">Full prompt</span>
      <p className="review-snapshot-text">
        {fullPrompt || "No prompt was stored with this review."}
      </p>
    </section>
  );
}

function App() {
  const [prompts, setPrompts] = useState([]);
  const [chats, setChats] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [promptForm, setPromptForm] = useState(EMPTY_PROMPT);
  const [editingId, setEditingId] = useState(null);
  const [reviewForm, setReviewForm] = useState(EMPTY_REVIEW);
  const [followUp, setFollowUp] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeView, setActiveView] = useState("chat");
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);
  const [selectedReview, setSelectedReview] = useState(null);
  const [attachedDocument, setAttachedDocument] = useState(null);
  const [documentBusy, setDocumentBusy] = useState(false);

  async function refreshLists() {
    const [promptData, chatData, reviewData] = await Promise.all([
      getPrompts(),
      getChats(),
      getReviews()
    ]);
    setPrompts(promptData);
    setChats(chatData);
    setReviews(reviewData);
  }

  useEffect(() => {
    refreshLists().catch((err) => setError(err.message));
  }, []);

  async function runAction(key, action, successMessage = "") {
    setBusy(key);
    setError("");
    setNotice("");
    try {
      const result = await action();
      if (successMessage) setNotice(successMessage);
      return result;
    } catch (err) {
      setError(err.message);
      const failedChatId = err.data?.detail?.chat_id;
      if (failedChatId) {
        getChat(failedChatId).then(setActiveChat).catch(() => {});
        refreshLists().catch(() => {});
      }
      return null;
    } finally {
      setBusy("");
    }
  }

  async function handleSavePrompt(event) {
    event.preventDefault();
    const saved = await runAction(
      "prompt",
      () => (editingId ? updatePrompt(editingId, promptForm) : createPrompt(promptForm)),
      editingId ? "Prompt updated." : "Prompt created."
    );
    if (!saved) return;
    setPromptForm(EMPTY_PROMPT);
    setEditingId(null);
    setIsPromptModalOpen(false);
    await refreshLists();
  }

  async function handleExecute(prompt) {
    const chat = await runAction(
      `execute-${prompt.id}`,
      () => executePrompt(prompt.id),
      "Prompt executed. The conversation is ready."
    );
    if (!chat) return;
    setActiveChat(chat);
    setAttachedDocument(null);
    await refreshLists();
  }

  async function handleOpenChat(chatId) {
    const chat = await runAction(`open-${chatId}`, () => getChat(chatId));
    if (chat) {
      setActiveChat(chat);
      setAttachedDocument(null);
    }
  }

  function handleNewChat() {
    setActiveChat(null);
    setAttachedDocument(null);
    setFollowUp("");
    setError("");
    setNotice("");
  }

  async function handleDocumentUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx"].includes(extension)) {
      setError("Only PDF and DOCX documents are supported.");
      return;
    }

    setDocumentBusy(true);
    setError("");
    setNotice("");
    try {
      const document = await uploadDocument(file);
      setAttachedDocument({
        id: document.id,
        filename: document.filename,
        character_count: document.character_count
      });
      setNotice("Document attached. Its text will be used as model context.");
    } catch (err) {
      setError(err.message);
    } finally {
      setDocumentBusy(false);
    }
  }

  async function handleFollowUp(event) {
    event.preventDefault();
    const content = followUp.trim();
    if (!content) return;
    setFollowUp("");
    const chat = await runAction(
      activeChat ? "follow-up" : "document-chat",
      () =>
        activeChat
          ? sendChatMessage(activeChat.id, content, attachedDocument?.id)
          : createDocumentChat(attachedDocument?.id, content),
      activeChat ? "Reply added." : "Chat started."
    );
    if (!chat) return;
    setActiveChat(chat);
    setAttachedDocument(null);
    await refreshLists();
  }

  async function handleSummarize() {
    if (!activeChat) return;
    const result = await runAction(
      "summary",
      () => summarizeChat(activeChat.id),
      "Summary refreshed."
    );
    if (!result) return;
    setActiveChat((chat) => ({ ...chat, summary: result.summary }));
    await refreshLists();
  }

  async function handleDeleteChat() {
    if (!activeChat || !window.confirm("Delete this chat and its messages?")) return;
    const result = await runAction(
      "delete-chat",
      () => deleteChat(activeChat.id),
      "Chat deleted."
    );
    if (!result) return;
    setActiveChat(null);
    setAttachedDocument(null);
    await refreshLists();
  }

  async function handleDeleteHistoryChat(chatId) {
    if (!window.confirm("Delete this chat and its messages?")) return;
    const result = await runAction(
      `delete-history-${chatId}`,
      () => deleteChat(chatId),
      "Chat deleted."
    );
    if (!result) return;
    if (activeChat?.id === chatId) {
      setActiveChat(null);
      setAttachedDocument(null);
    }
    await refreshLists();
  }
  async function handleDeletePrompt(promptId) {
    if (!window.confirm("Delete this prompt and all of its chats?")) return;
    const result = await runAction(
      `delete-${promptId}`,
      () => deletePrompt(promptId),
      "Prompt deleted."
    );
    if (!result) return;
    if (activeChat?.prompt_id === promptId) setActiveChat(null);
    await refreshLists();
  }

  async function handleReview(event) {
    event.preventDefault();
    if (!reviewForm.target_id) {
      setError("Choose a prompt or chat to review.");
      return;
    }
    const payload = {
      target_type: reviewForm.target_type,
      reviewer_name: reviewForm.reviewer_name,
      score: Number(reviewForm.score),
      feedback: reviewForm.feedback,
      [reviewForm.target_type === "chat" ? "chat_id" : "prompt_id"]: reviewForm.target_id
    };
    const review = await runAction(
      "review",
      () => createReview(payload),
      "Review saved with a frozen snapshot."
    );
    if (!review) return;
    setReviewForm(EMPTY_REVIEW);
    await refreshLists();
  }

  const reviewTargets = reviewForm.target_type === "chat" ? chats : prompts;

  return (
    <div className={`app-shell ${activeView === "chat" ? "chat-mode" : ""}` }>
      <header className="hero">
        <div className="brand">
          <span className="brand-mark">P</span>
          <h1>Prompt Manager</h1>
        </div>

        <nav className="main-nav" aria-label="Main navigation">
          <button
            className={`nav-item ${activeView === "chat" ? "active" : ""}`}
            onClick={() => setActiveView("chat")}
          >
            Chat
          </button>
          <button
            className={`nav-item ${activeView === "workspace" ? "active" : ""}`}
            onClick={() => setActiveView("workspace")}
          >
            Workspace
          </button>
          <button
            className={`nav-item ${activeView === "reviews" ? "active" : ""}`}
            onClick={() => setActiveView("reviews")}
          >
            Reviews
            <span className="nav-count">{reviews.length}</span>
          </button>
        </nav>
      </header>

      {(error || notice) && (
        <div className={`alert ${error ? "alert-error" : "alert-success"}`}>
          {error || notice}
        </div>
      )}

      <main className={`workspace show-${activeView}`}>
        <aside className="sidebar">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="kicker">Library</span>
                <h2>Prompts</h2>
              </div>
              <div className="panel-actions">
                <span className="count">{prompts.length}</span>
                <button
                  type="button"
                  className="button primary new-prompt-button"
                  onClick={() => {
                    setEditingId(null);
                    setPromptForm(EMPTY_PROMPT);
                    setIsPromptModalOpen(true);
                  }}
                >
                  + New prompt
                </button>
              </div>
            </div>

            {isPromptModalOpen && (
              <div
                className="modal-backdrop"
                onMouseDown={(event) => {
                  if (event.target === event.currentTarget) setIsPromptModalOpen(false);
                }}
              >
                <section className="modal-card" aria-modal="true" role="dialog">
                  <div className="modal-header">
                    <div>
                      <span className="kicker">Prompt details</span>
                      <h2>{editingId ? "Edit prompt" : "Create prompt"}</h2>
                    </div>
                    <button
                      type="button"
                      className="modal-close"
                      aria-label="Close prompt form"
                      onClick={() => {
                        setEditingId(null);
                        setPromptForm(EMPTY_PROMPT);
                        setIsPromptModalOpen(false);
                      }}
                    >
                      ×
                    </button>
                  </div>
                  <form className="stack prompt-form" onSubmit={handleSavePrompt}>
                    <input
                      placeholder="Prompt name"
                      value={promptForm.name}
                      onChange={(e) => setPromptForm({ ...promptForm, name: e.target.value })}
                      required
                    />
                    <input
                      placeholder="Description"
                      value={promptForm.description}
                      onChange={(e) => setPromptForm({ ...promptForm, description: e.target.value })}
                    />
                    <textarea
                      placeholder="What should the model do?"
                      value={promptForm.content}
                      onChange={(e) => setPromptForm({ ...promptForm, content: e.target.value })}
                      required
                    />
                    <div className="button-row">
                      <button className="button primary" disabled={busy === "prompt"}>
                        {busy === "prompt" ? "Saving…" : editingId ? "Update prompt" : "Create prompt"}
                      </button>
                      {editingId && (
                        <button
                          className="button ghost"
                          type="button"
                          onClick={() => {
                            setEditingId(null);
                            setPromptForm(EMPTY_PROMPT);
                            setIsPromptModalOpen(false);
                          }}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </form>
                </section>
              </div>
            )}

            <div className="prompt-list">
              {prompts.map((prompt) => (
                <article className="prompt-card" key={prompt.id}>
                  <div className="prompt-title">
                    <div>
                      <h3>{prompt.name}</h3>
                      <p>{prompt.description || "No description"}</p>
                    </div>
                  </div>
                  <p className="prompt-copy">{prompt.content}</p>
                  <div className="button-row compact">
                    <button
                      className="button primary"
                      disabled={busy === `execute-${prompt.id}`}
                      onClick={() => handleExecute(prompt)}
                    >
                      {busy === `execute-${prompt.id}` ? "Running…" : "Execute"}
                    </button>
                    <button
                      className="button ghost"
                      onClick={() => {
                        setEditingId(prompt.id);
                        setIsPromptModalOpen(true);
                        setPromptForm({
                          name: prompt.name,
                          description: prompt.description || "",
                          content: prompt.content
                        });
                      }}
                    >
                      Edit
                    </button>
                    <button className="button danger-text" onClick={() => handleDeletePrompt(prompt.id)}>
                      Delete
                    </button>
                  </div>
                </article>
              ))}
              {!prompts.length && <p className="empty">Create your first prompt to begin.</p>}
            </div>
          </section>
        </aside>

        <section className="main-column">
          <section className="panel conversation-panel">
            <div className="panel-heading chat-heading">
              <div>
                <span className="kicker">Conversation</span>
                <h2>{activeChat?.title || "Select a chat"}</h2>
                {activeChat && <p>Updated {formatDate(activeChat.updated_at)}</p>}
              </div>
              {activeChat && (
                <div className="token-total">
                  <strong>{activeChat.total_tokens}</strong>
                  <span>total tokens</span>
                </div>
              )}
            </div>

            <div className="chat-tabs">
              {chats.map((chat) => (
                <button
                  className={activeChat?.id === chat.id ? "active" : ""}
                  key={chat.id}
                  onClick={() => handleOpenChat(chat.id)}
                >
                  <span>{chat.title}</span>
                  <small>{chat.total_tokens} tokens</small>
                </button>
              ))}
              {!chats.length && <p className="empty">Executed prompts will appear here.</p>}
            </div>

            {activeChat ? (
              <>
                <div className="messages">
                  {activeChat.messages?.map((message) => (
                    <article className={`message ${message.role}`} key={message.id}>
                      <div className="message-meta">
                        <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                        <span>{formatDate(message.created_at)}</span>
                      </div>
                      <MessageAttachments attachments={message.attachments} />
                      <FormattedContent content={message.content} />
                      {message.role === "assistant" && (
                        <div className="usage">
                          <span>Prompt {message.prompt_tokens}</span>
                          <span>Completion {message.completion_tokens}</span>
                          <span>Total {message.total_tokens}</span>
                        </div>
                      )}
                    </article>
                  ))}
                  {busy === "follow-up" && (
                    <article className="message assistant typing">
                      <span />
                      <span />
                      <span />
                    </article>
                  )}
                </div>

                {activeChat.summary && (
                  <div className="summary-card">
                    <span className="kicker">Conversation summary</span>
                    <p>{activeChat.summary}</p>
                  </div>
                )}
              </>
            ) : (
              <div className="messages chat-messages empty-thread">
                <div className="chat-empty-stage">
                  <div className="chat-start-copy">
                    <div className="empty-icon">AI</div>
                    <div>
                      <h3>Start a new conversation</h3>

                    </div>
                  </div>
                </div>
              </div>
            )}

            <form className="composer chat-composer" onSubmit={handleFollowUp}>
              {attachedDocument && (
                <div className="document-chip chat-document-chip">
                  <span>
                    <strong>{attachedDocument.filename}</strong>
                    <small>{attachedDocument.character_count.toLocaleString()} extracted characters</small>
                  </span>
                  <button type="button" aria-label="Remove attached document" onClick={() => setAttachedDocument(null)}>
                    ×
                  </button>
                </div>
              )}

              <textarea
                className="chat-input"
                placeholder={activeChat ? "Message the assistant…" : "Start a conversation…"}
                value={followUp}
                onChange={(event) => setFollowUp(event.target.value)}
                required
              />

              <div className="composer-actions">
                <div className="button-row compact">
                  <label className="button ghost document-upload chat-attach-button">
                    <input
                      type="file"
                      accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={handleDocumentUpload}
                      disabled={documentBusy || busy === "follow-up" || busy === "document-chat"}
                    />
                    {documentBusy ? "Attaching…" : "Attach file"}
                  </label>
                  {activeChat && (
                    <button type="button" className="button ghost" disabled={busy === "summary"} onClick={handleSummarize}>
                      {busy === "summary" ? "Summarizing…" : "Summarize"}
                    </button>
                  )}
                  {activeChat && (
                    <button type="button" className="button danger-text" onClick={handleDeleteChat}>
                      Delete chat
                    </button>
                  )}
                </div>
                <button className="button primary" disabled={busy === "follow-up" || busy === "document-chat"}>
                  {busy === "follow-up" || busy === "document-chat" ? "Thinking…" : activeChat ? "Send" : "Start chat"}
                </button>
              </div>
            </form>
          </section>

          <section className="review-grid">
            <div className="panel">
              <span className="kicker">Evaluation</span>
              <h2>Create review</h2>
              <form className="stack" onSubmit={handleReview}>
                <div className="segmented">
                  {["prompt", "chat"].map((type) => (
                    <button
                      type="button"
                      className={reviewForm.target_type === type ? "active" : ""}
                      key={type}
                      onClick={() => setReviewForm({ ...reviewForm, target_type: type, target_id: "" })}
                    >
                      {type}
                    </button>
                  ))}
                </div>
                <select
                  value={reviewForm.target_id}
                  onChange={(e) => setReviewForm({ ...reviewForm, target_id: e.target.value })}
                  required
                >
                  <option value="">Choose {reviewForm.target_type}</option>
                  {reviewTargets.map((target) => (
                    <option value={target.id} key={target.id}>
                      {target.name || target.title}
                    </option>
                  ))}
                </select>
                <input
                  placeholder="Reviewer name"
                  value={reviewForm.reviewer_name}
                  onChange={(e) => setReviewForm({ ...reviewForm, reviewer_name: e.target.value })}
                  required
                />
                <label className="score-field">
                  <span>Score</span>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={reviewForm.score}
                    onChange={(e) => setReviewForm({ ...reviewForm, score: e.target.value })}
                  />
                  <strong>{reviewForm.score}/5</strong>
                </label>
                <textarea
                  placeholder="Specific, useful feedback"
                  value={reviewForm.feedback}
                  onChange={(e) => setReviewForm({ ...reviewForm, feedback: e.target.value })}
                  required
                />
                <button className="button primary" disabled={busy === "review"}>
                  {busy === "review" ? "Saving…" : "Save review"}
                </button>
              </form>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <div>
                  <span className="kicker">History</span>
                  <h2>Reviews</h2>
                </div>
                <span className="count">{reviews.length}</span>
              </div>
              <div className="review-list">
                {reviews.map((review) => (
                  <button
                    type="button"
                    className={`review-card ${selectedReview?.id === review.id ? "active" : ""}`}
                    key={review.id}
                    onClick={() => setSelectedReview(review)}
                  >
                    <div>
                      <span className="tag">{review.target_type}</span>
                      <strong>{review.reviewer_name}</strong>
                    </div>
                    <span className="score">{review.score}/5</span>
                    <p>{review.feedback}</p>
                    <small>{formatDate(review.reviewed_at)}</small>
                  </button>
                ))}
                {!reviews.length && <p className="empty">No reviews submitted yet.</p>}
              </div>
            </div>
          </section>

          {selectedReview && (
            <div
              className="modal-backdrop"
              onMouseDown={(event) => {
                if (event.target === event.currentTarget) setSelectedReview(null);
              }}
            >
              <section className="modal-card review-detail-modal" aria-modal="true" role="dialog">
                <div className="modal-header">
                  <div>
                    <span className="kicker">Review details</span>
                    <h2>{selectedReview.reviewer_name}</h2>
                  </div>
                  <button
                    type="button"
                    className="modal-close"
                    aria-label="Close review details"
                    onClick={() => setSelectedReview(null)}
                  >
                    ×
                  </button>
                </div>
                <div className="review-detail-summary">
                  <span className="tag">{selectedReview.target_type}</span>
                  <strong>{selectedReview.score}/5</strong>
                  <p>{selectedReview.feedback}</p>
                  <small>{formatDate(selectedReview.reviewed_at)}</small>
                </div>
                <ReviewSnapshot review={selectedReview} />
              </section>
            </div>
          )}
        </section>

        <section className="chat-view">
          <aside className="panel chat-history-panel">
            <div className="panel-heading">
              <div>
                <span className="kicker">Chats</span>
                <h2>History</h2>
              </div>
              <div className="panel-actions">
                <span className="count">{chats.length}</span>
                <button type="button" className="button primary new-chat-button" onClick={handleNewChat}>
                  + New chat
                </button>
              </div>
            </div>

            <div className="chat-history-list">
              {chats.map((chat) => (
                <div
                  className={`chat-history-item ${activeChat?.id === chat.id ? "active" : ""}`}
                  key={chat.id}
                >
                  <button
                    type="button"
                    className="chat-history-open"
                    onClick={() => handleOpenChat(chat.id)}
                  >
                    <strong>{chat.title}</strong>
                    <p>{chat.summary || "General chat"}</p>
                    <small>{chat.total_tokens} tokens · {formatDate(chat.updated_at)}</small>
                  </button>
                  <button
                    type="button"
                    className="chat-history-delete"
                    aria-label={`Delete ${chat.title}`}
                    disabled={busy === `delete-history-${chat.id}`}
                    onClick={() => handleDeleteHistoryChat(chat.id)}
                  >
                    ×
                  </button>
                </div>
              ))}
              {!chats.length && <p className="empty">Your chats will appear here.</p>}
            </div>
          </aside>

          <section className="panel chat-panel">
            <div className="panel-heading chat-heading">
              <div>
                <span className="kicker">Conversation</span>
                <h2>{activeChat?.title || "Start a new chat"}</h2>
                <p>
                  {activeChat
                    ? `Updated ${formatDate(activeChat.updated_at)}`
                    : "Ask anything. Attach a PDF or DOCX only when you need file context."}
                </p>
              </div>
              {activeChat && (
                <div className="token-total">
                  <strong>{activeChat.total_tokens}</strong>
                  <span>total tokens</span>
                </div>
              )}
            </div>


            <div className={`messages chat-messages ${activeChat?.messages?.length ? "has-history" : "empty-thread"}`}>
              {activeChat?.messages?.length ? (
                activeChat.messages.map((message) => (
                  <article className={`message ${message.role}`} key={message.id}>
                    <div className="message-meta">
                      <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                      <span>{formatDate(message.created_at)}</span>
                    </div>
                    <MessageAttachments attachments={message.attachments} />
                    <FormattedContent content={message.content} />
                    {message.role === "assistant" && (
                      <div className="usage">
                        <span>Prompt {message.prompt_tokens}</span>
                        <span>Completion {message.completion_tokens}</span>
                        <span>Total {message.total_tokens}</span>
                      </div>
                    )}
                  </article>
                ))
              ) : (
                <div className="chat-empty-stage">
                  <div className="chat-start-copy">
                    <div className="empty-icon">AI</div>
                    <div>
                      <h3>Start a new conversation</h3>

                    </div>
                  </div>
                </div>
              )}
              {busy === "follow-up" && (
                <article className="message assistant typing">
                  <span />
                  <span />
                  <span />
                </article>
              )}
            </div>

            <form className="composer chat-composer" onSubmit={handleFollowUp}>
              {attachedDocument && (
                <div className="document-chip chat-document-chip">
                  <span>
                    <strong>{attachedDocument.filename}</strong>
                    <small>{attachedDocument.character_count.toLocaleString()} extracted characters</small>
                  </span>
                  <button type="button" aria-label="Remove attached document" onClick={() => setAttachedDocument(null)}>
                    ×
                  </button>
                </div>
              )}

              <textarea
                className="chat-input"
                placeholder={activeChat ? "Message the assistant…" : "Start a conversation…"}
                value={followUp}
                onChange={(event) => setFollowUp(event.target.value)}
                required
              />

              <div className="composer-actions">
                <div className="button-row compact">
                  <label className="button ghost document-upload chat-attach-button">
                    <input
                      type="file"
                      accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={handleDocumentUpload}
                      disabled={documentBusy || busy === "follow-up" || busy === "document-chat"}
                    />
                    {documentBusy ? "Attaching…" : "Attach file"}
                  </label>
                  {activeChat && (
                    <button type="button" className="button ghost" disabled={busy === "summary"} onClick={handleSummarize}>
                      {busy === "summary" ? "Summarizing…" : "Summarize"}
                    </button>
                  )}
                  {activeChat && (
                    <button type="button" className="button danger-text" onClick={handleDeleteChat}>
                      Delete chat
                    </button>
                  )}
                </div>
                <button className="button primary" disabled={busy === "follow-up" || busy === "document-chat"}>
                  {busy === "follow-up" || busy === "document-chat" ? "Thinking…" : activeChat ? "Send" : "Start chat"}
                </button>
              </div>
            </form>
          </section>
        </section>
      </main>
    </div>
  );
}

export default App;
