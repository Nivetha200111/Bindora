"""
Target Service - Protein target information and operations

Provides information about protein targets including structure data,
known drug interactions, biological function, and related pathways.
"""
import time
from typing import Dict, List, Optional, Union
import structlog

logger = structlog.get_logger()

from app.models.protein_encoder import ProteinEncoder
from app.utils.uniprot_client import fetch_protein_info, search_proteins_by_disease


class TargetService:
    """
    Service for protein target information and operations

    Args:
        protein_encoder: Initialized ProteinEncoder instance
    """

    def __init__(self, protein_encoder: ProteinEncoder):
        self.protein_encoder = protein_encoder

        # Cache for protein information
        self._protein_info_cache: Dict[str, Dict] = {}

        logger.info("Target service initialized")

    async def get_target_info(self, uniprot_id: str) -> Dict[str, Union[str, float, int, List, Dict]]:
        """
        Get comprehensive information about a protein target

        Args:
            uniprot_id: UniProt accession ID

        Returns:
            Complete target information dictionary

        Raises:
            ValueError: If target not found
        """
        start_time = time.time()

        logger.info(f"Fetching target information", uniprot_id=uniprot_id)

        try:
            # Check cache first
            if uniprot_id in self._protein_info_cache:
                logger.debug("Returning cached target info", uniprot_id=uniprot_id)
                return self._protein_info_cache[uniprot_id]

            # Fetch from UniProt
            target_data = await fetch_protein_info(uniprot_id)

            if not target_data:
                raise ValueError(f"Target not found: {uniprot_id}")

            # Get protein sequence for encoding
            sequence = target_data.get("sequence", "")

            # Generate embedding if sequence available
            embedding = None
            if sequence:
                try:
                    embedding = self.protein_encoder.encode(sequence)
                except Exception as e:
                    logger.warning(f"Failed to encode protein {uniprot_id}: {e}")

            # Build comprehensive response
            target_info = {
                "uniprot_id": target_data.get("uniprot_id", uniprot_id),
                "name": target_data.get("name"),
                "gene_name": target_data.get("gene_name"),
                "organism": target_data.get("organism"),
                "sequence": sequence,
                "sequence_length": len(sequence) if sequence else 0,
                "molecular_weight": target_data.get("molecular_weight"),
                "function": target_data.get("function"),
                "subcellular_location": target_data.get("subcellular_location"),
                "tissue_specificity": target_data.get("tissue_specificity"),
                "pathway": target_data.get("pathway"),
                "disease_associations": target_data.get("disease_associations", []),
                "drug_interactions": target_data.get("drug_interactions", []),
                "structure_available": target_data.get("structure_available", False),
                "embedding_available": embedding is not None,
                "embedding_dimensions": len(embedding) if embedding is not None else 0,
                "go_terms": target_data.get("go_terms", {}),
                "interpro_domains": target_data.get("interpro_domains", []),
                "post_translational_modifications": target_data.get("post_translational_modifications", []),
                "expression_data": target_data.get("expression_data"),
                "references": target_data.get("references", [])
            }

            # Cache the result
            self._protein_info_cache[uniprot_id] = target_info

            info_time = time.time() - start_time

            logger.info(
                f"Retrieved target information",
                uniprot_id=uniprot_id,
                name=target_info.get("name"),
                retrieval_time=f"{info_time".2f"}s"
            )

            return target_info

        except Exception as e:
            logger.error(f"Failed to get target info for {uniprot_id}: {e}")
            raise ValueError(f"Target information retrieval failed: {e}")

    async def find_related_targets(self, uniprot_id: str, limit: int = 10) -> List[Dict]:
        """
        Find related protein targets based on sequence similarity

        Args:
            uniprot_id: UniProt ID of query protein
            limit: Maximum number of related targets to return

        Returns:
            List of related target dictionaries
        """
        try:
            # Get query protein embedding
            target_info = await self.get_target_info(uniprot_id)

            if not target_info.get("sequence"):
                logger.warning(f"No sequence available for target {uniprot_id}")
                return []

            query_embedding = self.protein_encoder.encode(target_info["sequence"])

            # TODO: Implement similarity search against protein database
            # For now, return empty list
            logger.info("Related target search not yet implemented")

            return []

        except Exception as e:
            logger.error(f"Failed to find related targets for {uniprot_id}: {e}")
            return []

    async def search_targets_by_disease(self, disease_name: str) -> List[Dict]:
        """
        Search for protein targets associated with a disease

        Args:
            disease_name: Name of the disease

        Returns:
            List of target dictionaries
        """
        try:
            # Use UniProt disease search
            targets = await search_proteins_by_disease(disease_name)

            # Convert to detailed target info
            detailed_targets = []

            for target in targets[:10]:  # Limit to top 10
                try:
                    target_info = await self.get_target_info(target.get("uniprot_id"))
                    detailed_targets.append(target_info)
                except Exception as e:
                    logger.warning(f"Failed to get details for target {target.get('uniprot_id')}: {e}")
                    continue

            logger.info(
                f"Found targets for disease",
                disease=disease_name,
                num_targets=len(detailed_targets)
            )

            return detailed_targets

        except Exception as e:
            logger.error(f"Disease target search failed: {e}")
            return []

    async def get_target_embedding(self, uniprot_id: str) -> Optional[List[float]]:
        """
        Get protein embedding vector for a target

        Args:
            uniprot_id: UniProt accession ID

        Returns:
            Embedding vector as list of floats, or None if unavailable
        """
        try:
            target_info = await self.get_target_info(uniprot_id)

            if not target_info.get("sequence"):
                return None

            embedding = self.protein_encoder.encode(target_info["sequence"])

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to get embedding for {uniprot_id}: {e}")
            return None

    def clear_cache(self):
        """Clear protein information cache"""
        cache_size = len(self._protein_info_cache)
        self._protein_info_cache.clear()
        logger.info(f"Cleared target cache", entries_removed=cache_size)

    def get_cache_size(self) -> int:
        """Get number of cached target entries"""
        return len(self._protein_info_cache)

    def __repr__(self) -> str:
        return (
            f"TargetService("
            f"protein_encoder={self.protein_encoder.model_name}, "
            f"cache_size={self.get_cache_size()}"
            f")"
        )
