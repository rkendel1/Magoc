"""
Flow Suggester Service
Analyzes APIs and suggests common workflows
Direct port of Next.js suggest-flows logic
"""
import os
import json
from typing import List, Dict, Any
from openai import OpenAI


class FlowSuggester:
    """Suggest workflows based on API analysis"""
    
    def __init__(self):
        """Initialize the flow suggester with OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def suggest_flows(self, endpoints: List[Dict[str, Any]], spec_id: str) -> Dict[str, Any]:
        """
        Suggest workflows based on API endpoint analysis
        
        Args:
            endpoints: List of available API endpoints
            spec_id: OpenAPI specification ID
            
        Returns:
            Dictionary containing suggested flows and API summary
        """
        system_prompt = """You are an API workflow expert. Given a list of API endpoints, analyze them and suggest practical, useful workflows that can be created.

Your task is to:
1. Understand what the API does based on its endpoints
2. Identify common use cases and workflows that users might want to create
3. Suggest 5-8 diverse workflows covering different complexity levels and use cases
4. For each workflow, specify which endpoints would be used and in what general order

Return your response as a JSON object with this structure:
{
  "suggestedFlows": [
    {
      "id": "unique-flow-id",
      "name": "Clear, concise workflow name",
      "description": "One sentence description of what this workflow does",
      "useCase": "Detailed explanation of when and why a user would use this workflow",
      "endpoints": ["endpoint-id-1", "endpoint-id-2"],
      "category": "CRUD|Integration|Analytics|Notification|Automation|Data Processing",
      "complexity": "simple|moderate|complex"
    }
  ],
  "apiSummary": "A brief summary of what this API is designed to do based on the endpoints"
}"""

        # Format endpoints same as Next.js
        endpoints_list = self._format_endpoints(endpoints)
        
        user_prompt = f"""Available API endpoints:
{endpoints_list}

Analyze this API and suggest practical workflows."""

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
        if not data.get('suggestedFlows') or not isinstance(data['suggestedFlows'], list):
            raise ValueError("AI response is missing required 'suggestedFlows' array")
        
        return {
            "suggestedFlows": data['suggestedFlows'],
            "apiSummary": data.get('apiSummary', 'API analysis complete'),
            "specId": spec_id
        }
    
    def _format_endpoints(self, endpoints: List[Dict[str, Any]]) -> str:
        """Format endpoints list for the prompt"""
        return "\n\n---\n\n".join([
            f"ID: {ep['id']}\n"
            f"Method: {ep['method']}\n"
            f"Path: {ep['path']}\n"
            f"Summary: {ep.get('summary', 'N/A')}\n"
            f"Description: {ep.get('description', 'N/A')}"
            for ep in endpoints
        ])
