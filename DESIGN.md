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
| Local database environment | PostgreSQL        |
| Configuration              | `.env`            |
| Source control             | Git + GitHub      |

The project must remain compatible with the capstone requirement of **$0 / no credit card**. AI usage is therefore planned around available free-tier resources, while the system records AI calls, usage information, and estimated costs for monitoring.

Free-tier quota limits may restrict how quickly the development dataset can be processed. Such quota failures are recorded as processing failures rather than being treated as successful results.

---

## 4. Image Metadata Schema

The system stores structured metadata for each image after vision processing.

The metadata is represented using Pydantic validation before being persisted to the database.

### Image Understanding Schema

```text
subject       string
category      string
attributes    list
caption       string
confidence    float
```

The `confidence` value must be between `0.0` and `1.0`.

The validated metadata is stored in the corresponding fields of the `images` table:

```text
subject
category
attributes
caption
confidence
```

Additional processing state is stored in:

```text
status
embedding
error
```

### Processing Status

The `images.status` field tracks the outcome of image processing.

The processing pipeline uses:

```text
processed
failed
```

The database model uses `pending` as the default status for newly created image records before processing begins.

A failed image must never be silently treated as successfully processed. The `error` field stores failure information when processing does not complete successfully.

The current implementation uses an integer database ID and a unique `filename` to identify each image. It does not store separate creation or update timestamps.

---

## 5. Database Design

PostgreSQL provides persistent storage for image metadata, human review decisions, and AI operation logs.

### Tables

#### `images`

```text
id            INTEGER PRIMARY KEY
filename      VARCHAR(255) NOT NULL UNIQUE
status        VARCHAR(50) NOT NULL
subject       VARCHAR(100)
category      VARCHAR(100)
attributes    JSONB
caption       TEXT
confidence    FLOAT
embedding     JSONB
error         TEXT
```

The `images` table stores the complete state of each processed image.

Constraints and behavior:

* `id` is the primary key.
* `filename` is unique to prevent duplicate image records.
* `status` tracks the image processing state.
* `confidence`, when present, represents the vision model's confidence.
* `embedding` stores the generated image embedding.
* `error` stores failure information when image processing does not complete successfully.

#### `reviews`

```text
id            INTEGER PRIMARY KEY
filename      VARCHAR(255) NOT NULL UNIQUE
decision      VARCHAR(50) NOT NULL
feedback      TEXT
```

The `reviews` table stores human review decisions for processed images.

Constraints and behavior:

* `id` is the primary key.
* `filename` uniquely identifies the reviewed image.
* `decision` stores the review outcome.
* `feedback` optionally stores additional reviewer comments.

#### `ai_calls`

```text
id              INTEGER PRIMARY KEY
operation       VARCHAR(100) NOT NULL
provider        VARCHAR(50) NOT NULL
model           VARCHAR(100) NOT NULL
input_tokens    INTEGER
output_tokens   INTEGER
estimated_cost  FLOAT NOT NULL
success         BOOLEAN NOT NULL
error           TEXT
```

The `ai_calls` table records AI operations for observability, reliability tracking, and cost monitoring.

Constraints and behavior:

* `id` is the primary key.
* `operation` identifies the type of AI operation performed.
* `provider` identifies the AI provider.
* `model` identifies the model used.
* `input_tokens` and `output_tokens` record token usage when available.
* `estimated_cost` records the estimated cost of the operation.
* `success` indicates whether the AI operation completed successfully.
* `error` stores failure information when an AI operation fails.

The current implementation intentionally keeps image embeddings in the `images` table rather than maintaining a separate vector table or dedicated vector database. This is sufficient for the approximately 50-image development dataset and keeps the architecture simple.

---

## 6. Database Relationships

The current implementation keeps the database relationships intentionally simple.

```text
Image processing
      │
      ▼
   images
      │
      │ filename
      ▼
   reviews

AI operations
      │
      ▼
   ai_calls
```
The `reviews.filename` field identifies the image being reviewed, while `ai_calls` independently records AI operations performed by the system.

The current implementation does not use separate tables for image vectors, posts, post vectors, or suggestions. Image embeddings are stored directly in the `images.embedding` field.

Indexes are used on frequently queried fields:

* `images.filename`
* `images.status`
* `images.subject`
* `images.category`
* `reviews.filename`
* `ai_calls.operation`
* `ai_calls.success`

PostgreSQL primary keys and unique constraints are used to maintain data integrity. The `filename` uniqueness constraints prevent duplicate image and review records.

---

## 7. Idempotency

Image processing is designed to be safe to retry without creating duplicate image records.

The system uses the image `filename` and existing database or dataset state to maintain consistent processing state.

Rules:

1. An image with an existing unique `filename` will not create another image record in PostgreSQL.

2. An image that is already marked as successfully processed in the dataset is skipped by the batch job.

3. Retrying a failed image-processing job updates the existing dataset record rather than creating a duplicate entry.

4. The corresponding PostgreSQL `images` record is updated using its unique `filename`.

5. AI operations are recorded in the `ai_calls` table when they are recorded by the relevant AI service.

The current batch-processing implementation does not use the presence of an embedding as an independent duplicate-prevention condition. Image embedding generation is handled separately from the vision batch job.

This allows the image-processing batch to be safely rerun while keeping image records and dataset entries associated with a unique filename.

---

## 8. API Surface

The backend exposes versioned REST endpoints under `/api/v1`.

### Health

```text
GET /health
```

Returns the health status of the application.

### Image Matching

```text
POST /api/v1/match
```

Accepts blog content and runs the image matching analysis.

```text
GET /api/v1/test
```

Provides a simple route-level connectivity check for the image matching router.

### Background Image Processing

```text
POST /api/v1/jobs/image-batch
```

Starts the image batch-processing job as a FastAPI background task.

The endpoint immediately returns a job-started response while image processing continues in the background.

### Human Review

```text
POST /api/v1/review
```

Submits a human review decision for an image.

```text
GET /api/v1/review/{filename}
```

Retrieves the stored review for a specific image filename.

If no review exists, the endpoint returns a rejected response indicating that no review has been submitted.

### Evaluation

```text
GET /api/v1/evaluation
```

Runs the evaluation service and returns the current evaluation result.

All request and response schemas are validated using Pydantic models where applicable.

Invalid client input should produce an appropriate `4xx` response rather than an unhandled `500` error.

---

## 9. Architecture

The system follows a layered backend architecture with separate API, processing, matching, validation, and persistence responsibilities.

```text
                         ┌─────────────────────────┐
                         │        FastAPI          │
                         │       HTTP Layer        │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
             Image Matching        Jobs              Review
                Routes             Routes             Routes
                    │                 │                 │
                    ▼                 ▼                 ▼
           ImageMatchingService   Image Batch      ReviewService
                                      Processing
                    │                 │
                    ▼                 │
             MatchingService          │
                    │                 │
          ┌─────────┼─────────┐       │
          │         │         │       │
          ▼         ▼         ▼       ▼
       Post      Similarity  Mismatch  Vision /
     Embedding    Service     Guard   Embedding
       Service                         Services
          │         │         │         │
          └─────────┴─────────┴─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │    PostgreSQL    │
                │                  │
                │ images           │
                │ reviews          │
                │ ai_calls         │
                └──────────────────┘
```

### Image Processing Flow

The vision batch pipeline performs image understanding and metadata persistence:

```text
Image
  ↓
Vision Processing
  ↓
Pydantic Validation
  ↓
Persist Image Metadata
  ↓
Mark Processed / Failed
```

Image embeddings are generated by a separate embedding pipeline using the configured Gemini embedding service. The generated 768-dimensional embeddings are stored directly in the PostgreSQL `images.embedding` field.

The matching engine loads these stored embeddings from PostgreSQL when constructing image candidates. The current development dataset contains 50 images with successfully generated embeddings.

### Matching Flow

A blog post is processed through the matching pipeline:

```text
Blog Content
     ↓
PostEmbeddingService
     ↓
Post Embedding
     ↓
Cosine Similarity
     ↓
Candidate Images
     ↓
MismatchGuard
     ↓
Accepted / Rejected Candidates
     ↓
Rank by Acceptance + Similarity
     ↓
Best Accepted Image
```

`MatchingService` loads processed images that have embeddings stored in PostgreSQL. It calculates cosine similarity between the blog-post embedding and each stored image embedding.

The `MismatchGuard` then checks the similarity threshold and, when image metadata is available, validates image confidence and whether the image subject or category is mentioned in the blog content.

`ImageMatchingService` returns the highest-ranked accepted image. If no candidate passes the mismatch guard, the API returns a rejection response instead of selecting an image.


### Evaluation and Human Review

The evaluation and review components operate through their own API routes and services:

```text
Evaluation Route → EvaluationService

Review Route     → ReviewService
```

Human review decisions are persisted in the `reviews` table, while AI operations are recorded in the `ai_calls` table.

This architecture keeps image processing, matching, mismatch protection, evaluation, and human review separated into focused services while using PostgreSQL as the persistent application data layer.

---

## 10. Image Understanding Pipeline

Each image is processed through a vision-understanding pipeline that validates the model output before storing the result.

```text
Image
  ↓
Validate image exists
  ↓
Gemini Vision
  ↓
Structured JSON
  ↓
Pydantic validation
  ↓
Persist metadata
  ↓
Mark as processed / failed
```

The vision service uses Gemini with a structured response schema based on the `ImageUnderstanding` Pydantic model.

The vision response contains:

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

The application validates the response using Pydantic before the metadata is persisted.

### Image Metadata Persistence

For a successfully processed image, the following fields are stored in the `images` table:

```text
subject
category
attributes
caption
confidence
status
error
```

The processing status is set to:

```text
processed
```

when vision processing succeeds.

If processing fails after the retry policy is exhausted, the image is stored with:

```text
status = failed
```

and the failure information is stored in the `error` field.

### Image Embeddings

Image embeddings are generated by the image embedding pipeline using the configured Gemini embedding service.

The current pipeline performs:

```text
Image
  ↓
Gemini Embedding Service
  ↓
768-dimensional Image Embedding
  ↓
PostgreSQL images.embedding
```

Each generated embedding is stored directly in the `embedding` field of the corresponding PostgreSQL `images` record.

The image embedding pipeline matches images to existing database records using their unique filenames. This allows the matching service to load the stored image embeddings directly from PostgreSQL.

The current implementation has successfully generated embeddings for all 50 development images, with each embedding containing 768 dimensions.

### AI Usage Tracking

Successful vision operations record AI usage information including:

```text
prompt tokens
output tokens
thoughts tokens
total tokens
estimated cost
```

AI operations are also recorded in the PostgreSQL `ai_calls` table for observability and cost tracking.

### Batch Processing

The background image batch job processes `.jpg` images in `data/images`.

For each image, the job:

1. Checks whether the image has already been successfully processed.
2. Sends the image to the Gemini vision service.
3. Retries supported transient API failures up to three attempts.
4. Stores successful metadata in PostgreSQL.
5. Records failed images and their error information.
6. Updates dataset statistics and usage information.
7. Persists the updated dataset state to `data/dataset.json`.

Already processed images are skipped, allowing the batch job to be safely rerun without unnecessarily repeating successful vision processing.

---

## 11. Confidence Handling

The vision model's confidence value represents the confidence of the generated image metadata.

The value is validated by the `ImageUnderstanding` Pydantic schema and must be within:

```text
0.0 <= confidence <= 1.0
```

The current mismatch guard uses a minimum confidence threshold of:

```text
MIN_CONFIDENCE = 0.80
```

During matching:

```text
confidence >= 0.80
    → eligible for metadata-based matching

confidence < 0.80
    → rejected by the mismatch guard
```

The confidence check is applied when image subject or category metadata is available.

A low-confidence image is therefore not automatically accepted as a valid match.

The threshold is currently implemented as a class constant in the mismatch guard and can be adjusted in the implementation when required for evaluation.

---

## 12. Background Processing

Image understanding is executed as a background batch-processing job so that multiple images can be processed without requiring a separate request for each image.

The batch job is started through:

```text
POST /api/v1/jobs/image-batch
```

The processing flow is:

```text
Start Batch Job
      ↓
Load dataset
      ↓
Find .jpg images
      ↓
Check existing processing status
      ↓
Skip already processed images
      ↓
Process image with Gemini Vision
      ↓
Retry transient API failures
      ↓
Store result or failure
      ↓
Update dataset.json
      ↓
Calculate usage and dataset statistics
      ↓
Save final batch state
```

### Retry Policy

The image-processing job allows up to **3 attempts** for transient Gemini API failures.

Retryable API error codes are:

```text
429
500
502
503
504
```

A delay of **2 seconds** is applied between retry attempts.

Daily quota exhaustion is not retried because repeating the request will not resolve the quota limitation.

Non-retryable API errors and unexpected exceptions terminate processing for the affected image and are recorded as failures.

### Idempotent Batch Behavior

Before processing an image, the job checks `dataset.json` for an existing record with the same filename.

Images whose existing status is:

```text
processed
```

are skipped.

If an image is processed again after a failure, its existing dataset record is replaced with the new result rather than creating a duplicate entry.

The corresponding PostgreSQL `images` record is also updated using the unique filename.

### Failure Handling

When processing fails after the available attempts, the image is stored with:

```text
status: failed
error: <error message>
attempts: <number of attempts>
```

Failed images are also included in a `failure_alert` summary containing the failed count and filenames.

This ensures that processing failures remain visible instead of being silently ignored.

### Dataset and Usage Summary

After processing, the batch job calculates:

* category counts
* prompt token usage
* output token usage
* thoughts token usage
* total token usage
* estimated cost
* total successful images
* failed image count

The dataset is marked as final only when:

```text
50 images exist
AND
50 images are successfully processed
AND
0 images have failed
```

The resulting dataset state is persisted to `data/dataset.json`.

---

## 13. Matching Strategy

The matching system compares the semantic representation of a blog post with stored image embeddings.

Both blog text and images are embedded using the configured Gemini embedding model with an output dimensionality of **768**.

### Blog Post Embedding

```text
Blog Content
     ↓
PostEmbeddingService
     ↓
Gemini Text Embedding
     ↓
768-dimensional vector
```

### Image Embedding

```text
Image
  ↓
EmbeddingService
  ↓
Gemini Image Embedding
  ↓
768-dimensional vector
  ↓
PostgreSQL images.embedding
```

The image embedding pipeline generates embeddings for images in `data/images` and stores each generated embedding directly in the `embedding` field of the corresponding PostgreSQL `images` record.

The matching service loads these stored embeddings from PostgreSQL when constructing the candidate image set.

The current development dataset contains **50 images with successfully generated 768-dimensional embeddings**.

### Similarity Calculation

For each image with a stored embedding, the system calculates cosine similarity between:

```text
blog post embedding
        ↕
image embedding
```

The cosine similarity implementation validates that both vectors have the same dimensionality and returns a score representing their semantic similarity.

### Ranking

Each candidate image receives:

```text
filename
similarity score
accepted / rejected status
explanation
```

Candidates are sorted with accepted images first and higher similarity scores first within the same acceptance status.

The highest-ranked accepted image is returned as the final match.

If no image passes the mismatch guard, the system returns a rejection response instead of selecting an unsuitable image.

### Matching Flow

```text
Blog Content
      ↓
Generate Text Embedding
      ↓
Load Images With Stored Embeddings
      ↓
Calculate Cosine Similarity
      ↓
Run Mismatch Guard
      ↓
Accepted / Rejected
      ↓
Sort by Acceptance + Similarity
      ↓
Return Best Accepted Image
```

The matching process therefore combines semantic similarity with deterministic metadata-based validation rather than relying on embedding similarity alone.

---

## 14. Mismatch Guard

The mismatch guard prevents an image from being accepted solely because it has a relatively high embedding similarity score.

Each candidate must pass the following checks.

### 1. Similarity Threshold

The candidate must have a cosine similarity of at least:

```text
SIMILARITY_THRESHOLD = 0.30
```

Candidates below this threshold are rejected.

```text
similarity < 0.30
    → rejected
```

### 2. Confidence Threshold

When image subject or category metadata is available, the image confidence must be at least:

```text
MIN_CONFIDENCE = 0.80
```

```text
confidence < 0.80
    → rejected
```

### 3. Metadata Relevance Check

When vision metadata is available, the guard uses the most specific available metadata for the relevance check.

If an image subject is available, the blog post must contain that subject.

```text
subject available
       ↓
subject mentioned in post?
       ↓
   Yes → pass
   No  → reject
```

If no subject is available but a category is available, the blog post must contain that category.

```text
subject unavailable
       ↓
category available
       ↓
category mentioned in post?
       ↓
   Yes → pass
   No  → reject
```

A broad category cannot override a specific subject mismatch. For example, an image with subject `wolf` and category `animal` is rejected for a post about a `fox` even though the word `animal` appears in the post.

The current implementation performs this as a case-insensitive literal substring check. It does not use another AI model or semantic classifier for this metadata check.

### Guard Decision

The complete decision flow is:

```text
Candidate Image
      ↓
Similarity >= 0.30?
      │
     No ───────→ Reject
      │
     Yes
      ↓
Metadata available?
      │
     No ───────→ Accept
      │
     Yes
      ↓
Confidence >= 0.80?
      │
     No ───────→ Reject
      │
     Yes
      ↓
Subject available?
      │
     Yes
      ↓
Subject mentioned?
      │
     No ───────→ Reject
      │
     Yes
      ↓
    Accept

If subject is unavailable:
      ↓
Category available?
      │
     Yes
      ↓
Category mentioned?
      │
     No ───────→ Reject
      │
     Yes
      ↓
    Accept
```

Each rejection includes a human-readable explanation indicating which guard condition was not satisfied.

This guard provides a deterministic safety layer after semantic similarity calculation and prevents weak or obviously unrelated candidates from being returned as final matches.

---

## 15. Human Review

The system provides a human review layer for recording manual decisions about image relevance.

A reviewer can submit one of two decisions:

```text
approved
rejected
```

Optional reviewer feedback can also be stored with the decision.

### Review API

```text
POST /api/v1/review
```

Submits or updates a review decision for an image.

```text
GET /api/v1/review/{filename}
```

Retrieves the stored review decision for a specific image.

### Review Persistence

Human review decisions are persisted in the `reviews` table:

```text
id
filename
decision
feedback
```

The `filename` field is unique, so submitting another review for the same image updates the existing review rather than creating a duplicate record.

The review service stores and retrieves human decisions but does not automatically modify image metadata, embeddings, similarity scores, or mismatch-guard thresholds.

Human review therefore acts as a separate verification layer around the automated matching system.

---

## 16. Evaluation Dataset

The system includes a separate evaluation dataset stored in:

```text
data/eval_dataset.json
```

The dataset contains **10 evaluation posts**, covering the 10 target image categories:

```text
fox
wolf
cat
dog
bird
horse
motorcycle
car
mountain
plain
```

Each evaluation record contains:

```json
{
  "post": "A wild fox walking through a forest.",
  "expected_category": "fox"
}
```

The `post` field contains the input blog content, while `expected_category` identifies the expected image category.

### Evaluation Process

For each evaluation post:

1. The post is converted into an embedding.
2. The matching service ranks the available image candidates.
3. Candidates rejected by the mismatch guard are removed from consideration.
4. The highest-ranked accepted image is selected.
5. The predicted category is extracted from the selected filename.
6. The predicted category is compared with the expected category.

The evaluation records the post, expected category, predicted category, selected filename, similarity score, and whether the prediction was correct.

If no candidate passes the mismatch guard, the evaluation records no predicted category and marks the result as incorrect.

The evaluation dataset is kept separate from the development image dataset so that matching performance can be measured using a fixed set of test inputs.

---

## 17. Evaluation Metric

The primary evaluation metric is **Top-1 Precision**.

For each evaluation post, the system considers the highest-ranked image that passes the mismatch guard.

A prediction is counted as correct when the category derived from the selected image filename matches the expected category in the evaluation dataset.

The metric is calculated as:

```text
Top-1 Precision = Correct Predictions / Total Evaluations
```

For the current evaluation dataset:

```text
Total evaluations = 10
```

The evaluation service returns:

```text
total
correct
top_1_precision
results
```

Each individual result also records:

```text
post
expected_category
predicted_category
filename
score
correct
```

If no image passes the mismatch guard for an evaluation post, the prediction is recorded as incorrect.

Top-1 precision provides a direct measure of whether the system selects an image from the expected category as its highest-ranked accepted result.

---

## 18. Cost Tracking

The system tracks AI operations through the PostgreSQL `ai_calls` table.

Each recorded AI call contains:

```text
operation
provider
model
input_tokens
output_tokens
estimated_cost
success
error
```

The `AICostService` records AI operations performed by the vision and embedding services.

### Cost Estimation

For operations where token usage is available, the application estimates cost using the configured token rates:

```text
Input cost  = input tokens × 0.75 / 1,000,000

Output cost = output tokens × 3.75 / 1,000,000

Estimated cost = input cost + output cost
```

Embedding operations currently record an estimated cost of `0.0` because token usage is not returned by the current embedding implementation.

These values represent **application-level estimates**, not confirmed provider billing.

### Budget Protection

Before an AI operation is executed, the system checks the accumulated estimated cost against the configured AI budget limit.

```text
Current accumulated cost
        +
Estimated new operation cost
        ≤
Configured budget limit
```

If the estimated operation would exceed the configured budget limit, the operation is rejected before the API call is made.

### Cost Reporting

The system can calculate the total estimated AI cost by summing the `estimated_cost` values stored in `ai_calls`.

This provides persistent application-level cost monitoring across vision and embedding operations while supporting the project's requirement to operate within its configured AI usage budget.

---

## 19. Dataset

The development dataset is stored in:

```text
data/dataset.json
```

The dataset is represented as a development fixture with the following configuration:

```text
version: dev-1.0
target_image_count: 50
final_dataset: false
```

The intended dataset contains **50 images across 10 target categories**, with five images planned for each category:

```text
fox
wolf
cat
dog
bird
horse
motorcycle
car
mountain
plain
```

Each successfully processed image contains:

```text
filename
path
subject
category
attributes
caption
confidence
status
attempts
usage
```

Failed images instead record their filename, path, processing status, number of attempts, and error information.

### Dataset Processing State

The dataset maintains processing statistics including:

```text
category_counts
usage_summary
failure_alert
```

The `final_dataset` field is set to `true` only when all 50 expected images have been successfully processed with no failures.

The current development fixture is therefore treated as an **incomplete development dataset** until all required images have been processed successfully.

### Dataset and AI Metadata

For successfully processed images, the dataset records AI usage information including:

```text
prompt_tokens
output_tokens
thoughts_tokens
total_tokens
estimated_cost
```

This allows the dataset-building process to track both processing results and AI resource usage.

The dataset is used as the source for the background image-processing pipeline, while the PostgreSQL database stores the corresponding image metadata required by the application.

---

## 20. Phase Gates

The project is developed in four phases. Each phase has a defined completion gate based on the implemented system and required evidence.

### Phase 1 — Design and Data Foundation

Required:

* Design document.
* Image metadata schema.
* Matching strategy.
* Mismatch-guard rules.
* PostgreSQL database design.
* Approximately 50-image development dataset.
* Database models and migrations.

**Gate:** design, database structure, and development dataset are available and consistent with the implemented architecture.

### Phase 2 — Image Understanding Pipeline

Required:

* Gemini Vision integration.
* Structured JSON output.
* Pydantic validation.
* Confidence validation and low-confidence handling.
* Background batch processing.
* Retry handling for transient API failures.
* Idempotent processing behavior.
* AI usage and cost tracking.
* Failure recording.

**Gate:** the batch pipeline can process the development dataset while recording successful results, failures, retry information, and AI usage statistics.

### Phase 3 — Matching Engine

Required:

* Image embeddings.
* Blog-post text embeddings.
* Cosine similarity calculation.
* Candidate ranking.
* Mismatch guard.
* Human-readable rejection explanations.
* Integration of generated image embeddings with the PostgreSQL `images.embedding` field used by the matching service.

**Gate:**

The matching pipeline must demonstrate the intended behavior using actual evaluation inputs and stored image data:

```text
Fox article → fox candidate ranks highest among accepted results

Forced wolf candidate → rejected when the mismatch guard conditions are not satisfied
```

These are acceptance-test scenarios used to verify the matching and mismatch-protection behavior.

The current implementation has successfully integrated image embeddings into PostgreSQL and generated 768-dimensional embeddings for all 50 development images.

The evaluation dataset currently contains 10 labeled posts covering the 10 development categories. The latest evaluation run achieved:

```text
Total evaluation cases: 10
Correct: 10
Top-1 precision: 1.00
```

The detailed evaluation results are treated as project evidence and are recorded separately from this design specification.

### Phase 4 — Evaluation and Evidence

Required:

* Review API.
* Evaluation dataset.
* Top-1 precision calculation.
* README documentation.
* Architecture diagram.
* `EVIDENCE.md`.
* `BUILDLOG.md`.

**Gate:** the evaluation endpoint produces a measured Top-1 precision result, and the final project documentation records the evaluation setup, result, and supporting evidence.

### Phase Completion Rule

A phase is considered complete when its required implementation is available and its gate can be demonstrated using the project's actual code, database state, dataset, or evaluation output.

---

## 21. Explicit Non-Goals

This project will **not** build:

* A frontend application.
* A full image-management platform.
* User authentication and account management.
* Complex cloud infrastructure or distributed deployment.
* A dedicated vector database.
* Model training or fine-tuning.
* A large-scale production deployment.

The system is intentionally designed as a focused backend application demonstrating:

* Reliable image understanding.
* Structured AI output and validation.
* Semantic image-to-text matching.
* Mismatch detection and rejection.
* Background batch processing.
* PostgreSQL persistence.
* AI usage and cost tracking.
* Evaluation and measurable results.
* Human review.

The project uses a local PostgreSQL environment and keeps the architecture intentionally small enough to develop, test, and evaluate without requiring Docker, Kubernetes, or other deployment infrastructure.

The goal is not to build the biggest system possible.

## The goal is to build a **small, testable, evidence-backed backend that behaves correctly when the obvious answer is wrong**.
