from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Image Understanding & Content Matching Engine"
    debug: bool = True

    llm_provider: str = "openrouter"
    llm_model: str = "openrouter/free"
    llm_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()