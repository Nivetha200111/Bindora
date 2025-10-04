"""
API routes for drug-target interaction platform

Endpoints:
- POST /api/search - Search for drugs that bind to a target
- GET /api/drug/{chembl_id} - Get detailed drug information
- GET /api/target/{uniprot_id} - Get protein target information
- GET /api/stats - Get platform statistics
- GET /health - Health check endpoint
"""
import time
from typing import Dict, List, Optional
import structlog
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from app.api.schemas import (
    SearchRequest, SearchResponse, DrugDetailResponse, TargetInfo,
    StatsResponse, HealthResponse, ErrorResponse
)
from app.dependencies import (
    get_binding_predictor, get_drug_encoder, get_protein_encoder,
    get_db, get_redis, get_logger
)
from app.services.search_service import SearchService
from app.services.drug_service import DrugService
from app.services.target_service import TargetService
from app.models.binding_predictor import BindingPredictor
from app.models.drug_encoder import DrugEncoder
from app.models.protein_encoder import ProteinEncoder

logger = structlog.get_logger()

# Create router
router = APIRouter()

# Initialize services (will be overridden by dependencies in production)
_search_service = None
_drug_service = None
_target_service = None


def get_search_service(
    binding_predictor: BindingPredictor = Depends(get_binding_predictor)
) -> SearchService:
    """Get or create search service"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService(binding_predictor)
    return _search_service


def get_drug_service(
    drug_encoder: DrugEncoder = Depends(get_drug_encoder)
) -> DrugService:
    """Get or create drug service"""
    global _drug_service
    if _drug_service is None:
        _drug_service = DrugService(drug_encoder)
    return _drug_service


def get_target_service(
    protein_encoder: ProteinEncoder = Depends(get_protein_encoder)
) -> TargetService:
    """Get or create target service"""
    global _target_service
    if _target_service is None:
        _target_service = TargetService(protein_encoder)
    return _target_service


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_drugs(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
    background_tasks: BackgroundTasks = None
):
    """
    Search for drugs that bind to a target

    Accepts three types of queries:
    - **Disease name**: e.g., "Alzheimer's disease"
    - **Gene symbol**: e.g., "BRCA1"
    - **Protein sequence**: Full amino acid sequence

    Returns a list of drugs ranked by predicted binding affinity.
    """
    start_time = time.time()

    try:
        logger.info(
            "Drug search request",
            query=request.query,
            query_type=request.query_type,
            max_results=request.max_results
        )

        # Perform search
        results = await search_service.search_drugs_for_target(
            query=request.query,
            query_type=request.query_type,
            max_results=request.max_results
        )

        search_time = time.time() - start_time

        # Log successful search
        logger.info(
            "Drug search completed",
            query=request.query,
            results_count=len(results),
            search_time=f"{search_time".3f"}s"
        )

        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            query_type=request.query_type,
            search_time=search_time,
            resolved_targets=search_service.get_cache_size()
        )

    except ValueError as e:
        logger.warning("Search validation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/drug/{chembl_id}", response_model=DrugDetailResponse, status_code=status.HTTP_200_OK)
async def get_drug_details(
    chembl_id: str,
    drug_service: DrugService = Depends(get_drug_service)
):
    """
    Get detailed information about a specific drug

    Returns comprehensive drug information including:
    - Molecular properties
    - Clinical trial data
    - Similar drugs
    - Binding predictions
    """
    try:
        logger.info("Drug details request", chembl_id=chembl_id)

        drug_details = await drug_service.get_drug_details(chembl_id)

        logger.info(
            "Drug details retrieved",
            chembl_id=chembl_id,
            name=drug_details.get("name")
        )

        return drug_details

    except ValueError as e:
        logger.warning("Drug not found", chembl_id=chembl_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug not found: {chembl_id}"
        )
    except Exception as e:
        logger.error("Drug details retrieval failed", chembl_id=chembl_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drug details: {str(e)}"
        )


@router.get("/target/{uniprot_id}", response_model=TargetInfo, status_code=status.HTTP_200_OK)
async def get_target_info(
    uniprot_id: str,
    target_service: TargetService = Depends(get_target_service)
):
    """
    Get information about a protein target

    Returns comprehensive protein target information including:
    - Sequence and structure data
    - Biological function
    - Disease associations
    - Known drug interactions
    """
    try:
        logger.info("Target info request", uniprot_id=uniprot_id)

        target_info = await target_service.get_target_info(uniprot_id)

        logger.info(
            "Target info retrieved",
            uniprot_id=uniprot_id,
            name=target_info.get("name")
        )

        return target_info

    except ValueError as e:
        logger.warning("Target not found", uniprot_id=uniprot_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target not found: {uniprot_id}"
        )
    except Exception as e:
        logger.error("Target info retrieval failed", uniprot_id=uniprot_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve target information: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def get_platform_stats(
    search_service: SearchService = Depends(get_search_service),
    drug_service: DrugService = Depends(get_drug_service),
    target_service: TargetService = Depends(get_target_service)
):
    """
    Get platform statistics

    Returns overall statistics about the drug discovery platform
    including total drugs, targets, predictions made, and system status.
    """
    try:
        # TODO: Replace with actual database counts
        stats = StatsResponse(
            total_drugs=3247,  # Would query drug database
            total_targets=20189,  # Would query target database
            predictions_made=156789,  # Would query prediction log
            avg_prediction_time=1.23,  # Would calculate from logs
            cache_size=search_service.get_cache_size() + target_service.get_cache_size(),
            model_status="loaded"  # Would check model health
        )

        logger.debug("Platform stats retrieved", stats=stats.dict())

        return stats

    except Exception as e:
        logger.error("Stats retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve platform statistics: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(
    db_session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """
    Health check endpoint

    Returns the current health status of the service including
    model availability, database connectivity, and cache status.
    """
    start_time = time.time()

    try:
        # Check database connectivity
        db_healthy = True
        try:
            # Simple query to test connection
            await db_session.execute("SELECT 1")
        except Exception as e:
            logger.warning("Database health check failed", error=str(e))
            db_healthy = False

        # Check Redis connectivity
        cache_healthy = redis_client is not None
        if cache_healthy:
            try:
                await redis_client.ping()
            except Exception as e:
                logger.warning("Redis health check failed", error=str(e))
                cache_healthy = False

        # Check model availability
        models_healthy = True
        try:
            # Try to access encoders (this will trigger lazy loading if needed)
            protein_encoder = get_protein_encoder()
            drug_encoder = get_drug_encoder()
            binding_predictor = get_binding_predictor()

            # Test with a simple prediction
            test_score = binding_predictor.predict_binding(
                "MKTIIALSYIFCLVFA",  # Short test sequence
                "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
            )
            if not (0 <= test_score <= 100):
                models_healthy = False

        except Exception as e:
            logger.warning("Model health check failed", error=str(e))
            models_healthy = False

        # Overall status
        overall_status = "healthy" if (db_healthy and models_healthy) else "degraded"

        health_time = time.time() - start_time

        health_response = HealthResponse(
            status=overall_status,
            models_loaded=models_healthy,
            database_connected=db_healthy,
            cache_available=cache_healthy,
            version="1.0.0"
        )

        logger.info(
            "Health check completed",
            status=overall_status,
            health_check_time=f"{health_time".3f"}s"
        )

        return health_response

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/admin/cache/clear", status_code=status.HTTP_200_OK)
async def clear_cache(
    search_service: SearchService = Depends(get_search_service),
    target_service: TargetService = Depends(get_target_service)
):
    """
    Clear internal caches (admin endpoint)

    Clears protein embeddings and target information caches.
    Useful for memory management or after model updates.
    """
    try:
        # Clear all caches
        search_service.clear_cache()
        target_service.clear_cache()

        # Also clear binding predictor cache if it exists
        try:
            binding_predictor = get_binding_predictor()
            binding_predictor.clear_cache()
        except Exception:
            pass

        logger.info("All caches cleared")

        return {"message": "All caches cleared successfully"}

    except Exception as e:
        logger.error("Cache clear failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache clear failed: {str(e)}"
        )


@router.get("/admin/info", status_code=status.HTTP_200_OK)
async def get_system_info():
    """
    Get detailed system information (admin endpoint)

    Returns information about loaded models, cache sizes,
    and system configuration.
    """
    try:
        # Get service instances
        search_service = get_search_service()
        drug_service = get_drug_service()
        target_service = get_target_service()

        # Get model instances
        protein_encoder = get_protein_encoder()
        drug_encoder = get_drug_encoder()
        binding_predictor = get_binding_predictor()

        system_info = {
            "models": {
                "protein_encoder": {
                    "model_name": protein_encoder.model_name,
                    "device": protein_encoder.device,
                    "embedding_dim": protein_encoder.get_embedding_dimension()
                },
                "drug_encoder": {
                    "fingerprint_size": drug_encoder.get_fingerprint_size(),
                    "fingerprint_radius": drug_encoder.fingerprint_radius,
                    "property_count": len(drug_encoder.get_property_names())
                },
                "binding_predictor": {
                    "similarity_threshold": binding_predictor.similarity_threshold,
                    "scale_factor": binding_predictor.scale_factor
                }
            },
            "caches": {
                "protein_embeddings": search_service.get_cache_size(),
                "target_info": target_service.get_cache_size(),
                "binding_predictor": binding_predictor.get_cache_size()
            },
            "configuration": {
                "max_results": search_service.max_results,
                "min_binding_score": search_service.min_binding_score,
                "device": protein_encoder.device
            }
        }

        logger.debug("System info retrieved")

        return system_info

    except Exception as e:
        logger.error("System info retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System info retrieval failed: {str(e)}"
        )
