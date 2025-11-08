"""
Data models for workflow operations
"""
from .schemas import (
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    SuggestFlowsRequest,
    SuggestFlowsResponse,
    LearnPatternRequest,
    LearnPatternResponse,
    AutoBuildRequest,
    AutoBuildResponse,
    Endpoint,
    WorkflowStep,
    Workflow,
    SuggestedFlow,
)

__all__ = [
    "GenerateWorkflowRequest",
    "GenerateWorkflowResponse",
    "SuggestFlowsRequest",
    "SuggestFlowsResponse",
    "LearnPatternRequest",
    "LearnPatternResponse",
    "AutoBuildRequest",
    "AutoBuildResponse",
    "Endpoint",
    "WorkflowStep",
    "Workflow",
    "SuggestedFlow",
]
