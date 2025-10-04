"""
Binding Affinity Predictor for drug-target interactions

Predicts binding affinity between protein targets and drug molecules using
similarity-based scoring with protein embeddings and molecular fingerprints.
"""
import time
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import structlog
from sklearn.metrics.pairwise import cosine_similarity

logger = structlog.get_logger()

from app.models.protein_encoder import ProteinEncoder
from app.models.drug_encoder import DrugEncoder


class BindingPredictor:
    """
    Predicts drug-target binding affinity using similarity scoring

    Algorithm:
    1. Encode protein sequence using ESM-2 embeddings
    2. Encode drug molecule using Morgan fingerprints
    3. Calculate cosine similarity between vectors
    4. Apply sigmoid scaling to get binding score (0-100)

    Args:
        protein_encoder: Initialized ProteinEncoder instance
        drug_encoder: Initialized DrugEncoder instance
        similarity_threshold: Minimum similarity for prediction (default: 0.0)
        scale_factor: Scaling factor for sigmoid (default: 5.0)
    """

    def __init__(
        self,
        protein_encoder: ProteinEncoder,
        drug_encoder: DrugEncoder,
        similarity_threshold: float = 0.0,
        scale_factor: float = 5.0
    ):
        self.protein_encoder = protein_encoder
        self.drug_encoder = drug_encoder
        self.similarity_threshold = similarity_threshold
        self.scale_factor = scale_factor

        # Check if scientific libraries are available
        self._scientific_mode = protein_encoder._scientific_mode and drug_encoder._scientific_mode

        if not self._scientific_mode:
            logger.warning("Running in demo mode - AI models not available")

        # Cache for protein embeddings (to avoid re-encoding)
        self._protein_cache: Dict[str, np.ndarray] = {}

        logger.info(
            "Binding predictor initialized",
            protein_model=protein_encoder.model_name,
            drug_encoder_fp_size=drug_encoder.get_fingerprint_size(),
            similarity_threshold=similarity_threshold,
            scale_factor=scale_factor
        )

    def _get_protein_embedding(self, sequence: str) -> np.ndarray:
        """
        Get cached or compute protein embedding

        Args:
            sequence: Protein sequence

        Returns:
            Protein embedding vector
        """
        # Use sequence as cache key (normalize first)
        cache_key = sequence.upper().replace(' ', '')

        if cache_key not in self._protein_cache:
            embedding = self.protein_encoder.encode(sequence)
            self._protein_cache[cache_key] = embedding

            logger.debug(
                f"Cached protein embedding",
                sequence_length=len(sequence),
                cache_size=len(self._protein_cache)
            )

        return self._protein_cache[cache_key]

    def predict_binding(self, protein_seq: str, drug_smiles: str) -> float:
        """
        Predict binding affinity between a protein and drug

        Args:
            protein_seq: Amino acid sequence
            drug_smiles: SMILES string of drug molecule

        Returns:
            Binding score from 0-100 (higher = more likely to bind)

        Raises:
            ValueError: If inputs are invalid
        """
        start_time = time.time()

        try:
        # Validate inputs
        if not protein_seq or not protein_seq.strip():
            raise ValueError("Empty protein sequence provided")

        if not drug_smiles or not drug_smiles.strip():
            raise ValueError("Empty SMILES string provided")

        if not self._scientific_mode:
            # Demo mode: return mock prediction
            logger.info("Using demo mode for binding prediction")
            return self._generate_mock_prediction(protein_seq, drug_smiles)

        # Get embeddings/fingerprints
        protein_embedding = self._get_protein_embedding(protein_seq)
        drug_fingerprint = self.drug_encoder.encode_morgan_fingerprint(drug_smiles)

            # Calculate cosine similarity
            similarity = cosine_similarity(
                protein_embedding.reshape(1, -1),
                drug_fingerprint.reshape(1, -1)
            )[0, 0]

            # Apply sigmoid scaling to get score in 0-100 range
            # sigmoid(x) = 1 / (1 + exp(-x))
            # We use: sigmoid(similarity * scale_factor) * 100
            score = self._sigmoid_scale(similarity) * 100

            # Apply similarity threshold
            if similarity < self.similarity_threshold:
                score *= 0.5  # Reduce score for very low similarity

            # Ensure score is in valid range
            score = max(0.0, min(100.0, score))

            prediction_time = time.time() - start_time

            logger.info(
                f"Predicted binding affinity",
                protein_length=len(protein_seq),
                drug_smiles_length=len(drug_smiles),
                similarity=f"{similarity".3f"}",
                score=f"{score".1f"}",
                prediction_time=f"{prediction_time".3f"}s"
            )

            return score

        except Exception as e:
            logger.error(f"Binding prediction failed: {e}")
            raise RuntimeError(f"Binding prediction failed: {e}")

    def _sigmoid_scale(self, similarity: float) -> float:
        """
        Apply sigmoid scaling to similarity score

        Args:
            similarity: Cosine similarity (-1 to 1)

        Returns:
            Scaled score (0 to 1)
        """
        return 1.0 / (1.0 + np.exp(-similarity * self.scale_factor))

    def predict_batch(
        self,
        protein_seq: str,
        drug_smiles_list: List[str]
    ) -> List[float]:
        """
        Predict binding scores for multiple drugs against one protein

        Args:
            protein_seq: Protein sequence
            drug_smiles_list: List of SMILES strings

        Returns:
            List of binding scores
        """
        if not drug_smiles_list:
            return []

        start_time = time.time()

        try:
            # Get protein embedding once
            protein_embedding = self._get_protein_embedding(protein_seq)

            # Get fingerprints for all drugs
            drug_fingerprints = []
            valid_indices = []

            for i, smiles in enumerate(drug_smiles_list):
                try:
                    fp = self.drug_encoder.encode_morgan_fingerprint(smiles)
                    drug_fingerprints.append(fp)
                    valid_indices.append(i)
                except Exception as e:
                    logger.warning(f"Skipping invalid drug {i}: {e}")
                    continue

            if not drug_fingerprints:
                logger.warning("No valid drugs found for batch prediction")
                return [0.0] * len(drug_smiles_list)

            # Stack fingerprints
            drug_fingerprints = np.stack(drug_fingerprints)

            # Calculate similarities
            similarities = cosine_similarity(
                protein_embedding.reshape(1, -1),
                drug_fingerprints
            )[0]

            # Apply sigmoid scaling
            scores = [self._sigmoid_scale(sim) * 100 for sim in similarities]

            # Apply similarity threshold
            scores = [
                score * 0.5 if sim < self.similarity_threshold else score
                for score, sim in zip(scores, similarities)
            ]

            # Ensure scores are in valid range
            scores = [max(0.0, min(100.0, score)) for score in scores]

            # Create result list with 0s for invalid drugs
            results = [0.0] * len(drug_smiles_list)
            for i, score in zip(valid_indices, scores):
                results[i] = score

            batch_time = time.time() - start_time

            logger.info(
                f"Batch predicted binding affinities",
                protein_length=len(protein_seq),
                num_drugs=len(drug_smiles_list),
                valid_drugs=len(valid_indices),
                batch_time=f"{batch_time".3f"}s"
            )

            return results

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            # Return zeros for all drugs on error
            return [0.0] * len(drug_smiles_list)

    def rank_drugs(
        self,
        protein_seq: str,
        drugs: List[Dict[str, Union[str, float, int]]]
    ) -> List[Tuple[Dict[str, Union[str, float, int]], float]]:
        """
        Rank drugs by predicted binding affinity

        Args:
            protein_seq: Protein sequence
            drugs: List of drug dictionaries with 'smiles' key

        Returns:
            List of (drug_dict, score) tuples sorted by score (descending)
        """
        if not drugs:
            return []

        try:
            # Extract SMILES strings
            drug_smiles_list = [drug.get('smiles', '') for drug in drugs]

            # Get binding scores
            scores = self.predict_batch(protein_seq, drug_smiles_list)

            # Create (drug, score) pairs
            ranked_drugs = list(zip(drugs, scores))

            # Sort by score (highest first)
            ranked_drugs.sort(key=lambda x: x[1], reverse=True)

            logger.info(
                f"Ranked {len(drugs)} drugs by binding affinity",
                top_score=f"{ranked_drugs[0][1]".1f"}" if ranked_drugs else "N/A"
            )

            return ranked_drugs

        except Exception as e:
            logger.error(f"Drug ranking failed: {e}")
            # Return drugs with zero scores on error
            return [(drug, 0.0) for drug in drugs]

    def explain_prediction(
        self,
        protein_seq: str,
        drug_smiles: str
    ) -> Dict[str, Union[float, str]]:
        """
        Provide explanation for binding prediction

        Args:
            protein_seq: Protein sequence
            drug_smiles: SMILES string

        Returns:
            Dictionary with explanation details
        """
        try:
            # Get embeddings for explanation
            protein_embedding = self._get_protein_embedding(protein_seq)
            drug_fingerprint = self.drug_encoder.encode_morgan_fingerprint(drug_smiles)

            # Calculate similarity
            similarity = cosine_similarity(
                protein_embedding.reshape(1, -1),
                drug_fingerprint.reshape(1, -1)
            )[0, 0]

            # Get molecular properties
            descriptors = self.drug_encoder.encode_descriptors(drug_smiles)
            is_drug_like = self.drug_encoder.is_drug_like(drug_smiles)

            # Get binding score
            score = self.predict_binding(protein_seq, drug_smiles)

            explanation = {
                "binding_score": score,
                "similarity": similarity,
                "confidence": "medium",  # Could be enhanced with uncertainty estimation
                "method": "cosine_similarity_esm2_morgan",
                "molecular_properties": {
                    "molecular_weight": descriptors.get('molecular_weight', 0),
                    "logp": descriptors.get('logp', 0),
                    "is_drug_like": is_drug_like,
                    "hbd": descriptors.get('hbd', 0),
                    "hba": descriptors.get('hba', 0)
                },
                "interpretation": self._interpret_score(score, similarity),
                "protein_embedding_dim": len(protein_embedding),
                "drug_fingerprint_bits": self.drug_encoder.get_fingerprint_size(),
                "active_fingerprint_bits": int(drug_fingerprint.sum())
            }

            logger.debug(
                f"Generated prediction explanation",
                score=f"{score".1f"}",
                similarity=f"{similarity".3f"}"
            )

            return explanation

        except Exception as e:
            logger.error(f"Prediction explanation failed: {e}")
            return {
                "error": str(e),
                "binding_score": 0.0,
                "confidence": "low"
            }

    def _interpret_score(self, score: float, similarity: float) -> str:
        """
        Generate human-readable interpretation of binding score

        Args:
            score: Binding score (0-100)
            similarity: Cosine similarity (-1 to 1)

        Returns:
            Interpretation string
        """
        if score >= 80:
            return "Very high binding affinity predicted. Strong candidate for further investigation."
        elif score >= 60:
            return "High binding affinity predicted. Promising drug-target interaction."
        elif score >= 40:
            return "Moderate binding affinity predicted. May warrant further study."
        elif score >= 20:
            return "Low binding affinity predicted. Weak interaction expected."
        else:
            return "Very low binding affinity predicted. Unlikely to be a strong binder."

    def clear_cache(self):
        """Clear protein embedding cache"""
        cache_size = len(self._protein_cache)
        self._protein_cache.clear()
        logger.info(f"Cleared protein embedding cache", entries_removed=cache_size)

    def get_cache_size(self) -> int:
        """Get number of cached protein embeddings"""
        return len(self._protein_cache)

    def _generate_mock_prediction(self, protein_seq: str, drug_smiles: str) -> float:
        """
        Generate mock binding prediction for demo purposes

        Args:
            protein_seq: Protein sequence
            drug_smiles: Drug SMILES

        Returns:
            Mock binding score (0-100)
        """
        import hashlib

        # Create deterministic mock prediction based on inputs
        combined_input = f"{protein_seq}:{drug_smiles}"
        input_hash = int(hashlib.md5(combined_input.encode()).hexdigest()[:8], 16)

        # Generate pseudo-random but realistic score
        np.random.seed(input_hash)

        # Bias towards reasonable drug-like scores (60-90% range)
        base_score = 60.0 + np.random.rand() * 30.0

        logger.debug(
            f"Generated mock binding prediction",
            protein_length=len(protein_seq),
            drug_smiles_length=len(drug_smiles),
            score=f"{base_score".1f"}",
            demo_mode=True
        )

        return base_score

    def __repr__(self) -> str:
        return (
            f"BindingPredictor("
            f"protein_model={self.protein_encoder.model_name}, "
            f"drug_fp_size={self.drug_encoder.get_fingerprint_size()}"
            f")"
        )
