"""
Auto Builder Service
Auto-builds workflows using learned patterns
Direct port of Next.js auto-build-flows logic
"""
import os
import json
from typing import List, Dict, Any
from openai import OpenAI


class AutoBuilder:
    """Auto-build workflows from suggestions and patterns"""
    
    def __init__(self):
        """Initialize the auto builder with OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def build(
        self,
        suggested_flows: List[Dict[str, Any]],
        learned_patterns: Dict[str, Any],
        endpoints: List[Dict[str, Any]],
        spec_id: str
    ) -> Dict[str, Any]:
        """
        Auto-build workflows using learned patterns
        
        Args:
            suggested_flows: List of suggested workflow ideas
            learned_patterns: Previously learned workflow patterns
            endpoints: Available API endpoints
            spec_id: OpenAPI specification ID
            
        Returns:
            Dictionary containing built workflows
        """
        system_prompt = """You are an API workflow construction expert. Given suggested workflow ideas, learned patterns, and available endpoints, construct complete, executable workflows.

Your task is to:
1. Take each suggested workflow idea
2. Apply the learned patterns to structure the workflow
3. Select specific endpoints and their order
4. Define parameter mappings between steps
5. Create a complete, executable workflow specification

Return your response as a JSON object with this structure:
{
  "workflows": [
    {
      "flow_id": "the suggestion id this workflow is based on",
      "workflow": {
        "name": "Workflow name",
        "description": "What this workflow does",
        "steps": [
          {
            "id": "step-0",
            "endpointId": "endpoint-id",
            "order": 0,
            "reasoning": "Why this endpoint and position",
            "parameters": {
              "paramName": "description of what value should be provided"
            },
            "conditionalLogic": {
              "condition": "optional condition"
            }
          }
        ],
        "specId": "spec-id"
      },
      "applied_patterns": ["list of pattern types applied"]
    }
  ]
}"""

        # Format the input data
        suggestions_text = self._format_suggestions(suggested_flows)
        patterns_text = self._format_patterns(learned_patterns)
        endpoints_text = self._format_endpoints(endpoints)
        
        user_prompt = f"""Suggested Workflows:
{suggestions_text}

Learned Patterns:
{patterns_text}

Available API Endpoints:
{endpoints_text}

Build complete workflows by applying the learned patterns to the suggestions."""

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
        
        ai_response = response.choices[0].message.content
        if not ai_response:
            raise ValueError("AI did not return a response")
            
        data = json.loads(ai_response)
        
        # Validate response structure
        if not data.get('workflows') or not isinstance(data['workflows'], list):
            raise ValueError("AI response is missing required 'workflows' array")
        
        # Add specId to each workflow
        for workflow_item in data['workflows']:
            if 'workflow' in workflow_item and 'specId' not in workflow_item['workflow']:
                workflow_item['workflow']['specId'] = spec_id
        
        return {
            "workflows": data['workflows']
        }
    
    def _format_suggestions(self, suggestions: List[Dict[str, Any]]) -> str:
        """Format suggested flows for the prompt"""
        return "\n\n".join([
            f"ID: {flow['id']}\n"
            f"Name: {flow['name']}\n"
            f"Description: {flow['description']}\n"
            f"Use Case: {flow.get('useCase', 'N/A')}\n"
            f"Category: {flow.get('category', 'N/A')}\n"
            f"Complexity: {flow.get('complexity', 'N/A')}\n"
            f"Suggested Endpoints: {', '.join(flow.get('endpoints', []))}"
            for flow in suggestions
        ])
    
    def _format_patterns(self, patterns: Dict[str, Any]) -> str:
        """Format learned patterns for the prompt"""
        return json.dumps(patterns, indent=2)
    
    def _format_endpoints(self, endpoints: List[Dict[str, Any]]) -> str:
        """Format endpoints list for the prompt"""
        return "\n\n---\n\n".join([
            f"ID: {ep['id']}\n"
            f"Method: {ep['method']}\n"
            f"Path: {ep['path']}\n"
            f"Summary: {ep.get('summary', 'N/A')}\n"
            f"Description: {ep.get('description', 'N/A')}\n"
            f"Parameters: {self._format_parameters(ep.get('parameters', []))}"
            for ep in endpoints
        ])
    
    def _format_parameters(self, params: List[Dict]) -> str:
        """Format parameter list as a string"""
        if not params:
            return "None"
        return ", ".join([
            f"{p['name']} ({p.get('in', 'query')}, {'required' if p.get('required') else 'optional'})"
            for p in params
        ])
