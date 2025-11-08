"""
FastAPI application for Magoc Workflow Extensions
Provides REST API endpoints for AI-powered workflow generation
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

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
    optimal execution order.
    """
    try:
        generator = get_workflow_generator()
        result = generator.generate_from_nl(
            request.description,
            request.endpoints,
            request.specId
        )
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
    workflows that users might want to create.
    """
    try:
        suggester = get_flow_suggester()
        result = suggester.suggest_flows(
            request.endpoints,
            request.specId
        )
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
    that can be applied to future workflow generation.
    """
    try:
        learner = get_pattern_learner()
        result = learner.learn(
            request.referenceWorkflow,
            request.referenceEndpoints
        )
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
    available API endpoints.
    """
    try:
        builder = get_auto_builder()
        result = builder.build(
            request.suggestedFlows,
            request.learnedPatterns,
            request.endpoints,
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
