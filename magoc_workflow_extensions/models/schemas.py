"""
Pydantic models for request/response schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """API parameter definition"""
    name: str
    in_: str = Field(alias="in")
    required: bool = False
    type: Optional[str] = None
    description: Optional[str] = None


class Endpoint(BaseModel):
    """API endpoint definition"""
    id: str
    method: str
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Parameter] = []


class WorkflowStep(BaseModel):
    """Workflow step definition"""
    id: str
    endpointId: str
    order: int
    reasoning: str
    parameters: Dict[str, str] = {}
    conditionalLogic: Optional[Dict[str, Any]] = None


class Workflow(BaseModel):
    """Workflow definition"""
    name: str
    description: str
    steps: List[WorkflowStep]
    specId: str


class GenerateWorkflowRequest(BaseModel):
    """Request for generating workflow from natural language"""
    description: str = Field(..., description="Natural language description of the workflow")
    endpoints: List[Dict[str, Any]] = Field(..., description="Available API endpoints")
    specId: str = Field(..., description="OpenAPI spec ID")


class AIReasoning(BaseModel):
    """AI reasoning for endpoint selection"""
    endpointId: str
    reasoning: str


class GenerateWorkflowResponse(BaseModel):
    """Response from workflow generation"""
    workflow: Dict[str, Any]
    explanation: str
    aiReasoning: List[AIReasoning]


class SuggestFlowsRequest(BaseModel):
    """Request for suggesting workflows"""
    endpoints: List[Dict[str, Any]] = Field(..., description="Available API endpoints")
    specId: str = Field(..., description="OpenAPI spec ID")


class SuggestedFlow(BaseModel):
    """A suggested workflow"""
    id: str
    name: str
    description: str
    useCase: str
    endpoints: List[str]
    category: str
    complexity: str


class SuggestFlowsResponse(BaseModel):
    """Response from flow suggestion"""
    suggestedFlows: List[SuggestedFlow]
    apiSummary: str
    specId: str


class LearnPatternRequest(BaseModel):
    """Request for learning workflow patterns"""
    referenceWorkflow: Dict[str, Any] = Field(..., description="Reference workflow to learn from")
    referenceEndpoints: List[Dict[str, Any]] = Field(..., description="Endpoints used in workflow")


class WorkflowPattern(BaseModel):
    """Learned workflow pattern"""
    structure: Dict[str, Any]
    parameters: Dict[str, Any]
    interactions: Dict[str, Any]


class LearnPatternResponse(BaseModel):
    """Response from pattern learning"""
    patterns: WorkflowPattern
    confidence: float


class AutoBuildRequest(BaseModel):
    """Request for auto-building workflows"""
    suggestedFlows: List[Dict[str, Any]] = Field(..., description="Suggested flows to build")
    learnedPatterns: Dict[str, Any] = Field(..., description="Previously learned patterns")
    endpoints: List[Dict[str, Any]] = Field(..., description="Available API endpoints")
    specId: str = Field(..., description="OpenAPI spec ID")


class BuiltWorkflow(BaseModel):
    """A workflow built from patterns"""
    flow_id: str
    workflow: Dict[str, Any]
    applied_patterns: List[str]


class AutoBuildResponse(BaseModel):
    """Response from auto-building"""
    workflows: List[BuiltWorkflow]
