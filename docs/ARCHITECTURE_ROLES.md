# System Architecture - Roles and Responsibilities

## Overview

The Magoc Workflow Extensions system consists of three main components that work together to provide AI-powered API workflow generation:

1. **Next.js Frontend (Boltq)** - User interface and orchestration
2. **Convex Database** - Data persistence and real-time sync
3. **Python Backend (Magoc)** - AI processing and workflow generation

This document explains exactly what each component does and how they interact.

---

## 🖥️ Frontend (Next.js / Boltq) - Responsibilities

### What the Frontend Does

#### 1. **User Interface & Interaction**
- Displays conversational UI for users to describe desired workflows
- Renders workflow visualization and editing interfaces
- Shows API specification details and endpoint lists
- Provides forms for configuring workflow parameters
- Displays AI-generated suggestions and patterns

#### 2. **User Session Management**
- Handles user authentication and authorization
- Manages user sessions and workspace context
- Tracks user preferences and UI state
- Maintains conversation history

#### 3. **Data Management (via Convex)**
- Stores user data in Convex (specs, workflows, preferences)
- Retrieves user's API specifications from Convex
- Fetches user's workflows and patterns from Convex
- Saves user preferences and UI state to Convex
- Manages tab snapshots and conversation state

#### 4. **Request Orchestration**
- Collects user input from conversational interface
- Prepares request data (description, endpoints, specId, userId)
- Makes HTTP requests to Python backend
- Handles loading states and error feedback
- Displays AI-generated results to user

#### 5. **Workflow Management**
- Allows users to edit generated workflows
- Enables saving workflows for later use
- Provides workflow execution triggers
- Displays workflow execution results

### What the Frontend Does NOT Do
❌ Does NOT generate workflows with AI (delegates to backend)
❌ Does NOT analyze API endpoints (delegates to backend)
❌ Does NOT learn patterns from workflows (delegates to backend)
❌ Does NOT call OpenAI directly (delegates to backend)

### Frontend Data Flow

```
User Input
    ↓
Frontend UI
    ↓
[Fetch existing data from Convex]
    ↓
[Send request to Backend with userId + specId]
    ↓
[Wait for Backend response]
    ↓
[Save results to Convex]
    ↓
Display Results to User
```

---

## 💾 Convex Database - Responsibilities

### What Convex Does

#### 1. **Data Storage**
Stores persistent data for the entire system:

**API Specifications**
```typescript
{
  specId: string,           // Unique identifier
  name: string,             // API name
  version: string,          // API version
  spec: object,             // Full OpenAPI specification
  user: Id<"users">,        // Owner
  createdAt: number,
  updatedAt: number
}
```

**Workflows**
```typescript
{
  workflowId: string,       // Unique identifier
  name: string,             // Workflow name
  description: string,      // What it does
  steps: array,             // Workflow steps
  user: Id<"users">,        // Owner
  specId: string,           // Associated API spec
  createdAt: number,
  updatedAt: number
}
```

**Suggested Flows**
```typescript
{
  flowId: string,           // Unique identifier
  name: string,             // Flow name
  description: string,      // What it does
  useCase: string,          // When to use it
  category: string,         // Flow category
  complexity: string,       // simple|moderate|complex
  endpoints: array,         // Required endpoints
  specId: string,           // Associated API spec
  user: Id<"users">,        // Owner
  isConfigured: boolean,    // Has user configured?
  createdAt: number,
  updatedAt: number
}
```

**Flow Patterns**
```typescript
{
  patternId: string,        // Unique identifier
  name: string,             // Pattern name
  patterns: object,         // Learned patterns
  specId: string,           // Associated API spec
  user: Id<"users">,        // Owner
  referenceWorkflowId: string, // Source workflow
  isActive: boolean,        // Currently in use?
  generatedFlowsCount: number, // Usage stats
  createdAt: number,
  updatedAt: number
}
```

**User Data**
```typescript
{
  name: string,
  email: string,
  pic: string,
  uid: string
}
```

#### 2. **Real-Time Synchronization**
- Syncs data between frontend and backend in real-time
- Notifies frontend when data changes
- Ensures consistency across all components

#### 3. **Query Interface**
Provides read access to data:
- `getAPISpec(specId)` - Fetch a specific API spec
- `getUserWorkflows(userId)` - Get all user workflows
- `getSuggestedFlows(specId, userId)` - Get suggested flows
- `getActiveFlowPattern(specId, userId)` - Get active pattern

#### 4. **Mutation Interface**
Provides write access to data:
- `saveAPISpec(...)` - Store new API spec
- `saveWorkflow(...)` - Store generated workflow
- `saveSuggestedFlows(...)` - Store AI suggestions
- `createFlowPattern(...)` - Store learned pattern

### What Convex Does NOT Do
❌ Does NOT generate workflows (delegates to backend)
❌ Does NOT make AI decisions (delegates to backend)
❌ Does NOT call OpenAI (delegates to backend)
❌ Does NOT process natural language (delegates to backend)

### Convex Data Flow

```
Frontend writes data
    ↓
Convex stores data
    ↓
Backend reads data when needed
    ↓
Backend processes with AI
    ↓
Backend writes results
    ↓
Convex stores results
    ↓
Frontend reads and displays
```

---

## 🐍 Python Backend (Magoc) - Responsibilities

### What the Backend Does

#### 1. **AI-Powered Workflow Generation**
Takes natural language descriptions and generates executable workflows:

**Input:**
- Natural language description: "Create a user and send welcome email"
- API spec ID: "api-123"
- User ID: "user-abc"

**Process:**
1. Fetch API spec from Convex (if not provided)
2. Extract available endpoints from spec
3. Call OpenAI GPT-4 with:
   - User's description
   - Available endpoints
   - Instructions for workflow generation
4. Parse AI response into structured workflow
5. Validate and format the workflow
6. Save workflow to Convex

**Output:**
```json
{
  "workflow": {
    "name": "User Registration Flow",
    "description": "Create user and send welcome email",
    "steps": [
      {
        "id": "step-0",
        "endpointId": "create-user",
        "order": 0,
        "reasoning": "First create the user account",
        "parameters": {...}
      },
      {
        "id": "step-1",
        "endpointId": "send-email",
        "order": 1,
        "reasoning": "Send welcome email to new user",
        "parameters": {...}
      }
    ]
  },
  "explanation": "This workflow first creates...",
  "aiReasoning": [...]
}
```

#### 2. **Flow Suggestion Analysis**
Analyzes API endpoints and suggests practical workflows:

**Input:**
- API spec ID: "api-123"
- User ID: "user-abc"

**Process:**
1. Fetch API spec from Convex (if not provided)
2. Extract and analyze all endpoints
3. Call OpenAI GPT-4 with:
   - Endpoint descriptions
   - Instructions to suggest workflows
4. Generate 5-8 diverse workflow suggestions
5. Categorize by complexity and use case
6. Save suggestions to Convex

**Output:**
```json
{
  "suggestedFlows": [
    {
      "id": "flow-1",
      "name": "Complete User Onboarding",
      "description": "Full user registration and setup",
      "useCase": "When a new user signs up",
      "category": "CRUD",
      "complexity": "moderate",
      "endpoints": ["create-user", "send-email", "create-profile"]
    }
  ],
  "apiSummary": "This API provides user management..."
}
```

#### 3. **Pattern Learning**
Extracts reusable patterns from reference workflows:

**Input:**
- Reference workflow (user-created or edited)
- Endpoints used in workflow
- Spec ID and User ID

**Process:**
1. Analyze workflow structure
2. Call OpenAI GPT-4 with:
   - Workflow steps and logic
   - Endpoint details
   - Instructions to extract patterns
3. Identify structural patterns (sequential, parallel, conditional)
4. Extract parameter mapping strategies
5. Recognize interaction patterns (CRUD, chains, etc.)
6. Save learned pattern to Convex
7. Mark as active pattern for the spec

**Output:**
```json
{
  "patterns": {
    "structure": {
      "type": "sequential",
      "description": "Steps execute one after another"
    },
    "parameters": {
      "mappingStrategy": "Output of step N becomes input of step N+1",
      "commonMappings": ["output.userId -> input.id"]
    },
    "interactions": {
      "pattern": "CRUD",
      "description": "Create then Read pattern"
    }
  },
  "confidence": 0.95
}
```

#### 4. **Auto-Building Workflows**
Constructs complete workflows using learned patterns:

**Input:**
- Suggested flows (from suggestion phase)
- Spec ID and User ID

**Process:**
1. Fetch active flow pattern from Convex
2. Fetch API spec from Convex (if not provided)
3. Extract endpoints from spec
4. Call OpenAI GPT-4 with:
   - Suggested flow ideas
   - Learned patterns
   - Available endpoints
   - Instructions to build complete workflows
5. Apply patterns to generate detailed steps
6. Add parameter mappings and dependencies
7. Return complete executable workflows

**Output:**
```json
{
  "workflows": [
    {
      "flow_id": "flow-1",
      "workflow": {
        "name": "Complete User Onboarding",
        "steps": [...]
      },
      "applied_patterns": ["sequential", "CRUD"]
    }
  ]
}
```

#### 5. **Convex Integration**
Manages all database interactions:

**Read Operations:**
- Fetches API specs when only spec ID provided
- Retrieves active patterns for users
- Gets endpoint lists from specs

**Write Operations:**
- Saves generated workflows
- Stores suggested flows
- Saves learned patterns
- Updates pattern statistics

#### 6. **OpenAI Communication**
Manages all AI interactions:
- Constructs optimal prompts for each use case
- Handles OpenAI API authentication
- Processes AI responses
- Validates and structures AI output
- Handles errors and retries

### What the Backend Does NOT Do
❌ Does NOT manage user sessions (frontend responsibility)
❌ Does NOT store UI state (Convex responsibility)
❌ Does NOT render UI (frontend responsibility)
❌ Does NOT handle user authentication (frontend responsibility)

### Backend Processing Flow

```
Receive Request from Frontend
    ↓
Extract userId, specId, description
    ↓
Query Convex for existing data
    ├─ Get API spec
    ├─ Get endpoints
    └─ Get active patterns
    ↓
Prepare AI prompt with all data
    ↓
Call OpenAI GPT-4
    ↓
Process AI response
    ├─ Parse JSON
    ├─ Validate structure
    └─ Format output
    ↓
Save results to Convex
    ├─ Workflows
    ├─ Suggested flows
    └─ Learned patterns
    ↓
Return results to Frontend
```

---

## 🔄 Complete System Flow

### Example: User Generates a Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION (Frontend)                              │
│    User types: "Create a user and send welcome email"       │
│    UI collects: description, specId from current context    │
│    UI includes: userId from session                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND PREPARES REQUEST                                │
│    - Gets specId from current workspace                     │
│    - Gets userId from authentication                         │
│    - Sends POST to backend:                                  │
│      /api/workflows/generate-from-nl                         │
│      { description, specId, userId, endpoints: [] }          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND RECEIVES REQUEST                                  │
│    Backend sees:                                             │
│    - description: "Create a user and send welcome email"    │
│    - specId: "api-123"                                       │
│    - userId: "user-abc"                                      │
│    - endpoints: [] (empty - needs to fetch)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKEND QUERIES CONVEX                                    │
│    GET apiWorkflows:getAPISpec(specId: "api-123")           │
│    Convex returns:                                           │
│    {                                                         │
│      spec: {                                                 │
│        paths: {                                              │
│          "/users": { post: {...}, get: {...} },             │
│          "/emails/send": { post: {...} }                     │
│        }                                                     │
│      }                                                       │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BACKEND EXTRACTS ENDPOINTS                                │
│    Parses spec and creates endpoint list:                   │
│    [                                                         │
│      { id: "create-user", method: "POST", path: "/users" }, │
│      { id: "send-email", method: "POST", path: "/emails" }  │
│    ]                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. BACKEND CALLS OPENAI                                      │
│    POST https://api.openai.com/v1/chat/completions          │
│    {                                                         │
│      model: "gpt-4o",                                        │
│      messages: [                                             │
│        { role: "system", content: "You are an API expert" },│
│        { role: "user", content: "User wants: ... Available  │
│          endpoints: ..." }                                   │
│      ]                                                       │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. OPENAI RESPONDS                                           │
│    Returns workflow structure:                               │
│    {                                                         │
│      workflowName: "User Registration Flow",                │
│      selectedEndpoints: [                                    │
│        { endpointId: "create-user", order: 0, ... },        │
│        { endpointId: "send-email", order: 1, ... }          │
│      ],                                                      │
│      explanation: "..."                                      │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. BACKEND PROCESSES RESPONSE                                │
│    - Parses AI JSON response                                 │
│    - Validates structure                                     │
│    - Formats into workflow object                            │
│    - Generates unique workflow ID                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. BACKEND SAVES TO CONVEX                                   │
│    POST apiWorkflows:saveWorkflow                            │
│    {                                                         │
│      workflowId: "wf-456",                                   │
│      name: "User Registration Flow",                         │
│      steps: [...],                                           │
│      userId: "user-abc",                                     │
│      specId: "api-123"                                       │
│    }                                                         │
│    Convex stores the workflow                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. BACKEND RETURNS TO FRONTEND                              │
│     {                                                        │
│       success: true,                                         │
│       data: {                                                │
│         workflow: { name, description, steps },              │
│         workflowId: "wf-456",                                │
│         explanation: "...",                                  │
│         aiReasoning: [...]                                   │
│       }                                                      │
│     }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 11. FRONTEND DISPLAYS RESULTS                                │
│     - Shows generated workflow                               │
│     - Displays step-by-step explanation                      │
│     - Provides edit/save options                             │
│     - User can now execute or modify the workflow            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Responsibility Matrix

| Task | Frontend | Convex | Backend |
|------|----------|--------|---------|
| Display UI | ✅ | ❌ | ❌ |
| User authentication | ✅ | ❌ | ❌ |
| Store user data | ❌ | ✅ | ❌ |
| Store API specs | ❌ | ✅ | ❌ |
| Store workflows | ❌ | ✅ | ❌ |
| Fetch stored data | ✅ Frontend / ✅ Backend | ✅ | ✅ Backend |
| Generate workflows with AI | ❌ | ❌ | ✅ |
| Analyze API endpoints | ❌ | ❌ | ✅ |
| Learn patterns | ❌ | ❌ | ✅ |
| Call OpenAI | ❌ | ❌ | ✅ |
| Real-time sync | ✅ | ✅ | ❌ |
| Validate requests | ✅ | ❌ | ✅ |
| Error handling | ✅ | ❌ | ✅ |
| Workflow execution | ✅ | ❌ | Future |

---

## 🎯 Summary

### Frontend (Next.js)
**Role**: User Interface & Orchestration
- Displays conversational UI
- Collects user input
- Sends requests to backend with context (userId, specId)
- Stores/retrieves data via Convex
- Shows results to user

### Convex (Database)
**Role**: Data Persistence & Synchronization
- Stores all system data (specs, workflows, patterns, users)
- Provides query/mutation interface
- Syncs data between frontend and backend
- Ensures data consistency

### Backend (Python/FastAPI)
**Role**: AI Processing & Workflow Intelligence
- Generates workflows using GPT-4
- Analyzes APIs and suggests workflows
- Learns patterns from reference workflows
- Auto-builds complete workflows
- Fetches data from Convex
- Saves results to Convex
- Manages OpenAI communication

**Key Principle**: Each component has a clear, focused responsibility. The frontend handles UI, Convex handles data, and the backend handles AI intelligence.
