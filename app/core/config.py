# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration for Catsi.
    Pydantic will read these from environment variables
    or from a .env file (if present).
    """

    # ---- App ----
    APP_NAME: str = "Catsi API"
    DEBUG: bool = False

    # ---- Database ----
    DATABASE_URL: str = "sqlite+aiosqlite:///./catsi.db"
    # This SQLite URL will create a file 'catsi.db' in the project root.

    # ---- JWT ----
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ---- Ollama ----
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    CHAT_MODEL: str = "llama3.1:8b "               # default chat model
    EMBEDDING_MODEL: str = "nomic-embed-text" # default embedding model

    # ---- ChromaDB ----
    CHROMA_PERSIST_DIR: str = "./chroma_data"   # where vectors are stored

    # This tells pydantic-settings to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    CHROMA_COLLECTION_NAME: str = "catsi_documents"
    #
    # LANGSMITH_API_KEY: str = "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"
    # LANGSMITH_TRACING: str = 'true'
    # LANGSMITH_ENDPOINT: str  = "https://api.smith.langchain.com"
    # LANGSMITH_PROJECT: str = "Catsi"

# Create a single instance that we can import anywhere
settings = Settings()