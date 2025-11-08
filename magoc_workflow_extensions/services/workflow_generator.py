"""
Workflow Generator Service
Handles natural language to workflow conversion
Direct port of Next.js logic to Python backend
"""
import os
import json
from typing import List, Dict, Any
from openai import OpenAI


class WorkflowGenerator:
    """Generate workflows from natural language descriptions"""
    
    def __init__(self):
        """Initialize the workflow generator with OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def generate_from_nl(
        self, 
        description: str, 
        endpoints: List[Dict[str, Any]], 
        spec_id: str
    ) -> Dict[str, Any]:
        """
        Generate workflow from natural language description
        
        Args:
            description: Natural language description of desired workflow
            endpoints: List of available API endpoints
            spec_id: OpenAPI specification ID
            
        Returns:
            Dictionary containing workflow, explanation, and AI reasoning
        """
        # Build the exact same prompt as Next.js version
        system_prompt = """You are an API workflow expert. Given a natural language description of a desired flow or outcome, analyze which API endpoints should be used and in what order.

Your task is to:
1. Understand the user's intent from their natural language description
2. Select the most relevant endpoints from the available list
3. Determine the optimal order to call these endpoints
4. Provide parameter mappings and dependencies between steps

Return your response as a JSON object with this structure:
{
  "workflowName": "A clear name for this workflow",
  "workflowDescription": "A brief description of what this workflow does",
  "selectedEndpoints": [
    {
      "endpointId": "the endpoint ID",
      "order": 0,
      "reasoning": "why this endpoint was chosen and placed at this position",
      "parameters": {
        "paramName": "description of what value should be provided"
      },
      "dependsOn": ["list of previous step IDs this depends on"]
    }
  ],
  "explanation": "A detailed explanation of the workflow logic and data flow"
}"""

        # Format endpoints
        endpoints_list = "\n\n---\n\n".join([
            f"ID: {ep['id']}\n"
            f"Method: {ep['method']}\n"
            f"Path: {ep['path']}\n"
            f"Summary: {ep.get('summary', 'N/A')}\n"
            f"Description: {ep.get('description', 'N/A')}\n"
            f"Parameters: {self._format_parameters(ep.get('parameters', []))}"
            for ep in endpoints
        ])
        
        user_prompt = f"""User's desired flow/outcome:
"{description}"

Available API endpoints:
{endpoints_list}

Analyze this and create an optimal workflow."""

        # Call OpenAI with same parameters as Next.js
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
        
        # Parse and transform response
        ai_response = response.choices[0].message.content
        if not ai_response:
            raise ValueError("AI did not return a response")
            
        workflow_data = json.loads(ai_response)
        
        # Validate response structure
        if not workflow_data.get('selectedEndpoints') or not isinstance(workflow_data['selectedEndpoints'], list):
            raise ValueError("AI response is missing required 'selectedEndpoints' array")
        
        # Transform to expected format
        steps = [
            {
                "id": f"step-{ep['order']}",
                "endpointId": ep['endpointId'],
                "order": ep['order'],
                "reasoning": ep['reasoning'],
                "parameters": ep.get('parameters', {}),
                "conditionalLogic": {
                    "condition": f"depends on {', '.join(ep['dependsOn'])}"
                } if ep.get('dependsOn') else None
            }
            for ep in workflow_data['selectedEndpoints']
        ]
        
        return {
            "workflow": {
                "name": workflow_data['workflowName'],
                "description": workflow_data['workflowDescription'],
                "steps": steps,
                "specId": spec_id
            },
            "explanation": workflow_data['explanation'],
            "aiReasoning": [
                {
                    "endpointId": ep['endpointId'],
                    "reasoning": ep['reasoning']
                }
                for ep in workflow_data['selectedEndpoints']
            ]
        }
    
    def _format_parameters(self, params: List[Dict]) -> str:
        """Format parameter list as a string"""
        if not params:
            return "None"
        return ", ".join([
            f"{p['name']} ({p.get('in', 'query')}, {'required' if p.get('required') else 'optional'})"
            for p in params
        ])
