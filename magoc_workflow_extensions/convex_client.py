"""
Convex client for Python backend integration
Handles communication with Convex database for specs, patterns, suggested flows, and user preferences
"""
import os
import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ConvexClient:
    """
    Client for interacting with Convex database
    Provides methods to retrieve and store workflow-related data
    """

    def __init__(self, convex_url: Optional[str] = None):
        """
        Initialize Convex client

        Args:
            convex_url: Convex deployment URL (e.g., https://your-deployment.convex.cloud)
        """
        self.convex_url = convex_url or os.environ.get("CONVEX_URL")
        if not self.convex_url:
            raise ValueError(
                "CONVEX_URL must be provided or set in environment variables"
            )

        # Remove trailing slash if present
        self.convex_url = self.convex_url.rstrip("/")

        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"ConvexClient initialized with URL: {self.convex_url}")

    async def _query(self, function_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a Convex query

        Args:
            function_name: Name of the Convex function (e.g., "apiWorkflows:getAPISpec")
            args: Arguments to pass to the function

        Returns:
            Result from the Convex query
        """
        url = f"{self.convex_url}/api/query"
        payload = {"path": function_name, "args": args, "format": "json"}

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("value")
        except Exception as e:
            logger.error(f"Convex query error: {e}")
            raise

    async def _mutation(self, function_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a Convex mutation

        Args:
            function_name: Name of the Convex function
            args: Arguments to pass to the function

        Returns:
            Result from the Convex mutation
        """
        url = f"{self.convex_url}/api/mutation"
        payload = {"path": function_name, "args": args, "format": "json"}

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("value")
        except Exception as e:
            logger.error(f"Convex mutation error: {e}")
            raise

    # API Spec operations
    async def get_api_spec(self, spec_id: str) -> Optional[Dict[str, Any]]:
        """Get an API specification by ID"""
        return await self._query("apiWorkflows:getAPISpec", {"specId": spec_id})

    async def get_user_api_specs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API specs for a user"""
        return await self._query("apiWorkflows:getUserAPISpecs", {"userId": user_id})

    # Workflow operations
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID"""
        return await self._query("apiWorkflows:getWorkflow", {"workflowId": workflow_id})

    async def get_user_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a user"""
        return await self._query("apiWorkflows:getUserWorkflows", {"userId": user_id})

    async def save_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: Any,
        user_id: str,
        description: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Save a workflow to Convex"""
        return await self._mutation(
            "apiWorkflows:saveWorkflow",
            {
                "workflowId": workflow_id,
                "name": name,
                "description": description,
                "steps": steps,
                "userId": user_id,
                "workspaceId": workspace_id,
            },
        )

    # Suggested Flows operations
    async def get_suggested_flows(
        self, spec_id: str, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get suggested flows for a spec"""
        args = {"specId": spec_id}
        if user_id:
            args["userId"] = user_id
        return await self._query("suggestedFlows:getSuggestedFlows", args)

    async def save_suggested_flows(
        self, flows: List[Dict[str, Any]], spec_id: str, user_id: str
    ) -> List[str]:
        """Save suggested flows to Convex"""
        return await self._mutation(
            "suggestedFlows:saveSuggestedFlows",
            {"flows": flows, "specId": spec_id, "userId": user_id},
        )

    async def get_unconfigured_flows(
        self, spec_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get unconfigured suggested flows for a spec"""
        return await self._query(
            "suggestedFlows:getUnconfiguredFlows",
            {"specId": spec_id, "userId": user_id},
        )

    # Flow Patterns operations
    async def get_active_flow_pattern(
        self, spec_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the active flow pattern for a spec"""
        return await self._query(
            "flowPatterns:getActiveFlowPattern", {"specId": spec_id, "userId": user_id}
        )

    async def get_flow_patterns(
        self, spec_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all flow patterns for a spec"""
        return await self._query(
            "flowPatterns:getFlowPatterns", {"specId": spec_id, "userId": user_id}
        )

    async def create_flow_pattern(
        self,
        pattern_id: str,
        name: str,
        spec_id: str,
        user_id: str,
        reference_workflow_id: str,
        patterns: Dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """Create a new flow pattern"""
        return await self._mutation(
            "flowPatterns:createFlowPattern",
            {
                "patternId": pattern_id,
                "name": name,
                "description": description,
                "specId": spec_id,
                "userId": user_id,
                "referenceWorkflowId": reference_workflow_id,
                "patterns": patterns,
            },
        )

    async def update_flow_pattern_stats(
        self, pattern_id: str, user_id: str, increment: int = 1
    ):
        """Update flow pattern statistics after generating flows"""
        return await self._mutation(
            "flowPatterns:updateFlowPatternStats",
            {
                "patternId": pattern_id,
                "userId": user_id,
                "incrementGeneratedCount": increment,
            },
        )

    # User operations
    async def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await self._query("user:GetUser", {"email": email})

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global Convex client instance
_convex_client: Optional[ConvexClient] = None


def get_convex_client() -> ConvexClient:
    """Get or create the global Convex client instance"""
    global _convex_client
    if _convex_client is None:
        _convex_client = ConvexClient()
    return _convex_client
