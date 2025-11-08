"""
Pattern Learner Service
Learns patterns from reference workflows
Direct port of Next.js learn-pattern logic
"""
import os
import json
from typing import Dict, Any, List
from openai import OpenAI


class PatternLearner:
    """Learn workflow patterns from reference implementations"""
    
    def __init__(self):
        """Initialize the pattern learner with OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def learn(
        self,
        reference_workflow: Dict[str, Any],
        reference_endpoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn patterns from a reference workflow
        
        Args:
            reference_workflow: The workflow to learn from
            reference_endpoints: Endpoints used in the workflow
            
        Returns:
            Dictionary containing learned patterns and confidence score
        """
        system_prompt = """You are an API workflow pattern recognition expert. Given a reference workflow and its endpoints, analyze it to extract reusable patterns.

Your task is to:
1. Identify the structural pattern (sequential, parallel, conditional, etc.)
2. Extract parameter mapping strategies (how data flows between steps)
3. Recognize interaction patterns (CRUD operations, chains, etc.)
4. Determine what makes this workflow effective

Return your response as a JSON object with this structure:
{
  "patterns": {
    "structure": {
      "type": "sequential|parallel|conditional|hybrid",
      "description": "How steps are organized and executed"
    },
    "parameters": {
      "mappingStrategy": "Description of how parameters are passed between steps",
      "commonMappings": ["list of common parameter mappings like 'output.id -> input.userId'"]
    },
    "interactions": {
      "pattern": "CRUD|Chain|Fan-out|Fan-in|Pipeline",
      "description": "How endpoints interact with each other"
    }
  },
  "confidence": 0.95
}"""

        # Format the workflow for analysis
        workflow_description = self._format_workflow(reference_workflow, reference_endpoints)
        
        user_prompt = f"""Reference workflow to analyze:

{workflow_description}

Extract reusable patterns from this workflow."""

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
        if not data.get('patterns'):
            raise ValueError("AI response is missing required 'patterns' object")
        
        return {
            "patterns": data['patterns'],
            "confidence": data.get('confidence', 0.8)
        }
    
    def _format_workflow(
        self,
        workflow: Dict[str, Any],
        endpoints: List[Dict[str, Any]]
    ) -> str:
        """Format workflow and endpoints for analysis"""
        # Create endpoint lookup
        endpoint_map = {ep['id']: ep for ep in endpoints}
        
        # Format workflow steps
        steps_description = []
        for step in workflow.get('steps', []):
            endpoint = endpoint_map.get(step.get('endpointId'))
            if endpoint:
                step_desc = (
                    f"Step {step.get('order', 'N/A')}: {step.get('id', 'N/A')}\n"
                    f"  Endpoint: {endpoint['method']} {endpoint['path']}\n"
                    f"  Reasoning: {step.get('reasoning', 'N/A')}\n"
                    f"  Parameters: {json.dumps(step.get('parameters', {}), indent=4)}"
                )
                if step.get('conditionalLogic'):
                    step_desc += f"\n  Conditional: {step['conditionalLogic']}"
                steps_description.append(step_desc)
        
        return f"""Workflow Name: {workflow.get('name', 'N/A')}
Description: {workflow.get('description', 'N/A')}

Steps:
{chr(10).join(steps_description)}

Available Endpoints:
{self._format_endpoints(endpoints)}"""
    
    def _format_endpoints(self, endpoints: List[Dict[str, Any]]) -> str:
        """Format endpoints list"""
        return "\n".join([
            f"- {ep['id']}: {ep['method']} {ep['path']}"
            for ep in endpoints
        ])
