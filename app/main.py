from fastapi import FastAPI

from app.config import settings
from app.routes.evaluation import router as evaluation_router
from app.routes.image_matching import router as image_matching_router
from app.routes.review import router as review_router


app = FastAPI(
    title=settings.app_name,
    description="Backend service for understanding images and matching them to blog posts.",
    version="0.1.0",
)


app.include_router(image_matching_router)
app.include_router(evaluation_router)
app.include_router(review_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}