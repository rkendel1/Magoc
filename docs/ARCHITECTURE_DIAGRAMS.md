# System Architecture Diagrams

This document provides visual representations of the system architecture and data flows.

---

## 🏗️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        USER                                   │
│                          ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         FRONTEND (Next.js / Boltq)                  │    │
│  │  - Conversational UI                                 │    │
│  │  - User authentication                               │    │
│  │  - Request orchestration                             │    │
│  │  - Result visualization                              │    │
│  └──────────────┬────────────────────┬─────────────────┘    │
│                 ↓                    ↓                        │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │   CONVEX DATABASE    │  │  PYTHON BACKEND      │         │
│  │  - User data         │←─│  - AI processing     │         │
│  │  - API specs         │──→  - Workflow gen      │         │
│  │  - Workflows         │  │  - Pattern learning  │         │
│  │  - Patterns          │  │  - OpenAI comms      │         │
│  │  - Suggested flows   │  └──────────┬───────────┘         │
│  └──────────────────────┘             ↓                      │
│                              ┌──────────────────┐            │
│                              │  OPENAI API      │            │
│                              │  - GPT-4         │            │
│                              └──────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Request Flow

### Generate Workflow from Natural Language

```
USER
 │
 │ "Create a user and send welcome email"
 ↓
┌─────────────────────────────────────────┐
│ FRONTEND                                │
│ 1. Collect input                         │
│ 2. Get userId from session              │
│ 3. Get specId from workspace            │
│ 4. POST /api/workflows/generate-from-nl │
│    {                                     │
│      description,                        │
│      specId: "api-123",                  │
│      userId: "user-abc",                 │
│      endpoints: []                       │
│    }                                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ BACKEND                                  │
│ 1. Receive request                       │
│ 2. See endpoints: [] (empty)             │
│ 3. Query Convex:                         │
│    getAPISpec("api-123") ────────────┐   │
└──────────────┬──────────────────────┐│───┘
               │                      ││
               │                      │↓
               │         ┌────────────────────────┐
               │         │ CONVEX                 │
               │         │ Return spec with paths │
               │         │ {                      │
               │         │   paths: {             │
               │         │     "/users": {...},   │
               │         │     "/emails": {...}   │
               │         │   }                    │
               │         │ }                      │
               │         └────────────┬───────────┘
               │                      │
               ↓                      │
┌─────────────────────────────────────┴───┐
│ BACKEND                                  │
│ 4. Extract endpoints from spec           │
│ 5. Build AI prompt:                      │
│    - User description                    │
│    - Available endpoints                 │
│ 6. Call OpenAI ──────────────────────┐   │
└──────────────┬───────────────────────┘───┘
               │                       │
               │                       ↓
               │          ┌────────────────────────┐
               │          │ OPENAI GPT-4           │
               │          │ Analyze and generate:  │
               │          │ {                      │
               │          │   workflowName,        │
               │          │   selectedEndpoints,   │
               │          │   explanation          │
               │          │ }                      │
               │          └────────────┬───────────┘
               │                       │
               ↓                       │
┌─────────────────────────────────────┴───┐
│ BACKEND                                  │
│ 7. Parse AI response                     │
│ 8. Format workflow object                │
│ 9. Generate workflow ID                  │
│ 10. Save to Convex:                      │
│     saveWorkflow(...) ───────────────┐   │
└──────────────┬──────────────────────┘───┘
               │                      │
               │                      ↓
               │         ┌────────────────────────┐
               │         │ CONVEX                 │
               │         │ Store workflow         │
               │         │ Associated with user   │
               │         └────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ BACKEND                                  │
│ 11. Return response:                     │
│     {                                    │
│       success: true,                     │
│       data: {                            │
│         workflow: {...},                 │
│         workflowId: "wf-456",            │
│         explanation: "..."               │
│       }                                  │
│     }                                    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ FRONTEND                                 │
│ 12. Display workflow to user             │
│ 13. Show step-by-step visualization      │
│ 14. Offer edit/save/execute options      │
└──────────────┬──────────────────────────┘
               ↓
              USER
              sees generated workflow
```

---

## 📊 Data Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONVEX DATABASE                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │    users         │  │  workspaces      │            │
│  │  - name          │  │  - message       │            │
│  │  - email         │  │  - fileData      │            │
│  │  - pic           │  │  - user (ref)    │            │
│  │  - uid           │  └──────────────────┘            │
│  └────────┬─────────┘                                   │
│           │ (owner)                                     │
│           ↓                                             │
│  ┌──────────────────┐                                   │
│  │   apiSpecs       │←────────┐                        │
│  │  - specId        │         │ (linked)               │
│  │  - name          │         │                        │
│  │  - version       │         │                        │
│  │  - spec (object) │         │                        │
│  │  - user (ref)    │         │                        │
│  └────────┬─────────┘         │                        │
│           │ (links to)         │                        │
│           ↓                    │                        │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ suggestedFlows   │  │  apiWorkflows    │            │
│  │  - flowId        │  │  - workflowId    │            │
│  │  - name          │  │  - name          │            │
│  │  - description   │  │  - description   │            │
│  │  - useCase       │  │  - steps (array) │            │
│  │  - category      │  │  - user (ref)    │            │
│  │  - complexity    │  │  - specId        │            │
│  │  - endpoints     │  │  - isTemplate    │            │
│  │  - specId        │  └──────────────────┘            │
│  │  - user (ref)    │                                   │
│  │  - isConfigured  │                                   │
│  └──────────────────┘                                   │
│           ↓                                             │
│  ┌──────────────────┐                                   │
│  │  flowPatterns    │                                   │
│  │  - patternId     │                                   │
│  │  - name          │                                   │
│  │  - patterns (obj)│                                   │
│  │  - specId        │                                   │
│  │  - user (ref)    │                                   │
│  │  - referenceWfId │                                   │
│  │  - isActive      │                                   │
│  │  - genFlowsCount │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘

   ↑ read/write ↓              ↑ read/write ↓
   
┌─────────────┐              ┌─────────────┐
│  FRONTEND   │              │   BACKEND   │
│  (Next.js)  │              │  (FastAPI)  │
└─────────────┘              └─────────────┘
```

---

## 🔀 Workflow Lifecycle

```
START: User opens app
         ↓
┌────────────────────────────────────────┐
│ PHASE 1: EXPLORE                       │
│ Frontend:                               │
│ - User views API spec                   │
│ - Frontend fetches from Convex          │
│ - Displays endpoints                    │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ PHASE 2: SUGGEST                        │
│ Frontend → Backend:                     │
│ - Send specId + userId                  │
│                                         │
│ Backend:                                │
│ - Query Convex for spec                 │
│ - Analyze endpoints with AI             │
│ - Generate 5-8 suggestions              │
│ - Save to Convex                        │
│                                         │
│ Backend → Frontend:                     │
│ - Return suggested flows                │
│                                         │
│ Frontend:                               │
│ - Display suggestions to user           │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ PHASE 3: GENERATE (Option A)           │
│ User picks suggestion                   │
│                                         │
│ Frontend → Backend:                     │
│ - Send suggestion + specId + userId     │
│                                         │
│ Backend:                                │
│ - Query Convex for spec & pattern       │
│ - Generate detailed workflow            │
│ - Save workflow to Convex               │
│                                         │
│ Backend → Frontend:                     │
│ - Return complete workflow              │
└────────────┬───────────────────────────┘
             │
             └───OR───┐
                      ↓
┌────────────────────────────────────────┐
│ PHASE 3: GENERATE (Option B)           │
│ User types custom description           │
│                                         │
│ Frontend → Backend:                     │
│ - Send description + specId + userId    │
│                                         │
│ Backend:                                │
│ - Query Convex for spec                 │
│ - Generate workflow with AI             │
│ - Save workflow to Convex               │
│                                         │
│ Backend → Frontend:                     │
│ - Return generated workflow             │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ PHASE 4: REFINE                         │
│ Frontend:                               │
│ - User views workflow                   │
│ - User edits steps (optional)           │
│ - User saves changes                    │
│                                         │
│ Frontend → Convex:                      │
│ - Update workflow                       │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ PHASE 5: LEARN (Optional)               │
│ User marks workflow as reference         │
│                                         │
│ Frontend → Backend:                     │
│ - Send workflow + endpoints + ids       │
│                                         │
│ Backend:                                │
│ - Analyze workflow with AI              │
│ - Extract patterns                      │
│ - Save pattern to Convex                │
│ - Mark as active                        │
│                                         │
│ Backend → Frontend:                     │
│ - Confirm pattern learned               │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ PHASE 6: AUTO-BUILD (Next time)        │
│ When user wants new workflow:           │
│                                         │
│ Backend:                                │
│ - Query Convex for active pattern       │
│ - Apply pattern automatically           │
│ - Generate matching user preference     │
│                                         │
│ Result:                                 │
│ - Faster generation                     │
│ - Consistent with user's style          │
└────────────┬───────────────────────────┘
             ↓
           END: User has workflow ready
```

---

## 🎨 Component Interaction Matrix

```
┌─────────────┬──────────┬──────────┬──────────┐
│             │ Frontend │  Convex  │  Backend │
├─────────────┼──────────┼──────────┼──────────┤
│ Frontend    │    —     │  R/W     │    →     │
├─────────────┼──────────┼──────────┼──────────┤
│ Convex      │   R/W    │    —     │   R/W    │
├─────────────┼──────────┼──────────┼──────────┤
│ Backend     │    ←     │  R/W     │    —     │
└─────────────┴──────────┴──────────┴──────────┘

Legend:
  →   Frontend sends requests to Backend
  ←   Backend sends responses to Frontend
  R/W  Read and Write operations
  —    Same component
```

---

## 🔐 Authentication & Authorization Flow

```
┌──────────────────────────────────────────┐
│ USER                                      │
│  └─ Signs in via Frontend                │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ FRONTEND                                  │
│  1. Handles authentication (e.g., OAuth) │
│  2. Gets user credentials                │
│  3. Queries Convex:                      │
│     GetUser(email) ───────────────┐      │
└──────────────┬───────────────────┐│──────┘
               │                   │↓
               │       ┌───────────────────────┐
               │       │ CONVEX                │
               │       │ Returns:              │
               │       │ {                     │
               │       │   _id: "user-abc",    │
               │       │   name,               │
               │       │   email,              │
               │       │   uid                 │
               │       │ }                     │
               │       └───────────┬───────────┘
               ↓                   │
┌──────────────────────────────────┴───────┐
│ FRONTEND                                  │
│  4. Store userId in session               │
│  5. Include userId in all backend calls   │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ BACKEND                                   │
│  6. Receives userId with every request    │
│  7. Uses userId to:                       │
│     - Fetch user-specific data            │
│     - Save results for specific user      │
│  8. All Convex operations scoped to user  │
└───────────────────────────────────────────┘

Security Note:
- Backend trusts userId from Frontend
- In production, add JWT validation
- Backend verifies userId exists in Convex
```

---

## 📈 Scaling Considerations

```
Current Architecture (Single Backend):
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │ ──→ │ Backend  │ ──→ │  OpenAI  │
│          │ ←── │ (Single) │ ←── │   API    │
└────┬─────┘     └────┬─────┘     └──────────┘
     │                │
     └────→ ┌─────────┴─────┐
            │    Convex     │
            └───────────────┘

Future Architecture (Multiple Backends):
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │ ──→ │ Backend 1│ ──→ │  OpenAI  │
│          │     ├──────────┤     │   API    │
│          │ ──→ │ Backend 2│ ──→ │          │
│          │     ├──────────┤     │          │
│          │ ──→ │ Backend 3│ ──→ │          │
└────┬─────┘     └────┬─────┘     └──────────┘
     │                │
     └────→ ┌─────────┴─────┐
            │    Convex     │
            │  (Scales auto)│
            └───────────────┘

Benefits:
- Convex handles scaling automatically
- Multiple backend instances for load balancing
- Stateless backend = easy horizontal scaling
```

---

## 🎯 Key Takeaways

1. **Frontend** = UI & Orchestration
2. **Convex** = Data & Persistence
3. **Backend** = AI & Intelligence

Each component has a clear responsibility and they communicate through well-defined interfaces.
