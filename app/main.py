from fastapi import FastAPI

from app.config import settings
from app.routes.image_matching import router as image_matching_router


app = FastAPI(
    title=settings.app_name,
    description="Backend service for understanding images and matching them to blog posts.",
    version="0.1.0",
)


app.include_router(image_matching_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}