# BUILDLOG



## Purpose



This document records how AI tools were used during the development of the

AI Image Understanding \& Content Matching Engine, including where AI helped,

where suggestions were incorrect or incomplete, and what was changed as a

result.



## AI Assistance



AI assistance was used throughout development for:



- Project architecture and implementation planning

- FastAPI route and service structure

- Pydantic schema design and validation

- Gemini Vision integration

- Gemini image and text embedding integration

- Cosine similarity implementation

- Mismatch guard design

- Evaluation and testing strategy

- Review API implementation

- README and EVIDENCE.md documentation

- Debugging Python, dependency, Git, and API issues



All generated suggestions were reviewed and tested locally before being

accepted into the project.



## Development Decisions and Corrections



### Project setup



AI guidance helped structure the project into separate layers for:



- API routes

- Pydantic schemas

- Services and business logic

- Background jobs

- Dataset and evaluation data



The project was developed locally on Windows using a Python virtual

environment. Docker and WSL were not used for the local development setup.



### Dataset



The target dataset was expanded to 50 images across 10 categories:



- fox

- wolf

- cat

- dog

- bird

- horse

- motorcycle

- car

- mountain

- plain



The dataset contains five images per category.



### Vision processing



Gemini Vision was used to generate structured image metadata. A Pydantic

schema was created to validate fields such as subject, category, attributes,

caption, and confidence.



During processing, Gemini quota limits caused some requests to fail with

HTTP 429 errors. These failures were retained in the dataset rather than

being presented as successful classifications.



### Embeddings



Gemini multimodal embeddings were added for image and text representations.

The embedding pipeline produces 768-dimensional vectors for the image

library, while blog posts are embedded using the same embedding service.



### Matching and mismatch guard



AI assistance initially suggested a simple similarity-based matching flow.

This was extended with a mismatch guard using:



1. cosine similarity

2. image metadata when available

3. confidence thresholds

4. subject/category checks against the blog text



The similarity threshold was treated as provisional and evaluated against the

test dataset rather than being presented as a universally correct value.



### Evaluation



A 10-post evaluation dataset was created, covering the supported categories.

The final evaluation produced 100% top-1 precision on these 10 cases.



A forced wolf image was also tested against a fox-related post. The mismatch

guard rejected the candidate because its similarity score was below the

configured threshold.



### Review API

A review API was added with approve/reject decisions and optional feedback.

Review decisions are persisted in PostgreSQL so they remain available after
the application restarts.

