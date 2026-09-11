# AI Image Understanding & Content Matching Engine

A backend AI system that understands an image library and matches the most relevant image to a blog post using multimodal embeddings and a mismatch guard.

The project is designed around a simple principle:

> Choose the right image when the evidence is strong, and safely reject the match when it is not.

## What It Does

The system:

1. Maintains a dataset of 50 images across 10 categories.
2. Generates multimodal image embeddings with Gemini.
3. Generates a text embedding for a blog post.
4. Compares the post embedding against every image embedding using cosine similarity.
5. Applies a mismatch guard using similarity and, when available, image-understanding metadata.
6. Returns the highest-ranked accepted image.
7. Rejects the request when no candidate passes the guard.

## Current Status

The core image matching and mismatch-rejection flow is implemented and evaluated.

### Evaluation

* Dataset: 50 images
* Categories: 10
* Evaluation posts: 10
* Top-1 correct predictions: 10/10
* Top-1 precision: **100%**
* Forced mismatch test: **passed**

The evaluation includes one labeled post for each category:

`fox`, `wolf`, `cat`, `dog`, `bird`, `horse`, `motorcycle`, `car`, `mountain`, `plain`.

The forced mismatch test verifies that a wolf image is rejected for a fox-related post when its similarity score falls below the configured threshold.

## Architecture

```text
                    ┌──────────────────────┐
                    │      Blog Post       │
                    │       Text           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Post Embedding     │
                    │      Gemini          │
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────┐   ┌──────────────────────┐
│   Image Library  │──▶│   Matching Engine    │
│    50 images     │   │   Cosine Similarity  │
└────────┬─────────┘   └──────────┬───────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐    ┌──────────────────────┐
│ Image Embeddings │    │    Mismatch Guard    │
│     Gemini       │    │ Threshold + Metadata │
└──────────────────┘    └──────────┬───────────┘
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                     ┌─────────┐       ┌─────────┐
                     │  Accept │       │  Reject │
                     └────┬────┘       └────┬────┘
                          │                 │
                          └────────┬────────┘
                                   ▼
                              FastAPI API
```

## Matching Pipeline

### 1. Image Embeddings

The image embedding pipeline reads the images from:

```text
data/images/
```

Each image is sent to Gemini's multimodal embedding model:

```text
gemini-embedding-2-preview
```

The resulting embeddings use 768 dimensions and are stored in:

```text
data/image_embeddings.json
```

### 2. Blog Post Embedding

A blog post is converted into a text embedding using the same embedding model.

This places the post and images in a shared embedding space, allowing semantic comparison between them.

### 3. Similarity Calculation

The system calculates cosine similarity between the blog-post embedding and every image embedding.

Candidates are ranked by:

1. Whether they passed the mismatch guard.
2. Their similarity score.

### 4. Mismatch Guard

The mismatch guard prevents the system from blindly returning the highest-similarity image.

The current provisional similarity threshold is:

```text
0.30
```

For images with available vision metadata, the guard also requires:

* Confidence of at least `0.80`.
* The post text to mention either the image subject or category.

If no candidate passes the guard, the API returns a safe rejection instead of guessing.

The similarity threshold is provisional and should be tuned further using a larger evaluation dataset.

## Image Understanding

The project also contains a Gemini Vision pipeline for structured image understanding.

Image metadata is represented using Pydantic validation and includes:

* `subject`
* `category`
* `attributes`
* `caption`
* `confidence`

The batch-processing job can identify already processed images and supports retry/error handling for image processing.

Some image-understanding records in the current dataset failed because of Gemini API quota/rate-limit responses. The matching pipeline therefore handles images with unavailable vision metadata without automatically rejecting the entire image library.

## Dataset

The current dataset contains:

| Category   | Images |
| ---------- | -----: |
| Fox        |      5 |
| Wolf       |      5 |
| Cat        |      5 |
| Dog        |      5 |
| Bird       |      5 |
| Horse      |      5 |
| Motorcycle |      5 |
| Car        |      5 |
| Mountain   |      5 |
| Plain      |      5 |
| **Total**  | **50** |

The dataset is stored in:

```text
data/dataset.json
```

The evaluation dataset is stored in:

```text
data/eval_dataset.json
```

## API

The application is built with FastAPI.

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Test Route

```http
GET /api/v1/test
```

Response:

```json
{
  "message": "Image matching route is working"
}
```

### Match an Image to a Blog Post

```http
POST /api/v1/match
```

Request:

```json
{
  "blog_content": "A beautiful bird flying over a mountain landscape."
}
```

Example response:

```json
{
  "filename": "bird_004.jpg",
  "score": 0.3337994329018925,
  "accepted": true,
  "explanation": "Candidate passed similarity and available metadata checks."
}
```

If no candidate passes the mismatch guard:

```json
{
  "filename": "",
  "score": 0.0,
  "accepted": false,
  "explanation": "No image passed the mismatch guard for this blog post."
}
```

Interactive API documentation is available through FastAPI's Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## Project Structure

```text
image-relevance/
│
├── app/
│   ├── jobs/
│   │   ├── image_batch.py
│   │   └── image_matching_job.py
│   │
│   ├── routes/
│   │   └── evaluation.py
│   │   └── image_matching.py
│   │   └── review.py
│   │
│   ├── schemas/
│   │   ├── image.py
│   │   ├── image_matching.py
│   │   └── image_matching_response.py
│   │   └── review.py
│   │
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── image_embedding_pipeline.py
│   │   ├── image_matching_service.py
│   │   ├── llm_service.py
│   │   ├── matching_service.py
│   │   ├── mismatch_guard.py
│   │   ├── post_embedding_service.py
│   │   ├── similarity_service.py
│   │   ├── vision.py
│   │   ├── evaluation_service.py
│   │   └── review_service.py
│   │
│   ├── config.py
│   └── main.py
│
├── data/
│   ├── images/
│   ├── dataset.json
│   ├── eval_dataset.json
│   └── image_embeddings.json
│
├── scripts/
├── tests/
├── .env.example
├── DESIGN.md
├── requirements.txt
└── pytest.ini
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/abdulrehmanatif-alt/image-relevance.git
cd image-relevance
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

Set your Gemini API key:

```text
APP_NAME=AI Image Understanding & Content Matching Engine

DEBUG=True

LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
LLM_API_KEY=your_api_key_here
EMBEDDING_MODEL=gemini-embedding-2-preview
```

Do not commit `.env` or expose the API key.

### 5. Run the API

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

Run the test suite with:

```bash
python -m pytest -q
```

The project includes tests for:

* Image metadata schema validation.
* Image batch-processing behavior.
* Top-1 matching evaluation.
* Forced mismatch rejection.

The current evaluation result is:

```text
Top-1 precision: 100.00%
Correct: 10/10
```

## Technologies

* Python
* FastAPI
* Pydantic
* Google Gemini
* `google-genai`
* Multimodal embeddings
* Cosine similarity
* Pytest
* Git/GitHub

## Limitations

This is a backend capstone implementation rather than a production-scale image platform.

Current limitations include:

* The image library is currently file-based rather than persisted in PostgreSQL.
* Image embeddings are stored in a JSON file.
* The similarity threshold is provisional and requires more evaluation data for robust tuning.
* The current evaluation set contains only 10 posts.
* Vision metadata is unavailable for some dataset images because of Gemini API quota/rate-limit failures during batch processing.
* The metadata guard currently uses literal subject/category matching in the blog text.
* There is no frontend.
* There is no authentication system.
* There is no dedicated vector database.
* There is no model training or fine-tuning.

## Planned Improvements

The original design includes several extensions for a more complete production-style system:

* PostgreSQL persistence for images, vectors, posts, suggestions, reviews, and AI cost logs.
* Human review and approval/rejection endpoints.
* Persistent match suggestions.
* More robust metadata-aware matching.
* Larger and more diverse evaluation datasets.
* Threshold tuning based on evaluation results.
* Cost and usage tracking.
* More comprehensive mismatch and edge-case evaluation.
* Architecture and evidence documentation.

## Design Goals

The project intentionally prioritizes correctness and safe failure over simply returning an answer.

A high similarity score alone is not treated as proof that an image is appropriate. The mismatch guard provides a second layer of validation and allows the system to reject a candidate when the available evidence is insufficient.

The goal is a small, testable, evidence-backed backend that behaves correctly when the obvious answer is wrong.
