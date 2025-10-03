from fastapi import APIRouter, HTTPException, status
from app.api.schemas import (
    SearchRequest, 
    SearchResponse, 
    DrugDetailResponse,
    StatsResponse
)
from app.services.search_service import search_drugs_for_target
from app.services.drug_service import get_drug_details

router = APIRouter()

@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(request: SearchRequest):
    """
    Search for drugs that bind to a target
    
    Accepts three types of queries:
    - **Disease name**: e.g., "Alzheimer's disease"
    - **Gene symbol**: e.g., "BRCA1"
    - **Protein sequence**: Full amino acid sequence
    
    Returns a list of drugs ranked by predicted binding affinity.
    """
    try:
        results = await search_drugs_for_target(
            query=request.query,
            query_type=request.query_type,
            max_results=request.max_results
        )
        return SearchResponse(
            results=results, 
            total=len(results),
            query=request.query,
            query_type=request.query_type
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/drug/{chembl_id}", response_model=DrugDetailResponse, status_code=status.HTTP_200_OK)
async def get_drug(chembl_id: str):
    """
    Get detailed information about a specific drug
    
    Returns comprehensive drug information including:
    - Molecular properties
    - Clinical trial data
    - Similar drugs
    - Binding predictions
    """
    try:
        drug_details = await get_drug_details(chembl_id)
        return drug_details
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug not found: {chembl_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drug details: {str(e)}"
        )

@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def get_stats():
    """
    Get platform statistics
    
    Returns overall statistics about the drug discovery platform
    including total drugs, targets, and predictions made.
    """
    # TODO: Replace with actual database counts
    return StatsResponse(
        total_drugs=3000,
        total_targets=20000,
        predictions_made=150000
    )

