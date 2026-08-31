from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration (ADR-001: config lives in one place, never scattered
    os.environ calls throughout the codebase).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://raguser:ragpass@postgres:5432/ragplatform"

    # ChromaDB
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "rag_chunks"

    # Embeddings — AI-12: this value MUST stay identical between ingestion and query.
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 2048

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # RAG tuning (ADR-004)
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_top_k: int = 5
    low_confidence_threshold: float = 0.50  # AI-05: below this, fall back to related-docs mode


settings = Settings()
