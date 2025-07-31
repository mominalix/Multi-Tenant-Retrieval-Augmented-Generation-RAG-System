"""
Basic API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "app_name" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user_without_tenant(self, client: TestClient, sample_user_data):
        """Test user registration without valid tenant"""
        response = client.post(
            "/api/v1/auth/register",
            json=sample_user_data,
            params={"tenant_id": "nonexistent-tenant-id"}
        )
        
        # Should fail because tenant doesn't exist
        assert response.status_code == 404
    
    def test_login_with_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_without_auth(self, client: TestClient):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestDocumentEndpoints:
    """Test document management endpoints"""
    
    def test_list_documents_without_auth(self, client: TestClient):
        """Test listing documents without authentication"""
        response = client.get("/api/v1/documents/")
        
        assert response.status_code == 401
    
    def test_upload_document_without_auth(self, client: TestClient):
        """Test uploading document without authentication"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", "test content", "text/plain")}
        )
        
        assert response.status_code == 401


class TestQueryEndpoints:
    """Test RAG query endpoints"""
    
    def test_rag_query_without_auth(self, client: TestClient):
        """Test RAG query without authentication"""
        response = client.post("/api/v1/queries/rag", json={
            "query": "What is the meaning of life?",
            "max_chunks": 5
        })
        
        assert response.status_code == 401
    
    def test_query_history_without_auth(self, client: TestClient):
        """Test query history without authentication"""
        response = client.get("/api/v1/queries/history")
        
        assert response.status_code == 401


# Integration test (more complex)
class TestTenantWorkflow:
    """Test complete tenant workflow"""
    
    @pytest.mark.skip(reason="Requires complex setup with admin user")
    def test_complete_tenant_workflow(self, client: TestClient, sample_tenant_data, sample_user_data):
        """Test complete workflow: create tenant, create user, login, upload document, query"""
        
        # This test would require:
        # 1. Creating an admin user first
        # 2. Creating a tenant
        # 3. Creating a regular user in that tenant
        # 4. Logging in as that user
        # 5. Uploading a document
        # 6. Making a RAG query
        
        # This is a complex integration test that would need proper setup
        pass