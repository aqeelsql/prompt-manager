import { useEffect, useState } from "react";

import {
  getPrompts,
  getPromptById,
  checkPromptExists,
  createPrompt,
  updatePrompt,
  deletePrompt,
  getReviews,
  getReviewById,
  createReview,
  getReviewSummary
} from "./api";

function App() {
  const [prompts, setPrompts] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [summary, setSummary] = useState(null);

  const [editingId, setEditingId] = useState(null);
  const [promptSearchId, setPromptSearchId] = useState("");
  const [reviewSearchId, setReviewSearchId] = useState("");

  const [existsResult, setExistsResult] = useState(null);
  const [singlePrompt, setSinglePrompt] = useState(null);
  const [singleReview, setSingleReview] = useState(null);
  const [reviewLookupError, setReviewLookupError] = useState("");

  const [promptForm, setPromptForm] = useState({
    name: "",
    description: "",
    content: "",
    tags: "",
    model_target: ""
  });

  const [reviewForm, setReviewForm] = useState({
    prompt_id: "",
    reviewer_name: "",
    score: 1,
    feedback: ""
  });

  async function loadData() {
    const promptData = await getPrompts();
    const reviewData = await getReviews();

    setPrompts(promptData);
    setReviews(reviewData);
  }

  useEffect(() => {
    loadData();
  }, []);


  async function handleGetPromptById() {
    if (!promptSearchId.trim()) return;

    const data = await getPromptById(
      promptSearchId
    );

    setSinglePrompt(data);
  }

  async function handleExistsCheck() {
    if (!promptSearchId.trim()) return;

    const data = await checkPromptExists(
      promptSearchId
    );

    setExistsResult(data.exists);
  }

  async function handleGetReviewById() {
    const id = reviewSearchId.trim();

    if (!id) return;

    try {
      const data = await getReviewById(id);

      if (data.detail) {
        setSingleReview(null);
        setReviewLookupError(data.detail);
        return;
      }

      setSingleReview(data);
      setReviewLookupError("");
    } catch {
      setSingleReview(null);
      setReviewLookupError("Unable to fetch review.");
    }
  }

  async function handleSavePrompt(e) {
    e.preventDefault();

    if (editingId) {
      await updatePrompt(
        editingId,
        promptForm
      );
    } else {
      await createPrompt(promptForm);
    }

    setEditingId(null);

    setPromptForm({
      name: "",
      description: "",
      content: "",
      tags: "",
      model_target: ""
    });

    loadData();
  }

  async function handleDeletePrompt(id) {
    await deletePrompt(id);
    loadData();
  }

  async function handleCreateReview(e) {
    e.preventDefault();

    await createReview({
      prompt_id: reviewForm.prompt_id,
      reviewer_name: reviewForm.reviewer_name,
      score: Number(reviewForm.score),
      feedback: reviewForm.feedback
    });

    setReviewForm({
      prompt_id: "",
      reviewer_name: "",
      score: 1,
      feedback: ""
    });

    loadData();
  }

  async function handleSummary(promptId) {
    const data = await getReviewSummary(
      promptId
    );

    setSummary(data);
  }

  return (
    <div className="container">
      <h1>Prompt Manager System</h1>

      <div className="grid">
        <section className="box">
          <h2>
            {editingId
              ? "Update Prompt"
              : "Create Prompt"}
          </h2>

          <form onSubmit={handleSavePrompt}>
            <input
              placeholder="Prompt Name"
              value={promptForm.name}
              onChange={(e) =>
                setPromptForm({
                  ...promptForm,
                  name: e.target.value
                })
              }
              required
            />

            <input
              placeholder="Description"
              value={promptForm.description}
              onChange={(e) =>
                setPromptForm({
                  ...promptForm,
                  description: e.target.value
                })
              }
            />

            <textarea
              placeholder="Prompt Content"
              value={promptForm.content}
              onChange={(e) =>
                setPromptForm({
                  ...promptForm,
                  content: e.target.value
                })
              }
              required
            />

            <input
              placeholder="Tags"
              value={promptForm.tags}
              onChange={(e) =>
                setPromptForm({
                  ...promptForm,
                  tags: e.target.value
                })
              }
            />

            <input
              placeholder="Model Target"
              value={promptForm.model_target}
              onChange={(e) =>
                setPromptForm({
                  ...promptForm,
                  model_target: e.target.value
                })
              }
            />

            <button type="submit">
              {editingId
                ? "Update Prompt"
                : "Create Prompt"}
            </button>

            {editingId && (
              <button
                type="button"
                onClick={() => {
                  setEditingId(null);

                  setPromptForm({
                    name: "",
                    description: "",
                    content: "",
                    tags: "",
                    model_target: ""
                  });
                }}
              >
                Cancel
              </button>
            )}
          </form>
        </section>

        <section className="box">
          <h2>Create Review</h2>

          <form onSubmit={handleCreateReview}>
            <input
              placeholder="Prompt UUID"
              value={reviewForm.prompt_id}
              onChange={(e) =>
                setReviewForm({
                  ...reviewForm,
                  prompt_id: e.target.value
                })
              }
              required
            />

            <input
              placeholder="Reviewer Name"
              value={reviewForm.reviewer_name}
              onChange={(e) =>
                setReviewForm({
                  ...reviewForm,
                  reviewer_name: e.target.value
                })
              }
              required
            />

            <input
              type="number"
              min="1"
              max="5"
              value={reviewForm.score}
              onChange={(e) =>
                setReviewForm({
                  ...reviewForm,
                  score: e.target.value
                })
              }
            />

            <textarea
              placeholder="Feedback"
              value={reviewForm.feedback}
              onChange={(e) =>
                setReviewForm({
                  ...reviewForm,
                  feedback: e.target.value
                })
              }
            />

            <button>Create Review</button>
          </form>
        </section>
      </div>


      <section className="box">
        <h2>Prompt Lookup</h2>

        <input
          placeholder="Enter Prompt UUID"
          value={promptSearchId}
          onChange={(e) =>
            setPromptSearchId(e.target.value)
          }
        />

        <button
          onClick={handleGetPromptById}
        >
          Get Prompt
        </button>

        <button
          onClick={handleExistsCheck}
        >
          Exists?
        </button>

        {existsResult !== null && (
          <p>
            <strong>Exists:</strong>{" "}
            {existsResult
              ? "True"
              : "False"}
          </p>
        )}

        {singlePrompt && (
          <div className="card">
            <h3>{singlePrompt.name}</h3>
            <p>{singlePrompt.content}</p>
          </div>
        )}
      </section>

      <section className="box">
        <h2>Review Lookup</h2>

        <input
          placeholder="Enter Review UUID"
          value={reviewSearchId}
          onChange={(e) =>
            setReviewSearchId(e.target.value)
          }
        />

        <button
          onClick={handleGetReviewById}
        >
          Get Review
        </button>

        {reviewLookupError && (
          <p>
            <strong>Error:</strong>{" "}
            {reviewLookupError}
          </p>
        )}

        {singleReview && (
          <div className="card">
            <h3>
              {singleReview.reviewer_name}
            </h3>

            <p>
              <strong>Review ID:</strong>{" "}
              {singleReview.id}
            </p>

            <p>
              <strong>Prompt ID:</strong>{" "}
              {singleReview.prompt_id}
            </p>

            <p>
              <strong>Score:</strong>{" "}
              {singleReview.score}
            </p>

            <p>
              <strong>Feedback:</strong>{" "}
              {singleReview.feedback}
            </p>

            <p>
              <strong>Snapshot:</strong>
            </p>

            <p>{singleReview.prompt_snapshot}</p>

            {singleReview.reviewed_at && (
              <p>
                <strong>Reviewed At:</strong>{" "}
                {singleReview.reviewed_at}
              </p>
            )}
          </div>
        )}
      </section>

      <section className="box">
        <h2>Prompts</h2>

        {prompts.map((prompt) => (
          <div
            className="card"
            key={prompt.id}
          >
            <h3>{prompt.name}</h3>

            <p>
              <strong>ID:</strong>{" "}
              {prompt.id}
            </p>

            <p>{prompt.description}</p>

            <p>{prompt.content}</p>

            <p>
              <strong>Tags:</strong>{" "}
              {prompt.tags}
            </p>

            <button
              onClick={() => {
                setEditingId(prompt.id);

                setPromptForm({
                  name: prompt.name,
                  description:
                    prompt.description || "",
                  content: prompt.content,
                  tags: prompt.tags || "",
                  model_target:
                    prompt.model_target || ""
                });
              }}
            >
              Edit
            </button>

            <button
              onClick={() =>
                handleDeletePrompt(prompt.id)
              }
            >
              Delete
            </button>

            <button
              onClick={() =>
                handleSummary(prompt.id)
              }
            >
              Summary
            </button>
          </div>
        ))}
      </section>

      {summary && (
        <section className="box">
          <h2>Review Summary</h2>

          <p>
            Average Score:
            {summary.average_score}
          </p>

          <p>
            Total Reviews:
            {summary.total_reviews}
          </p>

          <ul>
            {summary.feedback?.map(
              (item, index) => (
                <li key={index}>{item}</li>
              )
            )}
          </ul>
        </section>
      )}

      <section className="box">
        <h2>Reviews</h2>

        {reviews.map((review) => (
          <div
            className="card"
            key={review.id}
          >
            <h3>
              {review.reviewer_name}
            </h3>

            <p>
              <strong>
                Review ID:
              </strong>{" "}
              {review.id}
            </p>

            <p>
              <strong>
                Prompt ID:
              </strong>{" "}
              {review.prompt_id}
            </p>

            <p>
              <strong>
                Score:
              </strong>{" "}
              {review.score}
            </p>

            <p>
              <strong>
                Feedback:
              </strong>{" "}
              {review.feedback}
            </p>

            <p>
              <strong>
                Snapshot:
              </strong>
            </p>

            <p>
              {
                review.prompt_snapshot
              }
            </p>

            {review.reviewed_at && (
              <p>
                <strong>
                  Reviewed At:
                </strong>{" "}
                {review.reviewed_at}
              </p>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}

export default App;