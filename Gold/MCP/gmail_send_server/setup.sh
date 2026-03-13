#!/bin/bash
# Setup script for Gmail Send MCP Server

echo "=================================="
echo "Gmail Send MCP Server - Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓${NC} Node.js found: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is installed
echo "Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}✓${NC} npm found: $NPM_VERSION"
else
    echo -e "${RED}✗${NC} npm not found."
    exit 1
fi

echo ""
echo "Installing dependencies..."
cd /mnt/d/AI_Employee_Hackathon_0/Silver/MCP/gmail_send_server

if npm install; then
    echo -e "${GREEN}✓${NC} Dependencies installed successfully"
else
    echo -e "${RED}✗${NC} Failed to install dependencies"
    exit 1
fi

echo ""
echo "Checking Gmail credentials..."

CREDENTIALS_FILE="/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json"
TOKEN_FILE="/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_token.json"

if [ -f "$CREDENTIALS_FILE" ]; then
    echo -e "${GREEN}✓${NC} Credentials file found"
else
    echo -e "${YELLOW}⚠${NC}  Credentials file not found: $CREDENTIALS_FILE"
    echo "   Please set up Gmail API credentials first."
fi

if [ -f "$TOKEN_FILE" ]; then
    echo -e "${GREEN}✓${NC} Token file found"
else
    echo -e "${YELLOW}⚠${NC}  Token file not found: $TOKEN_FILE"
    echo "   Run a Gmail watcher first to generate the token."
fi

echo ""
echo "Running tests..."
node test-server.js

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "MCP server is ready to use!"
echo ""
echo "To use with Claude Code:"
echo "  1. Restart Claude Code"
echo "  2. Ask: 'Send an email to ...'"
echo ""
echo "To test standalone:"
echo "  node index.js"
echo ""
