from fastapi import APIRouter

from app.services.evaluation_service import EvaluationService


router = APIRouter(
    prefix="/api/v1",
    tags=["Evaluation"],
)


service = EvaluationService()


@router.get("/evaluation")
def run_evaluation():
    return service.evaluate()