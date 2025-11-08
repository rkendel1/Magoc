# Magoc Workflow Extensions

FastAPI backend for AI-powered API workflow generation integrated with the Magoc MCP toolkit.

## Overview

This module provides REST API endpoints for workflow generation that integrate seamlessly with Next.js frontend applications. It's designed to work as part of the larger Magoc ecosystem for API evaluation and testing.

## Features

- **Natural Language to Workflow**: Convert plain English descriptions into executable API workflows using GPT-4
- **Flow Suggestions**: Analyze API endpoints and automatically suggest practical workflows
- **Pattern Learning**: Learn from reference workflows to improve future generations
- **Auto-Building**: Automatically construct complete workflows from suggestions and learned patterns

## Architecture

### Services

- `WorkflowGenerator`: Generates workflows from natural language descriptions
- `FlowSuggester`: Suggests workflows based on API endpoint analysis  
- `PatternLearner`: Extracts reusable patterns from reference workflows
- `AutoBuilder`: Constructs complete workflows using learned patterns

### API Endpoints

All endpoints follow REST best practices and return consistent JSON responses.

#### POST `/api/workflows/generate-from-nl`
Generate a workflow from a natural language description.

#### POST `/api/workflows/suggest-flows`
Suggest workflows based on API analysis.

#### POST `/api/workflows/learn-pattern`
Learn patterns from a reference workflow.

#### POST `/api/workflows/auto-build-flows`
Auto-build workflows using learned patterns.

#### GET `/`
Root endpoint returning service status and version.

#### GET `/health`
Health check endpoint.

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Quick Start

```bash
# Install dependencies
pip install -r requirements-workflow.txt

# Set environment variables
export OPENAI_API_KEY=your-openai-api-key

# Run the server
uvicorn magoc_workflow_extensions.api:app --reload --port 8000
```

### Using uv (Recommended)

```bash
# Install with uv
uv pip install -r requirements-workflow.txt

# Run with uv
uv run uvicorn magoc_workflow_extensions.api:app --reload --port 8000
```

## Configuration

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black magoc_workflow_extensions/

# Lint code  
ruff check magoc_workflow_extensions/
```

## Integration with Magoc

This module is designed to integrate with the broader Magoc ecosystem:

1. **MCP Tools**: Can be accessed via MCP protocol for AI agent integration
2. **CLI Integration**: Accessible through `automagik-tools` CLI
3. **Next.js Frontend**: Provides backend for conversational UI applications

## API Response Format

All endpoints return a consistent response format:

```json
{
  "success": true,
  "data": {
    // Endpoint-specific response data
  }
}
```

Error responses:

```json
{
  "success": false,
  "detail": "Error message"
}
```

## CORS Configuration

CORS is configured to allow all origins during development. For production, update the `allow_origins` in `api.py` to restrict to your frontend domain.

## Docker Support

```bash
# Build image
docker build -t magoc-workflow-extensions -f Dockerfile .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  magoc-workflow-extensions
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please ensure:
1. Code follows Python best practices
2. All endpoints have proper error handling
3. Tests are included for new features
4. Documentation is updated

## Support

For issues and questions, please open an issue on the GitHub repository.
