"""
Search Service - Main orchestration for drug-target search

Handles the complete search workflow:
1. Query type detection and resolution
2. Protein sequence retrieval
3. Drug candidate loading
4. Binding prediction and ranking
5. Result enrichment and formatting
"""
import time
import asyncio
from typing import Dict, List, Optional, Union
import structlog

logger = structlog.get_logger()

from app.models.binding_predictor import BindingPredictor
from app.utils.uniprot_client import fetch_protein_sequence, search_proteins_by_disease
from app.utils.chembl_client import fetch_approved_drugs


class SearchService:
    """
    Main search service for drug-target interaction prediction

    Args:
        binding_predictor: Initialized BindingPredictor instance
        max_results: Maximum number of results to return (default: 20)
        min_binding_score: Minimum binding score threshold (default: 0)
        cache_proteins: Whether to cache protein sequences (default: True)
    """

    def __init__(
        self,
        binding_predictor: BindingPredictor,
        max_results: int = 20,
        min_binding_score: float = 0.0,
        cache_proteins: bool = True
    ):
        self.binding_predictor = binding_predictor
        self.max_results = max_results
        self.min_binding_score = min_binding_score
        self.cache_proteins = cache_proteins

        # Protein sequence cache
        self._protein_cache: Dict[str, str] = {}

        logger.info(
            "Search service initialized",
            max_results=max_results,
            min_binding_score=min_binding_score
        )

    async def search_drugs_for_target(
        self,
        query: str,
        query_type: str,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Union[str, float, int, bool]]]:
        """
        Main search function - find drugs that bind to a target

        Args:
            query: User query (disease name, gene symbol, or protein sequence)
            query_type: Type of query ("disease", "gene", "sequence")
            max_results: Override default max results

        Returns:
            List of drug dictionaries with binding scores

        Raises:
            ValueError: If query type is invalid or query cannot be resolved
        """
        start_time = time.time()

        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Empty query provided")

        if query_type not in ["disease", "gene", "sequence"]:
            raise ValueError(f"Invalid query type: {query_type}")

        max_results = max_results or self.max_results

        logger.info(
            f"Starting drug search",
            query=query[:50] + "..." if len(query) > 50 else query,
            query_type=query_type,
            max_results=max_results
        )

        try:
            # Step 1: Resolve query to protein sequence(s)
            protein_sequences = await self._resolve_query_to_proteins(query, query_type)

            if not protein_sequences:
                raise ValueError(f"No protein targets found for query: {query}")

            logger.info(f"Found {len(protein_sequences)} protein targets")

            # Step 2: Load drug candidates
            drug_candidates = await self._load_drug_candidates()
            logger.info(f"Loaded {len(drug_candidates)} drug candidates")

            # Step 3: Predict binding and rank drugs
            ranked_drugs = []

            for protein_seq in protein_sequences:
                # Rank drugs for this protein
                protein_ranked = self.binding_predictor.rank_drugs(protein_seq, drug_candidates)

                # Add protein info to each drug
                for drug, score in protein_ranked:
                    drug_with_score = dict(drug)
                    drug_with_score['binding_score'] = score
                    drug_with_score['target_protein'] = protein_seq[:50] + "..." if len(protein_seq) > 50 else protein_seq
                    ranked_drugs.append(drug_with_score)

            # Step 4: Aggregate and sort results
            # Combine scores from multiple proteins (if applicable)
            aggregated_results = self._aggregate_results(ranked_drugs)

            # Filter by minimum score
            filtered_results = [
                drug for drug in aggregated_results
                if drug.get('binding_score', 0) >= self.min_binding_score
            ]

            # Sort by binding score (highest first)
            filtered_results.sort(key=lambda x: x.get('binding_score', 0), reverse=True)

            # Limit results
            final_results = filtered_results[:max_results]

            # Step 5: Enrich results with additional data
            enriched_results = await self._enrich_drug_data(final_results)

            search_time = time.time() - start_time

            logger.info(
                f"Drug search completed",
                num_targets=len(protein_sequences),
                num_candidates=len(drug_candidates),
                num_results=len(enriched_results),
                search_time=f"{search_time".2f"}s"
            )

            return enriched_results

        except Exception as e:
            logger.error("Drug search failed", error=str(e))
            raise RuntimeError(f"Search failed: {e}")

    async def _resolve_query_to_proteins(self, query: str, query_type: str) -> List[str]:
        """
        Convert query to protein sequence(s)

        Args:
            query: User query
            query_type: Query type

        Returns:
            List of protein sequences
        """
        if query_type == "sequence":
            # Direct sequence input
            if self.cache_proteins:
                cache_key = query.upper().replace(' ', '')
                if cache_key in self._protein_cache:
                    return [self._protein_cache[cache_key]]

            # Validate sequence
            if not self._is_valid_protein_sequence(query):
                raise ValueError("Invalid protein sequence provided")

            protein_seq = query.upper().replace(' ', '')
            if self.cache_proteins:
                self._protein_cache[cache_key] = protein_seq
            return [protein_seq]

        elif query_type == "gene":
            # Gene symbol lookup
            cache_key = f"gene:{query.upper()}"

            if self.cache_proteins and cache_key in self._protein_cache:
                return [self._protein_cache[cache_key]]

            # Fetch from UniProt
            protein_seq = await fetch_protein_sequence(query)

            if not protein_seq:
                raise ValueError(f"No protein sequence found for gene: {query}")

            if self.cache_proteins:
                self._protein_cache[cache_key] = protein_seq

            return [protein_seq]

        elif query_type == "disease":
            # Disease name lookup
            cache_key = f"disease:{query.lower()}"

            if self.cache_proteins and cache_key in self._protein_cache:
                return [self._protein_cache[cache_key]]

            # Search for related proteins
            protein_sequences = await search_proteins_by_disease(query)

            if not protein_sequences:
                raise ValueError(f"No protein targets found for disease: {query}")

            if self.cache_proteins:
                # Cache the first (most relevant) protein
                self._protein_cache[cache_key] = protein_sequences[0]

            return protein_sequences

        else:
            raise ValueError(f"Unknown query type: {query_type}")

    def _is_valid_protein_sequence(self, sequence: str) -> bool:
        """
        Validate protein sequence format

        Args:
            sequence: Protein sequence string

        Returns:
            True if valid sequence, False otherwise
        """
        if not sequence:
            return False

        # Standard amino acids
        valid_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")

        # Clean sequence (remove common separators)
        cleaned = ''.join(c.upper() for c in sequence if c.isalpha())

        # Check if all characters are valid amino acids
        return all(c in valid_amino_acids for c in cleaned)

    async def _load_drug_candidates(self) -> List[Dict[str, Union[str, float, int]]]:
        """
        Load drug candidates from database or API

        Returns:
            List of drug dictionaries with SMILES and metadata
        """
        try:
            # Try to load from local data first
            drugs = await self._load_drugs_from_local()

            if not drugs:
                # Fall back to ChEMBL API
                logger.warning("No local drug data found, fetching from ChEMBL API")
                drugs = await fetch_approved_drugs(limit=1000)

            # Filter for drug-like molecules only
            drug_like_drugs = []
            for drug in drugs:
                if drug.get('smiles'):
                    try:
                        is_drug_like = self.binding_predictor.drug_encoder.is_drug_like(drug['smiles'])
                        if is_drug_like:
                            drug_like_drugs.append(drug)
                    except Exception as e:
                        logger.warning(f"Could not check drug-likeness for {drug.get('chembl_id')}: {e}")
                        continue

            logger.info(f"Loaded {len(drug_like_drugs)} drug-like candidates from {len(drugs)} total drugs")

            return drug_like_drugs

        except Exception as e:
            logger.error(f"Failed to load drug candidates: {e}")
            # Return empty list on error
            return []

    async def _load_drugs_from_local(self) -> List[Dict[str, Union[str, float, int]]]:
        """
        Load drugs from local data files (CSV/JSON)

        Returns:
            List of drug dictionaries
        """
        # TODO: Implement local data loading from CSV files
        # For now, return empty to fall back to API
        return []

    def _aggregate_results(self, ranked_drugs: List[Dict]) -> List[Dict]:
        """
        Aggregate results from multiple protein targets

        Args:
            ranked_drugs: List of drug dictionaries with binding scores

        Returns:
            Aggregated and deduplicated results
        """
        # Group by ChEMBL ID
        drug_groups: Dict[str, List[Dict]] = {}

        for drug in ranked_drugs:
            chembl_id = drug.get('chembl_id', '')
            if chembl_id not in drug_groups:
                drug_groups[chembl_id] = []
            drug_groups[chembl_id].append(drug)

        # Aggregate scores for each drug
        aggregated_results = []

        for chembl_id, drug_list in drug_groups.items():
            if not drug_list:
                continue

            # Use maximum score across all targets
            max_score = max(drug.get('binding_score', 0) for drug in drug_list)

            # Use the drug data from the highest scoring instance
            best_drug = max(drug_list, key=lambda x: x.get('binding_score', 0))

            # Update with aggregated score
            aggregated_drug = dict(best_drug)
            aggregated_drug['binding_score'] = max_score
            aggregated_drug['num_targets_tested'] = len(drug_list)

            aggregated_results.append(aggregated_drug)

        return aggregated_results

    async def _enrich_drug_data(self, drugs: List[Dict]) -> List[Dict]:
        """
        Enrich drug data with additional properties

        Args:
            drugs: List of drug dictionaries

        Returns:
            Enriched drug dictionaries
        """
        enriched_drugs = []

        for drug in drugs:
            try:
                enriched_drug = dict(drug)

                # Calculate molecular properties if not present
                if 'molecular_weight' not in drug and drug.get('smiles'):
                    try:
                        descriptors = self.binding_predictor.drug_encoder.encode_descriptors(drug['smiles'])
                        enriched_drug.update({
                            'molecular_weight': descriptors.get('molecular_weight', 0),
                            'logp': descriptors.get('logp', 0),
                            'hbd': descriptors.get('hbd', 0),
                            'hba': descriptors.get('hba', 0),
                            'tpsa': descriptors.get('tpsa', 0),
                            'is_drug_like': descriptors.get('is_drug_like', True)
                        })
                    except Exception as e:
                        logger.warning(f"Could not calculate properties for {drug.get('chembl_id')}: {e}")

                # Ensure required fields
                enriched_drug.setdefault('molecular_weight', 0)
                enriched_drug.setdefault('logp', 0)
                enriched_drug.setdefault('hbd', 0)
                enriched_drug.setdefault('hba', 0)
                enriched_drug.setdefault('tpsa', 0)
                enriched_drug.setdefault('is_drug_like', False)
                enriched_drug.setdefault('clinical_phase', 4)  # Default to approved

                enriched_drugs.append(enriched_drug)

            except Exception as e:
                logger.error(f"Failed to enrich drug {drug.get('chembl_id')}: {e}")
                continue

        return enriched_drugs

    def clear_cache(self):
        """Clear protein sequence cache"""
        cache_size = len(self._protein_cache)
        self._protein_cache.clear()
        logger.info(f"Cleared protein cache", entries_removed=cache_size)

    def get_cache_size(self) -> int:
        """Get number of cached protein sequences"""
        return len(self._protein_cache)

    def __repr__(self) -> str:
        return (
            f"SearchService("
            f"max_results={self.max_results}, "
            f"cache_size={self.get_cache_size()}"
            f")"
        )
