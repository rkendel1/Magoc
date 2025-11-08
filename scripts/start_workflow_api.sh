#!/usr/bin/env bash
# Startup script for Magoc Workflow Extensions FastAPI backend

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Magoc Workflow Extensions Backend${NC}"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY environment variable is not set${NC}"
    echo -e "${BLUE}💡 Set it with: export OPENAI_API_KEY=your-key${NC}"
    exit 1
fi

# Install dependencies if needed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
python3 -c "import fastapi" 2>/dev/null || {
    echo -e "${BLUE}📥 Installing dependencies...${NC}"
    pip3 install -q -r requirements-workflow.txt
}

# Start the server
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
RELOAD=${RELOAD:-""}

echo -e "${GREEN}✅ Dependencies ready${NC}"
echo -e "${BLUE}🌐 Starting server on http://${HOST}:${PORT}${NC}"
echo -e "${BLUE}📚 API Documentation: http://${HOST}:${PORT}/docs${NC}"
echo -e "${BLUE}📖 ReDoc: http://${HOST}:${PORT}/redoc${NC}"
echo ""

if [ "$RELOAD" = "true" ]; then
    echo -e "${BLUE}🔄 Running in development mode with auto-reload${NC}"
    exec uvicorn magoc_workflow_extensions.api:app --host "$HOST" --port "$PORT" --reload
else
    exec uvicorn magoc_workflow_extensions.api:app --host "$HOST" --port "$PORT"
fi
