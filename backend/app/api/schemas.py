from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

class SearchRequest(BaseModel):
    """Request schema for drug search"""
    query: str = Field(..., description="Disease name, gene symbol, or protein sequence")
    query_type: Literal["disease", "gene", "sequence"] = Field("gene", description="Type of query")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results to return")
    
    class Config:
        json_schema_extra = {
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
    clinical_phase: int = Field(..., ge=0, le=4, description="Clinical phase (0-4, 4=approved)")
    
    class Config:
        json_schema_extra = {
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
                "clinical_phase": 4
            }
        }

class SearchResponse(BaseModel):
    """Response schema for drug search"""
    results: List[DrugResult] = Field(..., description="List of drug results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
    query_type: str = Field(..., description="Type of query")

class ClinicalTrial(BaseModel):
    """Schema for clinical trial information"""
    nct_id: str = Field(..., description="ClinicalTrials.gov ID")
    title: str = Field(..., description="Trial title")
    phase: str = Field(..., description="Clinical phase")
    status: str = Field(..., description="Trial status")

class DrugDetailResponse(DrugResult):
    """Detailed drug information response"""
    description: Optional[str] = Field(None, description="Drug description")
    inchi_key: Optional[str] = Field(None, description="InChI key")
    properties: Dict[str, float] = Field(default_factory=dict, description="Additional molecular properties")
    similar_drugs: List[str] = Field(default_factory=list, description="Similar drug ChEMBL IDs")
    clinical_trials: List[ClinicalTrial] = Field(default_factory=list, description="Clinical trial information")
    
    class Config:
        json_schema_extra = {
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
                "description": "Acetylsalicylic acid, commonly known as aspirin",
                "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "properties": {
                    "num_rotatable_bonds": 3,
                    "num_aromatic_rings": 1
                },
                "similar_drugs": ["CHEMBL26", "CHEMBL27"],
                "clinical_trials": []
            }
        }

class StatsResponse(BaseModel):
    """Platform statistics response"""
    total_drugs: int = Field(..., description="Total drugs in database")
    total_targets: int = Field(..., description="Total protein targets")
    predictions_made: int = Field(..., description="Total predictions made")

