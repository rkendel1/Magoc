# Workflow Extensions - Quick Start Guide

## Overview

The Magoc Workflow Extensions provide a FastAPI backend for AI-powered API workflow generation. This guide will help you get started quickly.

## Installation

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements-workflow.txt

# Or using the existing Magoc setup
make install  # This installs all Magoc dependencies
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY=your-openai-api-key-here
```

Or create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

## Starting the Server

### Quick Start

```bash
# Using the startup script (recommended)
./scripts/start_workflow_api.sh

# Or manually with uvicorn
uvicorn magoc_workflow_extensions.api:app --reload --port 8000
```

### Development Mode

```bash
# With auto-reload
RELOAD=true ./scripts/start_workflow_api.sh

# Or
uvicorn magoc_workflow_extensions.api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Multiple workers
uvicorn magoc_workflow_extensions.api:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Example Usage

### 1. Generate Workflow from Natural Language

```bash
curl -X POST http://localhost:8000/api/workflows/generate-from-nl \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a new user and send them a welcome email",
    "endpoints": [
      {
        "id": "create-user",
        "method": "POST",
        "path": "/users",
        "summary": "Create a new user"
      },
      {
        "id": "send-email",
        "method": "POST",
        "path": "/emails/send",
        "summary": "Send an email"
      }
    ],
    "specId": "my-api-v1"
  }'
```

### 2. Suggest Workflows

```bash
curl -X POST http://localhost:8000/api/workflows/suggest-flows \
  -H "Content-Type: application/json" \
  -d '{
    "endpoints": [
      {
        "id": "list-users",
        "method": "GET",
        "path": "/users",
        "summary": "List all users"
      },
      {
        "id": "create-user",
        "method": "POST",
        "path": "/users",
        "summary": "Create a user"
      }
    ],
    "specId": "my-api-v1"
  }'
```

### 3. Learn Pattern from Reference Workflow

```bash
curl -X POST http://localhost:8000/api/workflows/learn-pattern \
  -H "Content-Type: application/json" \
  -d '{
    "referenceWorkflow": {
      "name": "User Registration Flow",
      "description": "Complete user registration",
      "steps": [
        {
          "id": "step-1",
          "endpointId": "create-user",
          "order": 0,
          "reasoning": "First create the user account"
        }
      ]
    },
    "referenceEndpoints": [
      {
        "id": "create-user",
        "method": "POST",
        "path": "/users"
      }
    ]
  }'
```

### 4. Auto-Build Workflows

```bash
curl -X POST http://localhost:8000/api/workflows/auto-build-flows \
  -H "Content-Type: application/json" \
  -d '{
    "suggestedFlows": [
      {
        "id": "flow-1",
        "name": "User Onboarding",
        "description": "Complete user onboarding process",
        "endpoints": ["create-user", "send-email"]
      }
    ],
    "learnedPatterns": {
      "structure": {"type": "sequential"}
    },
    "endpoints": [
      {
        "id": "create-user",
        "method": "POST",
        "path": "/users"
      }
    ],
    "specId": "my-api-v1"
  }'
```

### 5. Health Check

```bash
curl http://localhost:8000/health
```

## Integration with Next.js Frontend

### Environment Configuration

In your Next.js `.env.local`:

```bash
NEXT_PUBLIC_MAGOC_BACKEND_URL=http://localhost:8000
```

### Example Fetch Request

```typescript
async function generateWorkflow(description: string, endpoints: any[]) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_MAGOC_BACKEND_URL}/api/workflows/generate-from-nl`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      description,
      endpoints,
      specId: 'my-api-spec'
    })
  });
  
  const result = await response.json();
  return result.data;
}
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all workflow extension tests
pytest tests/workflow_extensions/ -v

# Run with coverage
pytest tests/workflow_extensions/ --cov=magoc_workflow_extensions
```

### Manual Testing with Swagger UI

1. Start the server
2. Open http://localhost:8000/docs
3. Try out the endpoints interactively

## Troubleshooting

### "OPENAI_API_KEY not set" Error

Make sure to export the environment variable before starting the server:

```bash
export OPENAI_API_KEY=your-key-here
./scripts/start_workflow_api.sh
```

### Port Already in Use

Change the port:

```bash
PORT=8001 ./scripts/start_workflow_api.sh
```

Or:

```bash
uvicorn magoc_workflow_extensions.api:app --port 8001
```

### Import Errors

Make sure dependencies are installed:

```bash
pip install -r requirements-workflow.txt
```

## Docker Deployment

### Build Image

```bash
docker build -t magoc-workflow-api -f Dockerfile.workflow .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  magoc-workflow-api
```

## Advanced Configuration

### Custom Host and Port

```bash
HOST=0.0.0.0 PORT=9000 ./scripts/start_workflow_api.sh
```

### With Workers (Production)

```bash
uvicorn magoc_workflow_extensions.api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Behind Reverse Proxy

Configure your reverse proxy (nginx, traefik, etc.) to forward to the backend:

```nginx
location /api/workflows {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Need Help?

- Check the main repository README: `/README.md`
- View API documentation: http://localhost:8000/docs
- Open an issue on GitHub
