# AI Image Understanding & Content Matching Engine

## 1. Problem

Blog posts often need relevant images, but selecting an image using filenames or keywords can produce incorrect results. For example, an article about red foxes should not receive a visually similar wolf image.

This system understands the actual content of images and matches them to blog posts based on semantic meaning rather than filenames or exact keywords.

The most important behavior is safe rejection: when no image is a sufficiently good match, the system should return **"no confident match"** instead of guessing.

## 2. Goal

Build a backend service that:

* Understands images using a vision model.
* Produces structured metadata including subject, category, attributes, caption, and confidence.
* Validates all vision-model output against a schema.
* Creates embeddings for image descriptions and blog posts.
* Ranks images by semantic similarity.
* Uses a mismatch guard to reject incorrect or low-confidence matches.
* Provides an explanation when a recommendation is rejected.
* Supports human review through API endpoints.
* Measures matching quality using a labeled evaluation set.

## 3. Data Model

### Image

* `id`
* `filename`
* `path`
* `subject`
* `category`
* `attributes`
* `caption`
* `confidence`
* `status`
* `created_at`

### Image Vector

* `id`
* `image_id`
* `embedding`
* `created_at`

### Post

* `id`
* `title`
* `content`
* `created_at`

### Post Vector

* `id`
* `post_id`
* `embedding`
* `created_at`

### Suggestion

* `id`
* `post_id`
* `image_id`
* `similarity_score`
* `guard_status`
* `guard_reason`
* `created_at`

### Review

* `id`
* `suggestion_id`
* `decision`
* `created_at`

### AI Cost Log

* `id`
* `operation`
* `model`
* `item_id`
* `cost`
* `created_at`

## 4. API Surface

The backend will expose endpoints for:

* Health checking.
* Image ingestion and processing.
* Running the image batch job.
* Creating and managing posts.
* Getting ranked image suggestions for a post.
* Inspecting why an image was selected or rejected.
* Approving a suggested pairing.
* Rejecting a suggested pairing.
* Running the evaluation.

Example:

```text
GET /health

POST /images/process

POST /jobs/images

POST /posts

GET /posts/{post_id}/images

GET /suggestions/{suggestion_id}

POST /suggestions/{suggestion_id}/approve

POST /suggestions/{suggestion_id}/reject

POST /eval
```

## 5. Architecture

```text
                    ┌──────────────────┐
                    │     FastAPI      │
                    │    HTTP Layer    │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
      ┌───────▼────────┐          ┌────────▼────────┐
      │ Image Pipeline │          │ Matching Engine │
      │     Service    │          │     Service     │
      └───────┬────────┘          └────────┬────────┘
              │                            │
       ┌──────▼──────┐              ┌──────▼───────┐
       │ Vision Model│              │  Embeddings  │
       └──────┬──────┘              └──────┬───────┘
              │                            │
       ┌──────▼────────────────────────────▼───────┐
       │               PostgreSQL                  │
       │ images · posts · vectors · suggestions   │
       │ reviews · costs                           │
       └────────────────────┬──────────────────────┘
                            │
                     ┌──────▼───────┐
                     │ Mismatch Guard│
                     └──────────────┘
```

The system separates the HTTP layer, application logic, and data persistence. Slow vision and embedding work will run through background batch processing rather than blocking normal API requests.

## 6. Matching Strategy

Each image will first be processed by the vision model to produce structured metadata and a caption.

The image caption will be converted into an embedding. Blog post content will also be converted into an embedding.

For each post, image candidates will be ranked using cosine similarity between the post embedding and image embedding.

The system will therefore match concepts rather than relying on exact words. For example, a post mentioning **"Vulpes vulpes"** should be able to match an image described as a **"red fox"**.

## 7. Mismatch Guard

The mismatch guard is the safety layer between similarity ranking and the final recommendation.

It will consider:

1. Semantic similarity score.
2. Image classification/category.
3. Detected subject/tags.
4. Vision-model confidence.
5. Configured similarity thresholds.

Example:

```text
Post:
"The behavior of red foxes"

Candidate:
"Gray wolf in a forest"

Decision:
REJECTED

Reason:
Animal category/subject mismatch: expected fox, detected wolf.
```

If the candidate fails the guard, it will not be recommended even if it has a relatively high semantic similarity score.

If no candidate clears the required threshold, the API will return:

```text
No confident match
```

with an explanation such as:

```text
Similarity below threshold
```

or:

```text
Detected subject does not match the expected subject
```

Low-confidence vision classifications will be flagged for review instead of being silently accepted.

## 8. Database Design

PostgreSQL will be used for persistent storage.

The database will store:

* Image metadata.
* Image embeddings.
* Blog posts.
* Post embeddings.
* Matching suggestions.
* Approval/rejection decisions.
* AI cost records.

At the target corpus size of approximately 50 images, embeddings can be stored without requiring a dedicated vector database. Appropriate indexes will be added for frequently queried fields and relationships.

## 9. Background Processing

Vision processing and embedding generation are slow, bulk operations, so they will run as background batch jobs.

The batch system will provide:

* Progress tracking.
* Retries for failed calls.
* Idempotent processing.
* Failure visibility.
* Per-call AI cost tracking.

A failed vision response will never be silently accepted.

## 10. Evaluation

A labeled evaluation set containing at least 10 posts will be created.

Each post will have one manually identified correct image.

The main quality metric will be **top-1 precision**:

```text
Correct first suggestions
──────────────────────────
Total evaluated posts
```

The final precision value will be reported in the README and supported by the evaluation output.

## 11. Explicit Non-Goal

This project will **not** build a full image-management platform or frontend application.

The scope is a focused backend system demonstrating reliable image understanding, semantic matching, mismatch detection, evaluation, and human review through APIs.

A full frontend is unnecessary for the capstone requirements.
