"""
FastAPI application for Magoc Workflow Extensions
Provides REST API endpoints for AI-powered workflow generation
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging

from .models.schemas import (
    GenerateWorkflowRequest,
    SuggestFlowsRequest,
    LearnPatternRequest,
    AutoBuildRequest,
)
from .services.workflow_generator import WorkflowGenerator
from .services.flow_suggester import FlowSuggester
from .services.pattern_learner import PatternLearner
from .services.auto_builder import AutoBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title="Magoc Workflow Extensions",
    description="AI-powered API workflow generation backend",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (will be created on first request)
_workflow_gen = None
_flow_suggester = None
_pattern_learner = None
_auto_builder = None


def get_workflow_generator() -> WorkflowGenerator:
    """Get or create workflow generator instance"""
    global _workflow_gen
    if _workflow_gen is None:
        _workflow_gen = WorkflowGenerator()
    return _workflow_gen


def get_flow_suggester() -> FlowSuggester:
    """Get or create flow suggester instance"""
    global _flow_suggester
    if _flow_suggester is None:
        _flow_suggester = FlowSuggester()
    return _flow_suggester


def get_pattern_learner() -> PatternLearner:
    """Get or create pattern learner instance"""
    global _pattern_learner
    if _pattern_learner is None:
        _pattern_learner = PatternLearner()
    return _pattern_learner


def get_auto_builder() -> AutoBuilder:
    """Get or create auto builder instance"""
    global _auto_builder
    if _auto_builder is None:
        _auto_builder = AutoBuilder()
    return _auto_builder


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Magoc Workflow Extensions",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "magoc-workflow-extensions"
    }


@app.post("/api/workflows/generate-from-nl")
async def generate_workflow(request: GenerateWorkflowRequest) -> Dict[str, Any]:
    """
    Generate workflow from natural language description
    
    This endpoint takes a natural language description of a desired workflow
    and uses AI to select appropriate API endpoints and arrange them in an
    optimal execution order. Optionally saves to Convex if userId provided.
    """
    try:
        generator = get_workflow_generator()
        
        # If spec_id provided and no endpoints, try to fetch from Convex
        endpoints = request.endpoints
        if not endpoints and request.userId:
            from .convex_client import get_convex_client
            convex = get_convex_client()
            spec = await convex.get_api_spec(request.specId)
            if spec and spec.get("spec", {}).get("paths"):
                # Extract endpoints from OpenAPI spec
                endpoints = []
                for path, methods in spec["spec"]["paths"].items():
                    for method, details in methods.items():
                        if method.lower() in ["get", "post", "put", "delete", "patch"]:
                            endpoints.append({
                                "id": details.get("operationId", f"{method}_{path}"),
                                "method": method.upper(),
                                "path": path,
                                "summary": details.get("summary", ""),
                                "description": details.get("description", ""),
                                "parameters": details.get("parameters", [])
                            })
        
        result = generator.generate_from_nl(
            request.description,
            endpoints or request.endpoints,
            request.specId
        )
        
        # Optionally save workflow to Convex
        if request.userId:
            try:
                from .convex_client import get_convex_client
                import uuid
                convex = get_convex_client()
                workflow_id = str(uuid.uuid4())
                await convex.save_workflow(
                    workflow_id=workflow_id,
                    name=result["workflow"]["name"],
                    steps=result["workflow"]["steps"],
                    user_id=request.userId,
                    description=result["workflow"]["description"]
                )
                result["workflowId"] = workflow_id
            except Exception as e:
                # Log but don't fail the request if Convex save fails
                logger.warning(f"Failed to save workflow to Convex: {e}")
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate workflow: {str(e)}")


@app.post("/api/workflows/suggest-flows")
async def suggest_flows(request: SuggestFlowsRequest) -> Dict[str, Any]:
    """
    Suggest workflows based on API analysis
    
    This endpoint analyzes the available API endpoints and suggests practical
    workflows that users might want to create. Saves suggestions to Convex if userId provided.
    """
    try:
        suggester = get_flow_suggester()
        
        # If spec_id provided and no endpoints, try to fetch from Convex
        endpoints = request.endpoints
        if not endpoints and request.userId:
            from .convex_client import get_convex_client
            convex = get_convex_client()
            spec = await convex.get_api_spec(request.specId)
            if spec and spec.get("spec", {}).get("paths"):
                # Extract endpoints from OpenAPI spec
                endpoints = []
                for path, methods in spec["spec"]["paths"].items():
                    for method, details in methods.items():
                        if method.lower() in ["get", "post", "put", "delete", "patch"]:
                            endpoints.append({
                                "id": details.get("operationId", f"{method}_{path}"),
                                "method": method.upper(),
                                "path": path,
                                "summary": details.get("summary", ""),
                                "description": details.get("description", "")
                            })
        
        result = suggester.suggest_flows(
            endpoints or request.endpoints,
            request.specId
        )
        
        # Save suggested flows to Convex
        if request.userId:
            try:
                from .convex_client import get_convex_client
                convex = get_convex_client()
                await convex.save_suggested_flows(
                    flows=result["suggestedFlows"],
                    spec_id=request.specId,
                    user_id=request.userId
                )
            except Exception as e:
                logger.warning(f"Failed to save suggested flows to Convex: {e}")
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest flows: {str(e)}")


@app.post("/api/workflows/learn-pattern")
async def learn_pattern(request: LearnPatternRequest) -> Dict[str, Any]:
    """
    Learn patterns from reference workflow
    
    This endpoint analyzes a reference workflow and extracts reusable patterns
    that can be applied to future workflow generation. Saves pattern to Convex if userId provided.
    """
    try:
        learner = get_pattern_learner()
        result = learner.learn(
            request.referenceWorkflow,
            request.referenceEndpoints
        )
        
        # Save pattern to Convex
        if request.userId and request.specId:
            try:
                from .convex_client import get_convex_client
                import uuid
                convex = get_convex_client()
                pattern_id = str(uuid.uuid4())
                await convex.create_flow_pattern(
                    pattern_id=pattern_id,
                    name=request.referenceWorkflow.get("name", "Learned Pattern"),
                    spec_id=request.specId,
                    user_id=request.userId,
                    reference_workflow_id=request.referenceWorkflow.get("workflowId", pattern_id),
                    patterns=result["patterns"],
                    description=request.referenceWorkflow.get("description")
                )
                result["patternId"] = pattern_id
            except Exception as e:
                logger.warning(f"Failed to save pattern to Convex: {e}")
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to learn pattern: {str(e)}")


@app.post("/api/workflows/auto-build-flows")
async def auto_build(request: AutoBuildRequest) -> Dict[str, Any]:
    """
    Auto-build workflows using learned patterns
    
    This endpoint takes suggested workflow ideas and learned patterns, then
    constructs complete, executable workflows by combining them with the
    available API endpoints. Retrieves patterns from Convex if userId provided.
    """
    try:
        builder = get_auto_builder()
        
        # Fetch active pattern from Convex if userId provided and no patterns given
        learned_patterns = request.learnedPatterns
        if request.userId and not learned_patterns:
            try:
                from .convex_client import get_convex_client
                convex = get_convex_client()
                active_pattern = await convex.get_active_flow_pattern(
                    spec_id=request.specId,
                    user_id=request.userId
                )
                if active_pattern:
                    learned_patterns = active_pattern.get("patterns", {})
            except Exception as e:
                logger.warning(f"Failed to fetch pattern from Convex: {e}")
        
        # If spec_id provided and no endpoints, try to fetch from Convex  
        endpoints = request.endpoints
        if not endpoints and request.userId:
            try:
                from .convex_client import get_convex_client
                convex = get_convex_client()
                spec = await convex.get_api_spec(request.specId)
                if spec and spec.get("spec", {}).get("paths"):
                    # Extract endpoints from OpenAPI spec
                    endpoints = []
                    for path, methods in spec["spec"]["paths"].items():
                        for method, details in methods.items():
                            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                                endpoints.append({
                                    "id": details.get("operationId", f"{method}_{path}"),
                                    "method": method.upper(),
                                    "path": path,
                                    "summary": details.get("summary", ""),
                                    "description": details.get("description", ""),
                                    "parameters": details.get("parameters", [])
                                })
            except Exception as e:
                logger.warning(f"Failed to fetch spec from Convex: {e}")
        
        result = builder.build(
            request.suggestedFlows,
            learned_patterns or {},
            endpoints or request.endpoints,
            request.specId
        )
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-build flows: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
