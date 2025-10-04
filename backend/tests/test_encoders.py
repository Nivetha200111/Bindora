"""
Tests for AI encoders (ProteinEncoder and DrugEncoder)
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.models.protein_encoder import ProteinEncoder
from app.models.drug_encoder import DrugEncoder


class TestProteinEncoder:
    """Test cases for ProteinEncoder"""

    @pytest.fixture
    def encoder(self):
        """Create a ProteinEncoder instance for testing"""
        return ProteinEncoder()

    @pytest.fixture
    def valid_sequence(self):
        """Valid protein sequence for testing"""
        return "MKTIIALSYIFCLVFA"

    @pytest.fixture
    def invalid_sequence(self):
        """Invalid sequence for testing"""
        return "INVALIDXXX"

    def test_encoder_initialization(self, encoder):
        """Test encoder initialization"""
        assert encoder.model_name == "facebook/esm2_t33_650M_UR50D"
        assert encoder.device in ["cpu", "cuda", "mps"]
        assert encoder.max_length == 1024
        assert encoder.get_embedding_dimension() == 1280

    def test_validate_sequence_valid(self, encoder, valid_sequence):
        """Test sequence validation with valid sequence"""
        assert encoder._validate_sequence(valid_sequence)

    def test_validate_sequence_invalid(self, encoder, invalid_sequence):
        """Test sequence validation with invalid sequence"""
        assert not encoder._validate_sequence(invalid_sequence)

    def test_validate_sequence_empty(self, encoder):
        """Test sequence validation with empty input"""
        assert not encoder._validate_sequence("")
        assert not encoder._validate_sequence(None)

    def test_preprocess_sequence(self, encoder, valid_sequence):
        """Test sequence preprocessing"""
        result = encoder._preprocess_sequence(valid_sequence)
        assert isinstance(result, str)
        assert len(result) <= encoder.max_length
        assert result.isupper()

    def test_preprocess_sequence_invalid(self, encoder, invalid_sequence):
        """Test sequence preprocessing with invalid sequence"""
        with pytest.raises(ValueError, match="Invalid amino acid sequence"):
            encoder._preprocess_sequence(invalid_sequence)

    def test_encode_single_sequence(self, encoder, valid_sequence):
        """Test encoding of single protein sequence"""
        embedding = encoder.encode(valid_sequence)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1280,)
        assert np.isfinite(embedding).all()
        assert not np.isnan(embedding).any()

    def test_encode_empty_sequence(self, encoder):
        """Test encoding with empty sequence"""
        with pytest.raises(ValueError, match="Empty or None sequence"):
            encoder.encode("")

    def test_batch_encode(self, encoder):
        """Test batch encoding of multiple sequences"""
        sequences = ["MKTIIALSYIFCLVFA", "MDLSALRVEEVQNVINAMQK"]

        embeddings = encoder.batch_encode(sequences)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 1280)
        assert np.isfinite(embeddings).all()

    def test_batch_encode_empty(self, encoder):
        """Test batch encoding with empty list"""
        with pytest.raises(ValueError, match="Empty sequences list"):
            encoder.batch_encode([])

    def test_batch_encode_single(self, encoder, valid_sequence):
        """Test batch encoding with single sequence"""
        embeddings = encoder.batch_encode([valid_sequence])

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (1, 1280)

        # Should be same as single encode
        single_embedding = encoder.encode(valid_sequence)
        np.testing.assert_array_almost_equal(embeddings[0], single_embedding)


class TestDrugEncoder:
    """Test cases for DrugEncoder"""

    @pytest.fixture
    def encoder(self):
        """Create a DrugEncoder instance for testing"""
        return DrugEncoder()

    @pytest.fixture
    def valid_smiles(self):
        """Valid SMILES for testing"""
        return "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin

    @pytest.fixture
    def invalid_smiles(self):
        """Invalid SMILES for testing"""
        return "INVALIDSMILES"

    def test_encoder_initialization(self, encoder):
        """Test encoder initialization"""
        assert encoder.fingerprint_size == 2048
        assert encoder.fingerprint_radius == 2
        assert encoder.get_fingerprint_size() == 2048
        assert len(encoder.get_property_names()) > 0

    def test_is_valid_smiles_valid(self, encoder, valid_smiles):
        """Test SMILES validation with valid SMILES"""
        assert encoder.is_valid_smiles(valid_smiles)

    def test_is_valid_smiles_invalid(self, encoder, invalid_smiles):
        """Test SMILES validation with invalid SMILES"""
        assert not encoder.is_valid_smiles(invalid_smiles)

    def test_is_valid_smiles_empty(self, encoder):
        """Test SMILES validation with empty input"""
        assert not encoder.is_valid_smiles("")
        assert not encoder.is_valid_smiles(None)

    def test_encode_morgan_fingerprint(self, encoder, valid_smiles):
        """Test Morgan fingerprint generation"""
        fingerprint = encoder.encode_morgan_fingerprint(valid_smiles)

        assert isinstance(fingerprint, np.ndarray)
        assert fingerprint.shape == (2048,)
        assert fingerprint.dtype == np.float32
        assert np.isfinite(fingerprint).all()

    def test_encode_morgan_fingerprint_invalid(self, encoder, invalid_smiles):
        """Test Morgan fingerprint with invalid SMILES"""
        with pytest.raises(ValueError, match="Invalid SMILES string"):
            encoder.encode_morgan_fingerprint(invalid_smiles)

    def test_encode_descriptors(self, encoder, valid_smiles):
        """Test molecular descriptor calculation"""
        descriptors = encoder.encode_descriptors(valid_smiles)

        assert isinstance(descriptors, dict)
        assert "molecular_weight" in descriptors
        assert "logp" in descriptors
        assert "hbd" in descriptors
        assert "hba" in descriptors
        assert "tpsa" in descriptors

        # Check that values are reasonable
        assert descriptors["molecular_weight"] > 0
        assert isinstance(descriptors["hbd"], (int, float))
        assert isinstance(descriptors["hba"], (int, float))

    def test_encode_descriptors_invalid(self, encoder, invalid_smiles):
        """Test descriptor calculation with invalid SMILES"""
        with pytest.raises(ValueError, match="Invalid SMILES string"):
            encoder.encode_descriptors(invalid_smiles)

    def test_is_drug_like(self, encoder, valid_smiles):
        """Test drug-likeness check"""
        is_drug_like = encoder.is_drug_like(valid_smiles)

        assert isinstance(is_drug_like, bool)

    def test_is_drug_like_invalid(self, encoder, invalid_smiles):
        """Test drug-likeness check with invalid SMILES"""
        is_drug_like = encoder.is_drug_like(invalid_smiles)

        # Should return False for invalid molecules
        assert not is_drug_like

    def test_calculate_similarity(self, encoder, valid_smiles):
        """Test molecular similarity calculation"""
        smiles1 = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        smiles2 = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"  # Ibuprofen

        similarity = encoder.calculate_similarity(smiles1, smiles2)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_invalid(self, encoder, invalid_smiles):
        """Test similarity calculation with invalid SMILES"""
        similarity = encoder.calculate_similarity(valid_smiles, invalid_smiles)

        # Should return 0.0 for invalid molecules
        assert similarity == 0.0

    def test_encode_combined(self, encoder, valid_smiles):
        """Test combined encoding (fingerprint + descriptors)"""
        combined = encoder.encode_combined(valid_smiles)

        assert isinstance(combined, np.ndarray)
        # Should be fingerprint size + number of descriptors
        expected_size = encoder.get_fingerprint_size() + len(encoder.get_property_names())
        assert combined.shape == (expected_size,)

    def test_property_normalization(self, encoder):
        """Test property normalization"""
        # Test with a drug that should pass Lipinski rules
        aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
        descriptors = encoder.encode_descriptors(aspirin_smiles)

        # Check that normalized values are in [0, 1] range
        for prop_name in encoder.property_ranges.keys():
            if prop_name in descriptors:
                value = descriptors[prop_name]
                assert 0.0 <= value <= 1.0, f"Property {prop_name} not normalized: {value}"


class TestIntegration:
    """Integration tests between encoders"""

    @pytest.fixture
    def protein_encoder(self):
        """Create ProteinEncoder for integration tests"""
        return ProteinEncoder()

    @pytest.fixture
    def drug_encoder(self):
        """Create DrugEncoder for integration tests"""
        return DrugEncoder()

    def test_encoders_compatibility(self, protein_encoder, drug_encoder):
        """Test that encoders work together"""
        protein_seq = "MKTIIALSYIFCLVFA"
        drug_smiles = "CC(=O)Oc1ccccc1C(=O)O"

        # Encode both
        protein_emb = protein_encoder.encode(protein_seq)
        drug_fp = drug_encoder.encode_morgan_fingerprint(drug_smiles)

        # Check dimensions are compatible for similarity calculation
        assert protein_emb.shape[0] == 1280  # ESM-2 embedding size
        assert drug_fp.shape[0] == 2048  # Morgan fingerprint size

        # Test cosine similarity calculation
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(
            protein_emb.reshape(1, -1),
            drug_fp.reshape(1, -1)
        )[0, 0]

        assert -1.0 <= similarity <= 1.0
        assert np.isfinite(similarity)


if __name__ == "__main__":
    pytest.main([__file__])

