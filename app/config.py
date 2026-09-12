from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Image Understanding & Content Matching Engine"
    debug: bool = True

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""
    embedding_model: str = "gemini-embedding-2-preview"
    database_url: str = ""
    ai_budget_limit: float = 1.0
    ai_call_budget_estimate: float = 0.01

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()