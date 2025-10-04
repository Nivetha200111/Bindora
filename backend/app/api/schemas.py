"""
Pydantic schemas for API request/response models

Defines the structure of data exchanged between frontend and backend.
"""
from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
import structlog

logger = structlog.get_logger()


class SearchRequest(BaseModel):
    """Request schema for drug search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Disease name, gene symbol, or protein sequence")
    query_type: Literal["disease", "gene", "sequence"] = Field("gene", description="Type of query")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results to return")

    class Config:
        schema_extra = {
            "example": {
                "query": "BRCA1",
                "query_type": "gene",
                "max_results": 20
            }
        }


class DrugResult(BaseModel):
    """Schema for drug result in search response"""
    chembl_id: str = Field(..., description="ChEMBL ID")
    name: Optional[str] = Field(None, description="Drug name")
    smiles: str = Field(..., description="SMILES notation")
    binding_score: float = Field(..., ge=0, le=100, description="Predicted binding score (0-100)")
    molecular_weight: float = Field(..., description="Molecular weight in Da")
    logp: float = Field(..., description="LogP value (lipophilicity)")
    hbd: int = Field(..., description="Number of hydrogen bond donors")
    hba: int = Field(..., description="Number of hydrogen bond acceptors")
    tpsa: float = Field(..., description="Topological polar surface area")
    is_drug_like: bool = Field(..., description="Passes Lipinski's Rule of Five")
    clinical_phase: int = Field(..., ge=0, le=4, description="Clinical phase (0=preclinical, 4=approved)")
    target_protein: Optional[str] = Field(None, description="Target protein sequence (truncated)")
    num_targets_tested: Optional[int] = Field(None, description="Number of target proteins tested")

    class Config:
        schema_extra = {
            "example": {
                "chembl_id": "CHEMBL25",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "binding_score": 85.5,
                "molecular_weight": 180.16,
                "logp": 1.19,
                "hbd": 1,
                "hba": 4,
                "tpsa": 63.6,
                "is_drug_like": True,
                "clinical_phase": 4,
                "target_protein": "MKTIIALSYIFCLVFA...",
                "num_targets_tested": 1
            }
        }


class SearchResponse(BaseModel):
    """Response schema for drug search"""
    results: List[DrugResult] = Field(..., description="List of drug results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
    query_type: str = Field(..., description="Type of query")
    search_time: Optional[float] = Field(None, description="Search execution time in seconds")
    resolved_targets: Optional[int] = Field(None, description="Number of protein targets resolved")

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "chembl_id": "CHEMBL25",
                        "name": "Aspirin",
                        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                        "binding_score": 85.5,
                        "molecular_weight": 180.16,
                        "logp": 1.19,
                        "hbd": 1,
                        "hba": 4,
                        "tpsa": 63.6,
                        "is_drug_like": True,
                        "clinical_phase": 4
                    }
                ],
                "total": 1,
                "query": "BRCA1",
                "query_type": "gene",
                "search_time": 2.3,
                "resolved_targets": 1
            }
        }


class ClinicalTrial(BaseModel):
    """Schema for clinical trial information"""
    nct_id: str = Field(..., description="ClinicalTrials.gov ID")
    title: str = Field(..., description="Trial title")
    phase: str = Field(..., description="Clinical phase")
    status: str = Field(..., description="Trial status")
    start_date: Optional[str] = Field(None, description="Trial start date")
    completion_date: Optional[str] = Field(None, description="Trial completion date")

    class Config:
        schema_extra = {
            "example": {
                "nct_id": "NCT00000123",
                "title": "Aspirin for Pain Management",
                "phase": "Phase 4",
                "status": "Completed",
                "start_date": "2020-01-01",
                "completion_date": "2022-12-31"
            }
        }


class DrugDetailResponse(BaseModel):
    """Detailed drug information response"""
    chembl_id: str = Field(..., description="ChEMBL ID")
    name: Optional[str] = Field(None, description="Drug name")
    smiles: str = Field(..., description="SMILES notation")
    description: Optional[str] = Field(None, description="Drug description")
    inchi_key: Optional[str] = Field(None, description="InChI key")
    molecular_properties: Dict[str, Union[float, int, bool]] = Field(default_factory=dict, description="Molecular properties")
    similar_drugs: List[str] = Field(default_factory=list, description="Similar drug ChEMBL IDs")
    clinical_trials: List[ClinicalTrial] = Field(default_factory=list, description="Clinical trial information")
    is_drug_like: bool = Field(..., description="Passes Lipinski's Rule of Five")
    clinical_phase: int = Field(..., ge=0, le=4, description="Clinical phase")
    drugbank_id: Optional[str] = Field(None, description="DrugBank ID")
    pubchem_cid: Optional[str] = Field(None, description="PubChem CID")
    atc_codes: List[str] = Field(default_factory=list, description="ATC classification codes")
    indications: List[str] = Field(default_factory=list, description="Clinical indications")
    mechanism_of_action: Optional[str] = Field(None, description="Mechanism of action")
    metabolism: Optional[str] = Field(None, description="Metabolic information")
    toxicity: Optional[str] = Field(None, description="Toxicity information")
    half_life: Optional[str] = Field(None, description="Half-life information")
    bioavailability: Optional[str] = Field(None, description="Bioavailability information")

    class Config:
        schema_extra = {
            "example": {
                "chembl_id": "CHEMBL25",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "description": "Acetylsalicylic acid, commonly known as aspirin, is an analgesic and anti-inflammatory drug.",
                "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "molecular_properties": {
                    "molecular_weight": 180.16,
                    "logp": 1.19,
                    "hbd": 1,
                    "hba": 4,
                    "tpsa": 63.6,
                    "rotatable_bonds": 3,
                    "aromatic_rings": 1,
                    "is_drug_like": True,
                    "molecular_weight_ok": True,
                    "logp_ok": True,
                    "hbd_ok": True,
                    "hba_ok": True,
                    "passes_lipinski": True
                },
                "similar_drugs": ["CHEMBL26", "CHEMBL27"],
                "clinical_trials": [
                    {
                        "nct_id": "NCT00000123",
                        "title": "Aspirin for Pain Management",
                        "phase": "Phase 4",
                        "status": "Completed"
                    }
                ],
                "is_drug_like": True,
                "clinical_phase": 4,
                "atc_codes": ["N02BA01"],
                "indications": ["Pain", "Inflammation"]
            }
        }


class TargetInfo(BaseModel):
    """Schema for protein target information"""
    uniprot_id: str = Field(..., description="UniProt accession ID")
    name: Optional[str] = Field(None, description="Protein name")
    gene_name: Optional[str] = Field(None, description="Gene name")
    organism: Optional[str] = Field(None, description="Organism")
    sequence: Optional[str] = Field(None, description="Amino acid sequence")
    sequence_length: int = Field(..., description="Sequence length")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight")
    function: Optional[str] = Field(None, description="Biological function")
    subcellular_location: Optional[str] = Field(None, description="Subcellular location")
    tissue_specificity: Optional[str] = Field(None, description="Tissue specificity")
    pathway: Optional[str] = Field(None, description="Biological pathway")
    disease_associations: List[str] = Field(default_factory=list, description="Associated diseases")
    drug_interactions: List[str] = Field(default_factory=list, description="Known drug interactions")
    structure_available: bool = Field(..., description="Whether 3D structure is available")
    embedding_available: bool = Field(..., description="Whether embedding is available")
    embedding_dimensions: int = Field(..., description="Embedding vector dimensions")

    class Config:
        schema_extra = {
            "example": {
                "uniprot_id": "P38398",
                "name": "Breast cancer type 1 susceptibility protein",
                "gene_name": "BRCA1",
                "organism": "Homo sapiens",
                "sequence_length": 1863,
                "function": "Tumor suppressor involved in DNA repair",
                "disease_associations": ["Breast cancer", "Ovarian cancer"],
                "structure_available": False,
                "embedding_available": True,
                "embedding_dimensions": 1280
            }
        }


class StatsResponse(BaseModel):
    """Platform statistics response"""
    total_drugs: int = Field(..., description="Total drugs in database")
    total_targets: int = Field(..., description="Total protein targets")
    predictions_made: int = Field(..., description="Total predictions made")
    avg_prediction_time: float = Field(..., description="Average prediction time in seconds")
    cache_size: int = Field(..., description="Number of cached embeddings")
    model_status: str = Field(..., description="Status of AI models")

    class Config:
        schema_extra = {
            "example": {
                "total_drugs": 3247,
                "total_targets": 20189,
                "predictions_made": 156789,
                "avg_prediction_time": 1.23,
                "cache_size": 45,
                "model_status": "loaded"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    models_loaded: bool = Field(..., description="Whether AI models are loaded")
    database_connected: bool = Field(..., description="Database connection status")
    cache_available: bool = Field(..., description="Cache availability")
    version: str = Field(..., description="API version")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "models_loaded": True,
                "database_connected": True,
                "cache_available": True,
                "version": "1.0.0"
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: Optional[str] = Field(None, description="Error timestamp")

    class Config:
        schema_extra = {
            "example": {
                "detail": "Drug not found: INVALID123",
                "error_code": "DRUG_NOT_FOUND",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# Response models for specific endpoints
SearchDrugsResponse = SearchResponse
GetDrugDetailsResponse = DrugDetailResponse
GetTargetInfoResponse = TargetInfo
GetStatsResponse = StatsResponse
HealthCheckResponse = HealthResponse
