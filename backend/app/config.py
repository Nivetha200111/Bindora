from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/drugmatcher"
    
    # Models
    PROTEIN_MODEL: str = "facebook/esm2_t33_650M_UR50D"
    DRUG_MODEL: str = "seyonec/ChemBERTa-zinc-base-v1"
    
    # Paths
    DATA_DIR: str = "./data"
    MODEL_CACHE_DIR: str = "./models"
    
    # External APIs
    CHEMBL_API_URL: str = "https://www.ebi.ac.uk/chembl/api/data"
    UNIPROT_API_URL: str = "https://rest.uniprot.org"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()

