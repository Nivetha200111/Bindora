"""
Search Service - Business Logic for Drug Search

TODO: YOU NEED TO IMPLEMENT THIS!

This is the main business logic layer that orchestrates the search workflow:

Workflow:
1. Parse and validate query
2. Convert query to protein sequence:
   - If disease -> find related genes -> get protein sequences
   - If gene -> fetch protein sequence from UniProt
   - If sequence -> use directly
3. Load drug database (ChEMBL approved drugs)
4. Use BindingPredictor to score all drugs against target
5. Filter and sort results
6. Return top N drugs

For MVP: Keep it simple with hardcoded data
For V2: Integrate with real databases (PostgreSQL + ChEMBL API)
"""

from typing import List, Dict
from app.api.schemas import DrugResult
from app.models.protein_encoder import ProteinEncoder
from app.models.drug_encoder import DrugEncoder
from app.models.binding_predictor import BindingPredictor
from app.utils.uniprot_client import fetch_protein_sequence
from app.utils.chembl_client import fetch_approved_drugs

# Initialize models (lazy loading)
_protein_encoder = None
_drug_encoder = None
_binding_predictor = None

def get_models():
    """Lazy load AI models"""
    global _protein_encoder, _drug_encoder, _binding_predictor
    
    if _protein_encoder is None:
        print("🔄 Loading AI models...")
        _protein_encoder = ProteinEncoder()
        _drug_encoder = DrugEncoder()
        _binding_predictor = BindingPredictor(_protein_encoder, _drug_encoder)
        print("✅ Models loaded")
    
    return _protein_encoder, _drug_encoder, _binding_predictor


async def search_drugs_for_target(
    query: str,
    query_type: str,
    max_results: int = 20
) -> List[DrugResult]:
    """
    Main search function - finds drugs for a given target
    
    Args:
        query: User query (disease name, gene symbol, or sequence)
        query_type: Type of query ("disease", "gene", "sequence")
        max_results: Maximum number of results to return
    
    Returns:
        List of DrugResult objects ranked by binding score
    
    TODO: Implement the complete workflow
    """
    print(f"🔍 Search request: query='{query[:50]}', type={query_type}, max={max_results}")
    
    # Step 1: Get protein sequence based on query type
    protein_sequence = await _resolve_protein_sequence(query, query_type)
    
    if not protein_sequence:
        raise ValueError(f"Could not resolve protein sequence for query: {query}")
    
    # Step 2: Load drug candidates
    drug_candidates = await _load_drug_candidates()
    
    # Step 3: Load models and predict binding
    protein_encoder, drug_encoder, binding_predictor = get_models()
    
    # Step 4: Rank drugs by binding score
    ranked_drugs = binding_predictor.rank_drugs(protein_sequence, drug_candidates)
    
    # Step 5: Convert to DrugResult schema and return top N
    results = []
    for drug_dict, score in ranked_drugs[:max_results]:
        # Calculate molecular properties
        descriptors = drug_encoder.encode_descriptors(drug_dict['smiles'])
        is_drug_like = drug_encoder.is_drug_like(drug_dict['smiles'])
        
        result = DrugResult(
            chembl_id=drug_dict['chembl_id'],
            name=drug_dict.get('name'),
            smiles=drug_dict['smiles'],
            binding_score=round(score, 2),
            molecular_weight=round(descriptors['molecular_weight'], 2),
            logp=round(descriptors['logp'], 2),
            hbd=descriptors['hbd'],
            hba=descriptors['hba'],
            tpsa=round(descriptors['tpsa'], 2),
            is_drug_like=is_drug_like,
            clinical_phase=drug_dict.get('clinical_phase', 4)
        )
        results.append(result)
    
    return results


async def _resolve_protein_sequence(query: str, query_type: str) -> str:
    """
    Convert query to protein sequence
    
    TODO: Implement query resolution logic
    
    - For "gene": Call UniProt API to get sequence
    - For "disease": Map to genes, then get sequences
    - For "sequence": Validate and return
    """
    print(f"⚠️  _resolve_protein_sequence() NOT FULLY IMPLEMENTED")
    
    if query_type == "sequence":
        # Validate amino acid sequence
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        if not all(c.upper() in valid_aa for c in query.replace(" ", "")):
            raise ValueError("Invalid amino acid sequence")
        return query.upper().replace(" ", "")
    
    elif query_type == "gene":
        # TODO: Implement UniProt lookup
        print(f"   TODO: Fetch protein sequence from UniProt for gene: {query}")
        # For now, use a placeholder sequence
        protein_seq = await fetch_protein_sequence(query)
        return protein_seq
    
    elif query_type == "disease":
        # TODO: Implement disease -> gene -> protein mapping
        print(f"   TODO: Map disease '{query}' to genes and proteins")
        # For now, use a placeholder
        # In V2: Use disease ontology database
        raise NotImplementedError("Disease search not yet implemented. Try using a gene symbol instead.")
    
    else:
        raise ValueError(f"Unknown query type: {query_type}")


async def _load_drug_candidates() -> List[Dict]:
    """
    Load drug database
    
    TODO: Implement database loading
    
    For MVP: Return hardcoded sample drugs
    For V2: Load from PostgreSQL or ChEMBL API
    """
    print(f"⚠️  _load_drug_candidates() NOT FULLY IMPLEMENTED")
    print(f"   TODO: Load drugs from database")
    
    # For now, return sample drugs
    # In production, this would query ChEMBL or your database
    drugs = await fetch_approved_drugs(limit=100)
    
    return drugs

