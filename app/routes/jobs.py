from fastapi import APIRouter, BackgroundTasks

from app.jobs.image_batch import run_batch


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


@router.post("/image-batch")
def start_image_batch(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_batch)

    return {
        "status": "started",
        "job": "image_batch",
    }