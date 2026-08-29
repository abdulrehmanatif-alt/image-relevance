# AI Image Understanding & Content Matching Engine

## 1. Problem

Blog posts often need relevant images, but selecting an image using filenames, keywords, or superficial visual similarity can produce incorrect results.

For example, an article about **red foxes** should not receive an image of a visually similar **gray wolf** simply because both are animals photographed in similar environments.

This system understands the semantic content of images and matches them to blog posts using image metadata, embeddings, similarity ranking, and explicit mismatch protection.

The most important behavior is **safe rejection**: when no image is sufficiently relevant or when a candidate violates a mismatch rule, the system must return **"no confident match"** instead of guessing.

---

## 2. Goal

Build a small but production-oriented backend service that:

* Understands images using a Gemini vision model.
* Produces structured image metadata.
* Validates all model output using Pydantic.
* Flags low-confidence image classifications.
* Generates embeddings for image descriptions and blog posts.
* Ranks candidate images using semantic similarity.
* Applies a mismatch guard before recommending an image.
* Provides human-readable rejection explanations.
* Processes images through background batch jobs.
* Retries transient AI failures.
* Tracks AI calls and estimated costs.
* Persists application data in PostgreSQL.
* Supports human review through API endpoints.
* Measures matching quality using a labeled evaluation dataset.

The project intentionally focuses on a reliable backend rather than building a frontend or a complete image-management platform.

---

## 3. Technology Stack

| Component                  | Technology        |
| -------------------------- | ----------------- |
| Language                   | Python            |
| API                        | FastAPI           |
| Vision model               | Gemini Flash      |
| Embeddings                 | Gemini embeddings |
| Validation                 | Pydantic          |
| Database                   | PostgreSQL        |
| Local database environment | Docker            |
| Configuration              | `.env`            |
| Source control             | Git + GitHub      |

The project must remain compatible with the capstone requirement of **$0 / no credit card**. API usage will therefore be kept within the available free-tier limits and recorded through the AI cost log.

---

## 4. Image Metadata Schema

Each processed image will produce structured metadata.

### Image

* `id` — UUID primary key
* `filename` — original filename
* `path` — local/storage path
* `subject` — primary detected subject
* `category` — broad category such as `animal`, `vehicle`, `food`, `landscape`
* `attributes` — structured list of relevant attributes
* `caption` — human-readable description
* `confidence` — vision-model confidence from `0.0` to `1.0`
* `status` — processing state
* `created_at`
* `updated_at`

### Processing Status

Allowed image processing states:

```text
pending
processing
completed
failed
review_required
```

A failed or low-confidence image must never be silently treated as successfully processed.

---

## 5. Database Design

PostgreSQL will provide persistent storage.

### Tables

#### `images`

```text
id                  UUID PRIMARY KEY
filename            TEXT NOT NULL
path                TEXT NOT NULL UNIQUE
subject             TEXT
category            TEXT
attributes          JSONB
caption             TEXT
confidence          NUMERIC
status              TEXT NOT NULL
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

Constraints:

* `id` is the primary key.
* `path` is unique to support idempotent ingestion.
* `confidence`, when present, must be between `0.0` and `1.0`.
* `status` must use one of the defined processing states.

#### `image_vectors`

```text
id                  UUID PRIMARY KEY
image_id            UUID NOT NULL REFERENCES images(id)
embedding           JSONB
created_at          TIMESTAMP
```

Constraints:

* `image_id` is unique so the same image is not embedded repeatedly.
* The embedding belongs to exactly one image.

The initial dataset is only approximately 50 images, so a dedicated vector database is unnecessary. Embeddings can be persisted in PostgreSQL while similarity calculations are performed by the application.

#### `posts`

```text
id                  UUID PRIMARY KEY
title               TEXT NOT NULL
content             TEXT NOT NULL
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

#### `post_vectors`

```text
id                  UUID PRIMARY KEY
post_id             UUID NOT NULL REFERENCES posts(id)
embedding           JSONB
created_at          TIMESTAMP
```

Constraints:

* `post_id` is unique so a post has at most one current embedding.

#### `suggestions`

```text
id                  UUID PRIMARY KEY
post_id             UUID NOT NULL REFERENCES posts(id)
image_id            UUID NOT NULL REFERENCES images(id)
similarity_score    NUMERIC
guard_status        TEXT NOT NULL
guard_reason        TEXT
created_at          TIMESTAMP
```

Constraints:

* `(post_id, image_id)` is unique to prevent duplicate suggestions for the same pairing.
* `similarity_score` must be between `0.0` and `1.0`.
* `guard_status` is one of:

```text
accepted
rejected
no_confident_match
review_required
```

#### `reviews`

```text
id                  UUID PRIMARY KEY
suggestion_id       UUID NOT NULL REFERENCES suggestions(id)
decision            TEXT NOT NULL
created_at          TIMESTAMP
```

Allowed decisions:

```text
approved
rejected
```

#### `ai_cost_logs`

```text
id                  UUID PRIMARY KEY
operation            TEXT NOT NULL
model                TEXT NOT NULL
item_id              UUID
input_tokens        INTEGER
output_tokens       INTEGER
estimated_cost      NUMERIC
created_at          TIMESTAMP
```

The cost log records every billable AI operation for observability and evaluation.

---

## 6. Database Relationships

The main relationships are:

```text
Image 1 ───────────── 1 ImageVector

Post  1 ───────────── 1 PostVector

Post  1 ───────────── * Suggestion * ───────────── 1 Image

Suggestion 1 ──────── * Review

AI operations ──────── * AI CostLog
```

Foreign keys will enforce referential integrity.

Indexes will be added to frequently queried fields such as:

* `images.status`
* `images.subject`
* `images.category`
* `suggestions.post_id`
* `suggestions.image_id`
* `suggestions.guard_status`
* `ai_cost_logs.operation`

PostgreSQL primary keys, unique constraints, check constraints, and foreign keys will be used to enforce data integrity.

---

## 7. Idempotency

Image processing and embedding generation must be safe to retry.

The system will use stable identifiers such as the image path and database IDs to prevent duplicate processing.

Rules:

1. An image with an existing unique `path` will not create another image record.
2. An image with a completed vision result will not be processed again unless explicitly requested.
3. An image with an existing vector will not receive a duplicate vector.
4. A `(post_id, image_id)` suggestion pair will be unique.
5. Retrying a failed job will update the existing record rather than create a duplicate.

This allows background jobs to be safely retried after transient failures.

---

## 8. API Surface

The backend will expose endpoints for:

```text
GET  /health

POST /images/process

POST /jobs/images

POST /posts

GET  /posts/{post_id}/images

GET  /suggestions/{suggestion_id}

POST /suggestions/{suggestion_id}/approve

POST /suggestions/{suggestion_id}/reject

POST /eval
```

All invalid client input should produce an appropriate **4xx response** rather than an unhandled `500` error.

---

## 9. Architecture

```text
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │      HTTP Layer      │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
          ┌─────────▼─────────┐          ┌──────────▼─────────┐
          │ Image Pipeline    │          │ Matching Engine    │
          │ Service           │          │ Service            │
          └─────────┬─────────┘          └──────────┬─────────┘
                    │                               │
          ┌─────────▼─────────┐          ┌──────────▼─────────┐
          │ Gemini Vision     │          │ Gemini Embeddings  │
          └─────────┬─────────┘          └──────────┬─────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │     PostgreSQL       │
                         │                     │
                         │ images              │
                         │ posts               │
                         │ vectors             │
                         │ suggestions         │
                         │ reviews             │
                         │ AI cost logs        │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   Mismatch Guard     │
                         │                     │
                         │ similarity          │
                         │ subject/category    │
                         │ confidence           │
                         │ thresholds          │
                         └─────────────────────┘
```

Slow vision and embedding operations will run through background batch processing rather than blocking normal API requests.

---

## 10. Image Understanding Pipeline

Each image follows this pipeline:

```text
Image
  ↓
Validate input
  ↓
Gemini Vision
  ↓
Structured JSON
  ↓
Pydantic validation
  ↓
Confidence check
  ↓
Persist metadata
  ↓
Generate image embedding
  ↓
Persist embedding
  ↓
Mark processing complete
```

Gemini's multimodal capabilities support image understanding tasks such as image captioning and classification, while structured output can constrain model responses to a defined schema.

The vision response will contain at minimum:

```json
{
  "subject": "red fox",
  "category": "animal",
  "attributes": [
    "red-orange fur",
    "bushy tail",
    "outdoor environment"
  ],
  "caption": "A red fox standing in a grassy outdoor environment.",
  "confidence": 0.94
}
```

The application will validate this response using Pydantic before persistence.

---

## 11. Confidence Handling

Confidence will be represented as a value from `0.0` to `1.0`.

Initial policy:

```text
confidence >= 0.80
    → eligible for normal matching

0.60 <= confidence < 0.80
    → review_required

confidence < 0.60
    → rejected from automatic matching
```

These thresholds are configuration values and can be adjusted during evaluation.

Low-confidence classifications will never be silently treated as reliable matches.

---

## 12. Background Processing

Vision processing and embedding generation are slow bulk operations, so they will run through background jobs.

The batch system will provide:

* Progress tracking.
* Retries for transient failures.
* Idempotent processing.
* Failure visibility.
* Per-call AI cost tracking.
* No duplicate processing.
* Final success/failure status.

### Retry Policy

Transient failures may be retried up to **3 times** using increasing delays.

Permanent validation failures will not be endlessly retried.

Example:

```text
Attempt 1 → failure
     ↓
Attempt 2 → failure
     ↓
Attempt 3 → failure
     ↓
status = failed
```

A failed AI response will never be silently accepted.

---

## 13. Matching Strategy

Each successfully processed image will have:

1. Structured metadata.
2. A descriptive caption.
3. An embedding derived from its semantic description.

Each blog post will also receive an embedding.

For a post, candidate images will be ranked using cosine similarity between:

```text
post embedding
       ↕
image embedding
```

The system will return ranked candidates rather than relying on exact keyword matching.

For example:

```text
Post:
"Ecology and behavior of Vulpes vulpes"

Image metadata:
subject = "red fox"
category = "animal"
```

The semantic representation should allow the system to recognize that **Vulpes vulpes** and **red fox** refer to the same subject.

---

## 14. Mismatch Guard

The mismatch guard is the safety layer between similarity ranking and the final recommendation.

It will consider:

1. Semantic similarity score.
2. Image category.
3. Detected subject.
4. Vision-model confidence.
5. Configured similarity threshold.

The guard will run **after candidate ranking but before final recommendation**.

### Example: Valid Match

```text
Post:
"The behavior of red foxes"

Candidate:
"Red fox standing in a forest"

Similarity:
high

Subject:
red fox

Decision:
ACCEPT
```

### Example: Invalid Match

```text
Post:
"The behavior of red foxes"

Candidate:
"Gray wolf standing in a forest"

Similarity:
high enough to be considered

Subject:
gray wolf

Decision:
REJECT

Reason:
Detected subject does not match the expected subject.
```

The system must not allow a high embedding similarity score to override an explicit subject mismatch.

### Example: No Confident Match

```text
Post:
"Rare desert fox behavior"

Best candidate:
Similarity below threshold

Decision:
NO_CONFIDENT_MATCH

Reason:
No candidate exceeded the required similarity threshold.
```

---

## 15. Human Review

Candidates that are uncertain but potentially useful may be marked:

```text
review_required
```

Review endpoints will allow a human to:

```text
approve
reject
```

a suggestion.

Human decisions will be persisted in the `reviews` table.

---

## 16. Evaluation Dataset

A labeled evaluation set containing at least **10 posts** will be created.

Each evaluation post will have one manually identified correct image.

The evaluation dataset will deliberately contain difficult near-matches, including examples such as:

```text
fox ↔ wolf
cat ↔ dog
car ↔ motorcycle
mountain ↔ hill
```

This ensures that the evaluation tests both semantic ranking and mismatch protection.

---

## 17. Evaluation Metric

The primary quality metric is **Top-1 Precision**:

```text
Number of evaluated posts where the correct image ranks first
───────────────────────────────────────────────────────────
Total evaluated posts
```

For example:

```text
9 correct first suggestions
─────────────────────────── = 0.90
10 evaluated posts
```

The final measured precision will be reported in:

```text
README.md
EVIDENCE.md
BUILDLOG.md
```

The evaluation output will also be retained as evidence.

---

## 18. Cost Tracking

Every Gemini operation will create an `ai_cost_logs` record.

At minimum, the record will identify:

```text
operation
model
item_id
input tokens
output tokens
estimated cost
timestamp
```

The purpose is to make AI usage visible and auditable.

The project will remain within the required **$0 / no credit card** constraint.

---

## 19. Dataset

The initial development dataset will contain approximately **50 images**.

The dataset will include:

* Multiple subject categories.
* Multiple examples of the same subject.
* Visually similar but semantically different subjects.
* Images suitable for mismatch testing.
* Metadata needed for evaluation.

The dataset will be organized so that image identity and expected subject labels can be reproduced consistently.

The final repository will document the dataset source and licensing/usage status.

---

## 20. Phase Gates

### Phase 1 — Design

Required:

* Design document.
* Image metadata/schema.
* Matching strategy.
* Mismatch-guard rules.
* Database design.
* Approximately 50-image dataset.

**Gate:** design committed and dataset available.

### Phase 2 — Image Understanding Pipeline

Required:

* Gemini Vision.
* Structured JSON output.
* Pydantic validation.
* Low-confidence flagging.
* Background batch processing.
* Retries.
* Idempotency.
* Cost tracking.

**Gate:** all dataset images processed successfully or explicitly recorded as failed, with AI costs visible.

### Phase 3 — Matching Engine

Required:

* Image embeddings.
* Post embeddings.
* Similarity search.
* Ranking.
* Mismatch guard.
* Human-readable rejection explanations.

**Gate:**

```text
Fox article → fox ranks first

Forced wolf candidate → rejected
```

### Phase 4 — Production Layer

Required:

* Review API.
* Evaluation dataset.
* Top-1 precision.
* README.
* Architecture diagram.
* `EVIDENCE.md`.
* `BUILDLOG.md`.

**Gate:** measured evaluation precision is produced and documented.

---

## 21. Explicit Non-Goals

This project will **not** build:

* A frontend application.
* A full image-management platform.
* User authentication.
* Complex cloud infrastructure.
* A dedicated vector database.
* Model training or fine-tuning.

The scope is a focused backend system demonstrating:

* Reliable image understanding.
* Structured AI output.
* Semantic matching.
* Mismatch detection.
* Background processing.
* Persistence.
* Cost tracking.
* Evaluation.
* Human review.

The goal is not to build the biggest system possible.

The goal is to build a **small, testable, evidence-backed backend that behaves correctly when the obvious answer is wrong**.
