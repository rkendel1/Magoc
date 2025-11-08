"""
Tests for FastAPI workflow endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from magoc_workflow_extensions.api import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "workflowName": "Test Workflow",
        "workflowDescription": "A test workflow",
        "selectedEndpoints": [
            {
                "endpointId": "endpoint-1",
                "order": 0,
                "reasoning": "Test reasoning",
                "parameters": {"param1": "value1"},
                "dependsOn": []
            }
        ],
        "explanation": "Test explanation"
    }


class TestRootEndpoints:
    """Test root and health endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Magoc Workflow Extensions"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "magoc-workflow-extensions"


class TestGenerateWorkflow:
    """Test workflow generation endpoint"""
    
    def test_generate_workflow_success(self, client, mock_openai_response):
        """Test successful workflow generation"""
        with patch("magoc_workflow_extensions.services.workflow_generator.OpenAI") as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = str(mock_openai_response).replace("'", '"')
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Test request
            request_data = {
                "description": "Create a user and send email",
                "endpoints": [
                    {
                        "id": "endpoint-1",
                        "method": "POST",
                        "path": "/users",
                        "summary": "Create user",
                        "parameters": []
                    }
                ],
                "specId": "test-spec"
            }
            
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                response = client.post("/api/workflows/generate-from-nl", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "workflow" in data["data"]
    
    def test_generate_workflow_missing_description(self, client):
        """Test workflow generation with missing description"""
        request_data = {
            "endpoints": [],
            "specId": "test-spec"
        }
        
        response = client.post("/api/workflows/generate-from-nl", json=request_data)
        assert response.status_code == 422  # Validation error


class TestSuggestFlows:
    """Test flow suggestion endpoint"""
    
    def test_suggest_flows_success(self, client):
        """Test successful flow suggestion"""
        with patch("magoc_workflow_extensions.services.flow_suggester.OpenAI") as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_response = Mock()
            mock_suggestion = {
                "suggestedFlows": [
                    {
                        "id": "flow-1",
                        "name": "Test Flow",
                        "description": "A test flow",
                        "useCase": "Testing",
                        "endpoints": ["endpoint-1"],
                        "category": "CRUD",
                        "complexity": "simple"
                    }
                ],
                "apiSummary": "Test API"
            }
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = str(mock_suggestion).replace("'", '"')
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            request_data = {
                "endpoints": [
                    {
                        "id": "endpoint-1",
                        "method": "GET",
                        "path": "/test",
                        "summary": "Test endpoint"
                    }
                ],
                "specId": "test-spec"
            }
            
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                response = client.post("/api/workflows/suggest-flows", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data


class TestLearnPattern:
    """Test pattern learning endpoint"""
    
    def test_learn_pattern_success(self, client):
        """Test successful pattern learning"""
        with patch("magoc_workflow_extensions.services.pattern_learner.OpenAI") as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_response = Mock()
            mock_pattern = {
                "patterns": {
                    "structure": {"type": "sequential", "description": "Test"},
                    "parameters": {"mappingStrategy": "Test"},
                    "interactions": {"pattern": "CRUD", "description": "Test"}
                },
                "confidence": 0.9
            }
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = str(mock_pattern).replace("'", '"')
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            request_data = {
                "referenceWorkflow": {
                    "name": "Test Workflow",
                    "description": "Test",
                    "steps": []
                },
                "referenceEndpoints": []
            }
            
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                response = client.post("/api/workflows/learn-pattern", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestAutoBuild:
    """Test auto-build endpoint"""
    
    def test_auto_build_success(self, client):
        """Test successful auto-building"""
        with patch("magoc_workflow_extensions.services.auto_builder.OpenAI") as mock_openai:
            # Setup mock
            mock_client = Mock()
            mock_response = Mock()
            mock_workflows = {
                "workflows": [
                    {
                        "flow_id": "flow-1",
                        "workflow": {
                            "name": "Built Workflow",
                            "description": "Test",
                            "steps": [],
                            "specId": "test-spec"
                        },
                        "applied_patterns": ["sequential"]
                    }
                ]
            }
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = str(mock_workflows).replace("'", '"')
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            request_data = {
                "suggestedFlows": [{"id": "flow-1", "name": "Test", "endpoints": []}],
                "learnedPatterns": {},
                "endpoints": [],
                "specId": "test-spec"
            }
            
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                response = client.post("/api/workflows/auto-build-flows", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options(
            "/api/workflows/generate-from-nl",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
