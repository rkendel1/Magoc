# Convex Integration Guide

## Overview

The Magoc Workflow Extensions backend integrates with Convex to provide persistent storage for API specifications, workflows, suggested flows, learned patterns, and user preferences. This integration enables seamless data sharing between the Next.js frontend and the Python backend.

## Architecture

```
Next.js Frontend (Boltq)
        ↓
    Convex Database
        ↓
Python Backend (Magoc Workflow Extensions)
```

The backend can:
- **Read** from Convex: API specs, workflows, patterns, user preferences
- **Write** to Convex: Generated workflows, suggested flows, learned patterns

## Setup

### 1. Configure Convex URL

Set your Convex deployment URL in the environment:

```bash
export CONVEX_URL=https://your-deployment.convex.cloud
```

Or in `.env` file:

```bash
CONVEX_URL=https://your-deployment.convex.cloud
```

### 2. Convex Schema

The backend integrates with the following Convex tables:

#### `apiSpecs`
Stores OpenAPI specifications:
```typescript
{
  specId: string,
  name: string,
  version: string,
  description?: string,
  spec: any, // Full OpenAPI spec
  user: Id<"users">,
  createdAt: number,
  updatedAt: number
}
```

#### `apiWorkflows`
Stores generated workflows:
```typescript
{
  workflowId: string,
  name: string,
  description?: string,
  steps: any[],
  user: Id<"users">,
  workspace?: Id<"workspaces">,
  specId?: string,
  createdAt: number,
  updatedAt: number
}
```

#### `suggestedFlows`
Stores AI-suggested workflows:
```typescript
{
  flowId: string,
  name: string,
  description: string,
  useCase: string,
  category: string,
  complexity: string,
  endpoints: string[],
  specId: string,
  user: Id<"users">,
  isConfigured?: boolean,
  createdAt: number,
  updatedAt: number
}
```

#### `flowPatterns`
Stores learned workflow patterns:
```typescript
{
  patternId: string,
  name: string,
  description?: string,
  specId: string,
  user: Id<"users">,
  referenceWorkflowId: string,
  patterns: any, // Learned patterns
  isActive?: boolean,
  generatedFlowsCount?: number,
  createdAt: number,
  updatedAt: number
}
```

## Usage

### API Endpoints with Convex Integration

All endpoints support an optional `userId` field. When provided, the backend will:
1. Fetch data from Convex
2. Save generated results back to Convex
3. Associate data with the user

#### Generate Workflow from Natural Language

**With Convex Integration:**
```bash
curl -X POST http://localhost:8000/api/workflows/generate-from-nl \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a user and send welcome email",
    "specId": "api-spec-123",
    "userId": "user_abc123",
    "endpoints": []  # Empty - will fetch from Convex
  }'
```

**What happens:**
1. Backend fetches API spec from Convex using `specId`
2. Extracts endpoints from the spec
3. Generates workflow using AI
4. Saves workflow to Convex associated with `userId`

#### Suggest Workflows

**With Convex Integration:**
```bash
curl -X POST http://localhost:8000/api/workflows/suggest-flows \
  -H "Content-Type: application/json" \
  -d '{
    "specId": "api-spec-123",
    "userId": "user_abc123",
    "endpoints": []  # Empty - will fetch from Convex
  }'
```

**What happens:**
1. Backend fetches API spec from Convex
2. Generates workflow suggestions
3. Saves suggestions to Convex for the user

#### Learn Pattern

**With Convex Integration:**
```bash
curl -X POST http://localhost:8000/api/workflows/learn-pattern \
  -H "Content-Type: application/json" \
  -d '{
    "referenceWorkflow": {...},
    "referenceEndpoints": [...],
    "userId": "user_abc123",
    "specId": "api-spec-123"
  }'
```

**What happens:**
1. Backend analyzes the reference workflow
2. Extracts reusable patterns
3. Saves pattern to Convex as active for the spec

#### Auto-Build Workflows

**With Convex Integration:**
```bash
curl -X POST http://localhost:8000/api/workflows/auto-build-flows \
  -H "Content-Type: application/json" \
  -d '{
    "suggestedFlows": [...],
    "learnedPatterns": {},  # Empty - will fetch from Convex
    "specId": "api-spec-123",
    "userId": "user_abc123",
    "endpoints": []  # Empty - will fetch from Convex
  }'
```

**What happens:**
1. Backend fetches active flow pattern from Convex
2. Backend fetches API spec to get endpoints
3. Generates complete workflows using patterns
4. Returns built workflows

## Convex Client API

The `ConvexClient` class provides methods for interacting with Convex:

### Initialize Client

```python
from magoc_workflow_extensions.convex_client import get_convex_client

convex = get_convex_client()
```

### API Spec Operations

```python
# Get a specific API spec
spec = await convex.get_api_spec("spec-id-123")

# Get all specs for a user
specs = await convex.get_user_api_specs("user_abc123")
```

### Workflow Operations

```python
# Get a workflow
workflow = await convex.get_workflow("workflow-id-123")

# Get all workflows for a user
workflows = await convex.get_user_workflows("user_abc123")

# Save a workflow
workflow_id = await convex.save_workflow(
    workflow_id="workflow-123",
    name="User Registration",
    steps=[...],
    user_id="user_abc123"
)
```

### Suggested Flows Operations

```python
# Get suggested flows for a spec
flows = await convex.get_suggested_flows("spec-id-123", "user_abc123")

# Save suggested flows
flow_ids = await convex.save_suggested_flows(
    flows=[...],
    spec_id="spec-id-123",
    user_id="user_abc123"
)

# Get unconfigured flows
unconfigured = await convex.get_unconfigured_flows("spec-id-123", "user_abc123")
```

### Flow Pattern Operations

```python
# Get active pattern for a spec
pattern = await convex.get_active_flow_pattern("spec-id-123", "user_abc123")

# Get all patterns for a spec
patterns = await convex.get_flow_patterns("spec-id-123", "user_abc123")

# Create a new pattern
pattern_id = await convex.create_flow_pattern(
    pattern_id="pattern-123",
    name="CRUD Pattern",
    spec_id="spec-id-123",
    user_id="user_abc123",
    reference_workflow_id="workflow-123",
    patterns={...}
)

# Update pattern statistics
await convex.update_flow_pattern_stats(
    pattern_id="pattern-123",
    user_id="user_abc123",
    increment=1
)
```

## Data Flow Examples

### Example 1: Complete Workflow Generation

```
User Request (Frontend)
    ↓
1. Frontend sends to Backend:
   - description: "Create user and send email"
   - specId: "api-123"
   - userId: "user-abc"
    ↓
2. Backend queries Convex:
   - Fetches API spec "api-123"
   - Extracts endpoints from spec
    ↓
3. Backend generates workflow with AI
    ↓
4. Backend saves to Convex:
   - Workflow with steps
   - Associated with userId
    ↓
5. Backend returns to Frontend:
   - Generated workflow
   - Workflow ID for reference
```

### Example 2: Pattern-Based Auto-Generation

```
User Request (Frontend)
    ↓
1. Frontend sends to Backend:
   - suggestedFlows: [flow1, flow2]
   - specId: "api-123"
   - userId: "user-abc"
   - learnedPatterns: {} (empty)
    ↓
2. Backend queries Convex:
   - Fetches active flow pattern for spec
   - Fetches API spec for endpoints
    ↓
3. Backend generates workflows:
   - Applies learned patterns
   - Uses spec endpoints
    ↓
4. Backend returns to Frontend:
   - Complete workflows
   - Applied patterns info
```

## Error Handling

The backend implements graceful degradation:

- **Convex unavailable**: Backend continues with provided data, logs warning
- **Missing data**: Backend returns clear error messages
- **Save failures**: Backend logs warnings but doesn't fail the request

## Best Practices

1. **Always provide userId**: Enables Convex integration and data persistence
2. **Use specId consistently**: Links workflows, patterns, and suggestions
3. **Cache frequently used specs**: Reduces Convex query load
4. **Handle empty responses**: Check if Convex returns data before using it
5. **Monitor Convex logs**: Track usage and identify issues

## Testing

### Test Convex Integration

```python
# Test connecting to Convex
from magoc_workflow_extensions.convex_client import ConvexClient

async def test_convex():
    convex = ConvexClient(convex_url="https://your-deployment.convex.cloud")
    
    # Test query
    spec = await convex.get_api_spec("test-spec-id")
    print(f"Got spec: {spec}")
    
    await convex.close()
```

### Test API with Convex

```bash
# Set environment
export CONVEX_URL=https://your-deployment.convex.cloud
export OPENAI_API_KEY=your-key

# Start server
./scripts/start_workflow_api.sh

# Test endpoint
curl -X POST http://localhost:8000/api/workflows/suggest-flows \
  -H "Content-Type: application/json" \
  -d '{
    "specId": "existing-spec-id",
    "userId": "existing-user-id",
    "endpoints": []
  }'
```

## Troubleshooting

### "CONVEX_URL not set" Error

```bash
export CONVEX_URL=https://your-deployment.convex.cloud
```

### Connection Timeout

- Check Convex deployment status
- Verify URL is correct (no trailing slash)
- Check network connectivity

### Data Not Found

- Verify specId exists in Convex
- Verify userId has access to the data
- Check Convex logs for permission issues

## Security Considerations

1. **API Keys**: Never expose Convex URLs with sensitive data in public
2. **User Isolation**: Backend respects user-based data access
3. **Validation**: All data from Convex is validated before use
4. **Error Messages**: Don't leak sensitive information in errors

## Performance

- **Connection Pooling**: httpx client reuses connections
- **Async Operations**: All Convex operations are async
- **Timeout**: 30-second timeout on all operations
- **Retry Logic**: Consider adding retry logic for production

## Next Steps

- [ ] Add caching layer for frequently accessed specs
- [ ] Implement retry logic with exponential backoff
- [ ] Add Convex webhook support for real-time updates
- [ ] Add monitoring and metrics for Convex operations
