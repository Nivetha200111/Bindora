"""
Configuration settings for Bindora API
"""
import os
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Bindora API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered drug discovery platform for drug-target interaction prediction"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database Configuration
    DATABASE_URL: str = "postgresql://bindora:password@localhost/bindora"

    # AI Model Configuration
    PROTEIN_MODEL: str = "facebook/esm2_t33_650M_UR50D"
    DEVICE: str = "auto"  # auto, cuda, cpu, mps
    MODEL_CACHE_DIR: str = "./models"
    EMBEDDING_DIMENSIONS: int = 1280  # ESM-2 embedding size

    # Drug Encoding Configuration
    FINGERPRINT_SIZE: int = 2048  # Morgan fingerprint bits
    FINGERPRINT_RADIUS: int = 2   # Morgan fingerprint radius

    # Caching Configuration
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_EMBEDDINGS: bool = True

    # Performance Configuration
    MAX_RESULTS: int = 100
    BATCH_SIZE: int = 32
    PREDICTION_TIMEOUT: int = 30  # seconds

    # Data Configuration
    DATA_DIR: str = "./data"
    MAX_SEQUENCE_LENGTH: int = 1024  # ESM-2 max input length

    # External API Configuration
    CHEMBL_API_URL: str = "https://www.ebi.ac.uk/chembl/api/data"
    UNIPROT_API_URL: str = "https://rest.uniprot.org"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def device(self) -> str:
        """Determine the best available device"""
        if self.DEVICE != "auto":
            return self.DEVICE

        # Try CUDA first
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass

        # Try MPS for Apple Silicon
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
        except (ImportError, AttributeError):
            pass

        # Fall back to CPU
        return "cpu"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create settings instance
settings = get_settings()
