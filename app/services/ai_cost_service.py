from sqlalchemy import func, select

from app.config import settings
from app.database import SessionLocal
from app.models import AICall


class AICostService:
    def record_call(
        self,
        operation: str,
        provider: str,
        model: str,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        estimated_cost: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        with SessionLocal() as db:
            db.add(
                AICall(
                    operation=operation,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=estimated_cost,
                    success=success,
                    error=error,
                )
            )
            db.commit()

    def get_total_cost(self) -> float:
        with SessionLocal() as db:
            total = db.scalar(
                select(func.coalesce(func.sum(AICall.estimated_cost), 0.0))
            )
            return float(total)

    def check_budget(self, estimated_cost: float) -> bool:
        current_cost = self.get_total_cost()
        return current_cost + estimated_cost <= settings.ai_budget_limit

    def estimate_cost(
        self,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> float:
        input_cost = (input_tokens or 0) * 0.75 / 1_000_000
        output_cost = (output_tokens or 0) * 3.75 / 1_000_000

        return input_cost + output_cost