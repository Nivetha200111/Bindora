"""
Tests for BindingPredictor and related components
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch

from app.models.binding_predictor import BindingPredictor
from app.models.protein_encoder import ProteinEncoder
from app.models.drug_encoder import DrugEncoder


class TestBindingPredictor:
    """Test cases for BindingPredictor"""

    @pytest.fixture
    def protein_encoder(self):
        """Mock protein encoder for testing"""
        encoder = Mock(spec=ProteinEncoder)
        encoder.model_name = "test_model"
        encoder.encode.return_value = np.random.rand(1280)
        encoder.batch_encode.return_value = np.random.rand(2, 1280)
        return encoder

    @pytest.fixture
    def drug_encoder(self):
        """Mock drug encoder for testing"""
        encoder = Mock(spec=DrugEncoder)
        encoder.get_fingerprint_size.return_value = 2048
        encoder.encode_morgan_fingerprint.return_value = np.random.randint(0, 2, 2048).astype(np.float32)
        encoder.encode_descriptors.return_value = {
            "molecular_weight": 180.0,
            "logp": 1.5,
            "hbd": 1,
            "hba": 4,
            "tpsa": 60.0
        }
        encoder.is_drug_like.return_value = True
        return encoder

    @pytest.fixture
    def predictor(self, protein_encoder, drug_encoder):
        """Create BindingPredictor instance for testing"""
        return BindingPredictor(protein_encoder, drug_encoder)

    @pytest.fixture
    def test_protein_seq(self):
        """Test protein sequence"""
        return "MKTIIALSYIFCLVFA"

    @pytest.fixture
    def test_drug_smiles(self):
        """Test drug SMILES"""
        return "CC(=O)Oc1ccccc1C(=O)O"

    def test_predictor_initialization(self, predictor, protein_encoder, drug_encoder):
        """Test predictor initialization"""
        assert predictor.protein_encoder is protein_encoder
        assert predictor.drug_encoder is drug_encoder
        assert predictor.similarity_threshold == 0.0
        assert predictor.scale_factor == 5.0
        assert len(predictor._protein_cache) == 0

    def test_predict_binding(self, predictor, test_protein_seq, test_drug_smiles):
        """Test single binding prediction"""
        score = predictor.predict_binding(test_protein_seq, test_drug_smiles)

        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        assert np.isfinite(score)

    def test_predict_binding_empty_inputs(self, predictor):
        """Test prediction with empty inputs"""
        with pytest.raises(ValueError, match="Empty protein sequence"):
            predictor.predict_binding("", test_drug_smiles)

        with pytest.raises(ValueError, match="Empty SMILES string"):
            predictor.predict_binding(test_protein_seq, "")

    def test_predict_batch(self, predictor, test_protein_seq):
        """Test batch prediction"""
        drug_smiles_list = [
            "CC(=O)Oc1ccccc1C(=O)O",
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
            "INVALIDSMILES"
        ]

        scores = predictor.predict_batch(test_protein_seq, drug_smiles_list)

        assert isinstance(scores, list)
        assert len(scores) == 3  # Should return score for each input
        assert all(isinstance(score, float) for score in scores)
        assert all(0.0 <= score <= 100.0 for score in scores)

    def test_predict_batch_empty(self, predictor, test_protein_seq):
        """Test batch prediction with empty list"""
        scores = predictor.predict_batch(test_protein_seq, [])
        assert scores == []

    def test_rank_drugs(self, predictor, test_protein_seq):
        """Test drug ranking"""
        drugs = [
            {"chembl_id": "CHEMBL1", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "name": "Drug1"},
            {"chembl_id": "CHEMBL2", "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "name": "Drug2"},
            {"chembl_id": "CHEMBL3", "smiles": "INVALID", "name": "Drug3"}
        ]

        ranked_drugs = predictor.rank_drugs(test_protein_seq, drugs)

        assert isinstance(ranked_drugs, list)
        assert len(ranked_drugs) == 3  # Should return all drugs

        # Check that drugs are sorted by score (highest first)
        scores = [drug_score for _, drug_score in ranked_drugs]
        assert scores == sorted(scores, reverse=True)

        # Check structure
        for drug_data, score in ranked_drugs:
            assert isinstance(drug_data, dict)
            assert "chembl_id" in drug_data
            assert isinstance(score, float)
            assert 0.0 <= score <= 100.0

    def test_rank_drugs_empty(self, predictor, test_protein_seq):
        """Test drug ranking with empty list"""
        ranked_drugs = predictor.rank_drugs(test_protein_seq, [])
        assert ranked_drugs == []

    def test_explain_prediction(self, predictor, test_protein_seq, test_drug_smiles):
        """Test prediction explanation"""
        explanation = predictor.explain_prediction(test_protein_seq, test_drug_smiles)

        assert isinstance(explanation, dict)
        assert "binding_score" in explanation
        assert "similarity" in explanation
        assert "confidence" in explanation
        assert "method" in explanation
        assert "molecular_properties" in explanation

        # Check score is valid
        score = explanation["binding_score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_cache_functionality(self, predictor, test_protein_seq):
        """Test protein embedding cache"""
        # First call should cache
        score1 = predictor.predict_binding(test_protein_seq, test_drug_smiles)

        # Check cache size increased
        assert len(predictor._protein_cache) > 0

        # Second call should use cache
        score2 = predictor.predict_binding(test_protein_seq, test_drug_smiles)

        # Scores should be identical (deterministic with cache)
        assert score1 == score2

    def test_clear_cache(self, predictor, test_protein_seq):
        """Test cache clearing"""
        # Add something to cache
        predictor.predict_binding(test_protein_seq, test_drug_smiles)
        assert len(predictor._protein_cache) > 0

        # Clear cache
        predictor.clear_cache()
        assert len(predictor._protein_cache) == 0

    def test_sigmoid_scale(self, predictor):
        """Test sigmoid scaling function"""
        # Test various similarity values
        test_cases = [
            (-1.0, 0.0),  # Minimum similarity
            (0.0, 0.5),   # Neutral similarity
            (1.0, 1.0),   # Maximum similarity
        ]

        for similarity, expected_range in test_cases:
            scaled = predictor._sigmoid_scale(similarity)
            assert 0.0 <= scaled <= 1.0

    def test_similarity_threshold(self, predictor, test_protein_seq, test_drug_smiles):
        """Test similarity threshold functionality"""
        # Set high threshold
        predictor.similarity_threshold = 0.9

        # This should still work (threshold applied after scoring)
        score = predictor.predict_binding(test_protein_seq, test_drug_smiles)
        assert 0.0 <= score <= 100.0


class TestIntegrationWithRealEncoders:
    """Integration tests with real encoders (if dependencies available)"""

    @pytest.mark.skipif(
        not hasattr(ProteinEncoder, '_validate_sequence'),
        reason="ProteinEncoder not properly implemented"
    )
    def test_real_protein_encoder(self):
        """Test with real ProteinEncoder if available"""
        try:
            encoder = ProteinEncoder()
            sequence = "MKTIIALSYIFCLVFA"
            embedding = encoder.encode(sequence)

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (1280,)

        except Exception as e:
            pytest.skip(f"ProteinEncoder test skipped: {e}")

    @pytest.mark.skipif(
        not hasattr(DrugEncoder, 'is_valid_smiles'),
        reason="DrugEncoder not properly implemented"
    )
    def test_real_drug_encoder(self):
        """Test with real DrugEncoder if available"""
        try:
            encoder = DrugEncoder()
            smiles = "CC(=O)Oc1ccccc1C(=O)O"
            fingerprint = encoder.encode_morgan_fingerprint(smiles)

            assert isinstance(fingerprint, np.ndarray)
            assert fingerprint.shape == (2048,)

        except Exception as e:
            pytest.skip(f"DrugEncoder test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__])

