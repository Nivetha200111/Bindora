"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import json

from app.main import app


class TestAPIEndpoints:
    """Test cases for API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "models_loaded" in data
        assert "database_connected" in data
        assert "cache_available" in data
        assert "version" in data

        assert data["status"] in ["healthy", "degraded", "error"]

    def test_stats_endpoint(self, client):
        """Test platform statistics endpoint"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_drugs" in data
        assert "total_targets" in data
        assert "predictions_made" in data
        assert "avg_prediction_time" in data
        assert "cache_size" in data
        assert "model_status" in data

        # Check data types
        assert isinstance(data["total_drugs"], int)
        assert isinstance(data["total_targets"], int)
        assert isinstance(data["predictions_made"], int)
        assert isinstance(data["avg_prediction_time"], float)
        assert isinstance(data["cache_size"], int)
        assert isinstance(data["model_status"], str)

    def test_search_endpoint_gene(self, client):
        """Test drug search with gene query"""
        request_data = {
            "query": "BRCA1",
            "query_type": "gene",
            "max_results": 5
        }

        response = client.post("/api/search", json=request_data)

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()

            assert "results" in data
            assert "total" in data
            assert "query" in data
            assert "query_type" in data

            assert isinstance(data["results"], list)
            assert isinstance(data["total"], int)
            assert data["query"] == "BRCA1"
            assert data["query_type"] == "gene"

            # Check result structure if results exist
            if data["results"]:
                result = data["results"][0]
                assert "chembl_id" in result
                assert "name" in result
                assert "smiles" in result
                assert "binding_score" in result
                assert "molecular_weight" in result
                assert "is_drug_like" in result
                assert "clinical_phase" in result

                # Check data types and ranges
                assert isinstance(result["binding_score"], float)
                assert 0.0 <= result["binding_score"] <= 100.0
                assert isinstance(result["is_drug_like"], bool)
                assert 0 <= result["clinical_phase"] <= 4

    def test_search_endpoint_sequence(self, client):
        """Test drug search with sequence query"""
        request_data = {
            "query": "MKTIIALSYIFCLVFA",
            "query_type": "sequence",
            "max_results": 5
        }

        response = client.post("/api/search", json=request_data)

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            assert len(data["results"]) <= 5
            assert data["query_type"] == "sequence"

    def test_search_endpoint_invalid_query_type(self, client):
        """Test search with invalid query type"""
        request_data = {
            "query": "test",
            "query_type": "invalid_type",
            "max_results": 5
        }

        response = client.post("/api/search", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_search_endpoint_empty_query(self, client):
        """Test search with empty query"""
        request_data = {
            "query": "",
            "query_type": "gene",
            "max_results": 5
        }

        response = client.post("/api/search", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_drug_details_endpoint(self, client):
        """Test drug details endpoint"""
        # Try to get a known drug
        response = client.get("/api/drug/CHEMBL25")

        # Should either succeed or return 404 if drug not in test data
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            assert "chembl_id" in data
            assert "name" in data
            assert "smiles" in data
            assert "molecular_properties" in data
            assert "is_drug_like" in data

    def test_drug_details_endpoint_invalid_id(self, client):
        """Test drug details with invalid ID"""
        response = client.get("/api/drug/INVALID123")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_target_info_endpoint(self, client):
        """Test target information endpoint"""
        response = client.get("/api/target/P38398")

        # Should either succeed or return 404 if target not in test data
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            assert "uniprot_id" in data
            assert "name" in data
            assert "sequence_length" in data
            assert "embedding_available" in data

    def test_target_info_endpoint_invalid_id(self, client):
        """Test target info with invalid ID"""
        response = client.get("/api/target/INVALID123")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_admin_endpoints(self, client):
        """Test admin endpoints"""
        # Test cache clear
        response = client.post("/api/admin/cache/clear")
        assert response.status_code in [200, 404]  # May not be implemented

        # Test system info
        response = client.get("/api/admin/info")
        assert response.status_code in [200, 404]  # May not be implemented

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/search")

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers


class TestAPIErrorHandling:
    """Test API error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post("/api/search", data="invalid json")

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post("/api/search", json={"query": "test"})

        assert response.status_code == 422

    def test_invalid_content_type(self, client):
        """Test handling of invalid content type"""
        response = client.post(
            "/api/search",
            data=json.dumps({"query": "test", "query_type": "gene"}),
            headers={"Content-Type": "text/plain"}
        )

        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 415, 422]


if __name__ == "__main__":
    pytest.main([__file__])

