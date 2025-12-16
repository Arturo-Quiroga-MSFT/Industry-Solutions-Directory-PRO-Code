#!/bin/bash

##############################################################################
# Test ISD MCP Server endpoints
# Run this after deployment to verify functionality
##############################################################################

# Read MCP server URL from deployment info or use default
if [ -f "deployment/mcp-deployment-info.json" ]; then
    MCP_SERVER_URL=$(cat deployment/mcp-deployment-info.json | grep -o '"mcp_server_url": "[^"]*' | cut -d'"' -f4)
else
    echo "❌ Deployment info file not found"
    echo "Please provide the MCP server URL:"
    read MCP_SERVER_URL
fi

if [ -z "$MCP_SERVER_URL" ]; then
    echo "❌ No MCP server URL provided"
    exit 1
fi

echo "=========================================="
echo "Testing ISD MCP Server"
echo "=========================================="
echo ""
echo "Server URL: $MCP_SERVER_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
curl -s "$MCP_SERVER_URL/health" | jq .
echo ""
echo ""

# Test 2: Server info
echo "Test 2: Server Info"
echo "--------------------"
curl -s "$MCP_SERVER_URL/" | jq .
echo ""
echo ""

# Test 3: List tools
echo "Test 3: List Tools"
echo "--------------------"
curl -s "$MCP_SERVER_URL/tools" | jq .
echo ""
echo ""

# Test 4: List industries
echo "Test 4: List Industries"
echo "--------------------"
curl -s -X POST "$MCP_SERVER_URL/tools/list_industries" | jq '.result | length'
echo "Industries found"
echo ""
echo ""

# Test 5: List technologies
echo "Test 5: List Technologies"
echo "--------------------"
curl -s -X POST "$MCP_SERVER_URL/tools/list_technologies" | jq '.result | length'
echo "Technologies found"
echo ""
echo ""

# Test 6: Get solutions by industry
echo "Test 6: Get Solutions by Industry (Managing Risk and Compliance)"
echo "--------------------"
curl -s -X POST "$MCP_SERVER_URL/tools/get_solutions_by_industry" \
  -H 'Content-Type: application/json' \
  -d '{"industry": "Managing Risk and Compliance"}' | jq '.result | length'
echo "Solutions found"
echo ""
echo ""

# Test 7: Search solutions
echo "Test 7: Search Solutions (AI)"
echo "--------------------"
curl -s -X POST "$MCP_SERVER_URL/tools/search_solutions" \
  -H 'Content-Type: application/json' \
  -d '{"query": "AI", "limit": 5}' | jq '.result | length'
echo "Solutions found"
echo ""
echo ""

# Test 8: MCP Protocol endpoint
echo "Test 8: MCP Protocol - List Tools"
echo "--------------------"
curl -s -X POST "$MCP_SERVER_URL/mcp" \
  -H 'Content-Type: application/json' \
  -d '{"method": "tools/list", "params": {}}' | jq '.result | length'
echo "Tools available via MCP protocol"
echo ""
echo ""

echo "=========================================="
echo "Testing Complete"
echo "=========================================="
echo ""
echo "✅ All tests completed"
echo ""
echo "Next steps:"
echo "  1. Connect to Azure AI Foundry at https://ai.azure.com"
echo "  2. Add MCP server as custom tool"
echo "  3. Test with AI agent"
echo ""
