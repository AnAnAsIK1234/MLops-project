import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "ml-orm-service")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000",
    ).split(",")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    OLLAMA_TIMEOUT_SEC: float = float(os.getenv("OLLAMA_TIMEOUT_SEC", "180"))
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))


settings = Settings()
