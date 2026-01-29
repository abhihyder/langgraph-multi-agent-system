#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Multi-Agent AI System - Startup Script           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Please create a .env file with your API keys."
    echo "See .env.example for reference."
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check which mode to run
echo "Select mode:"
echo "  1) Production API Server (with OAuth, Database, Rate Limiting)"
echo "  2) CLI Mode (Interactive terminal - no auth required)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🚀 Starting Production API Server...${NC}"
        echo ""
        echo "Server will be available at:"
        echo -e "  ${BLUE}http://localhost:8000${NC}"
        echo ""
        echo "Documentation:"
        echo -e "  ${BLUE}http://localhost:8000/docs${NC} (Swagger UI)"
        echo ""
        echo "Features:"
        echo "  ✓ Google OAuth authentication"
        echo "  ✓ Database persistence"
        echo "  ✓ Rate limiting"
        echo "  ✓ User personas"
        echo ""
        echo "Main endpoints:"
        echo "  POST /api/query           - Process queries (requires auth)"
        echo "  GET  /api/conversations   - Conversation history"
        echo "  GET  /health              - Health check"
        echo ""
        echo "Press Ctrl+C to stop the server"
        echo ""
        
        # Start production server
        python server.py
        ;;
    2)
        echo ""
        echo -e "${GREEN}🤖 Starting CLI mode...${NC}"
        echo ""
        echo "This mode provides direct access to the agent system"
        echo "without authentication or database persistence."
        echo ""
        python -m app.main
        ;;
    *)
        echo ""
        echo -e "${YELLOW}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac
