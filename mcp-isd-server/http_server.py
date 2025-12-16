"""
HTTP Server wrapper for MCP ISD Server
Exposes MCP server functionality over HTTP for Azure Container Apps deployment

This allows the MCP server to be deployed as a remote endpoint and connected
to Azure AI Foundry agents.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import asyncio
import json
from typing import Any, Dict, List
from server import ISDClient

app = FastAPI(
    title="ISD MCP Server",
    description="Microsoft Industry Solutions Directory MCP Server - HTTP Endpoint",
    version="1.0.0"
)

# Global ISD client
isd_client: ISDClient = None


@app.on_event("startup")
async def startup_event():
    """Initialize the ISD client on startup"""
    global isd_client
    isd_client = ISDClient()
    print("✅ ISD MCP Server started - HTTP mode")


@app.on_event("shutdown")
async def shutdown_event():
    """Close the ISD client on shutdown"""
    global isd_client
    if isd_client:
        await isd_client.close()
    print("👋 ISD MCP Server stopped")


@app.get("/health")
async def health_check():
    """Health check endpoint for Azure Container Apps"""
    return {
        "status": "healthy",
        "service": "isd-mcp-server",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "ISD MCP Server",
        "description": "Microsoft Industry Solutions Directory MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "list_industries": "/tools/list_industries",
            "list_technologies": "/tools/list_technologies",
            "get_solutions_by_industry": "/tools/get_solutions_by_industry",
            "get_solutions_by_technology": "/tools/get_solutions_by_technology",
            "search_solutions": "/tools/search_solutions"
        },
        "mcp_protocol": {
            "version": "1.0",
            "transport": "HTTP/SSE",
            "endpoint": "/mcp"
        }
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "list_industries",
                "description": "Get all available industry categories and use cases from ISD",
                "parameters": {}
            },
            {
                "name": "list_technologies",
                "description": "Get all available technology categories from ISD",
                "parameters": {}
            },
            {
                "name": "get_solutions_by_industry",
                "description": "Get all partner solutions for a specific industry use case",
                "parameters": {
                    "industry": {
                        "type": "string",
                        "description": "Industry use case name (e.g., 'Managing Risk and Compliance', 'Student Success')",
                        "required": True
                    }
                }
            },
            {
                "name": "get_solutions_by_technology",
                "description": "Get all partner solutions for a specific technology category across all industries",
                "parameters": {
                    "technology": {
                        "type": "string",
                        "description": "Technology name (e.g., 'AI Business Solutions', 'Cloud and AI Platforms', 'Security')",
                        "required": True
                    }
                }
            },
            {
                "name": "search_solutions",
                "description": "Search solutions by keyword with optional filters",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Keyword search",
                        "required": False
                    },
                    "industry": {
                        "type": "string",
                        "description": "Filter by industry",
                        "required": False
                    },
                    "technology": {
                        "type": "string",
                        "description": "Filter by technology",
                        "required": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "required": False
                    }
                }
            }
        ]
    }


@app.post("/tools/list_industries")
async def list_industries_endpoint():
    """List all available industries"""
    try:
        industries = await isd_client.get_all_industries()
        # Return just the names for simpler output
        industry_names = [ind["name"] for ind in industries]
        return {"result": industry_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/list_technologies")
async def list_technologies_endpoint():
    """List all available technologies"""
    try:
        technologies = await isd_client.get_all_technologies()
        # Return just the names for simpler output
        tech_names = [tech["name"] for tech in technologies]
        return {"result": tech_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_solutions_by_industry")
async def get_solutions_by_industry_endpoint(request: Request):
    """Get solutions by industry"""
    try:
        body = await request.json()
        industry = body.get("industry")
        if not industry:
            raise HTTPException(status_code=400, detail="industry parameter is required")
        
        solutions = await isd_client.get_solutions_by_industry(industry)
        return {"result": solutions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_solutions_by_technology")
async def get_solutions_by_technology_endpoint(request: Request):
    """Get solutions by technology"""
    try:
        body = await request.json()
        technology = body.get("technology")
        if not technology:
            raise HTTPException(status_code=400, detail="technology parameter is required")
        
        solutions = await isd_client.get_solutions_by_technology(technology)
        return {"result": solutions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/search_solutions")
async def search_solutions_endpoint(request: Request):
    """Search solutions with filters"""
    try:
        body = await request.json()
        query = body.get("query")
        industry = body.get("industry")
        technology = body.get("technology")
        limit = body.get("limit", 10)
        
        solutions = await isd_client.search_all_solutions(
            query=query,
            industry_filter=industry,
            technology_filter=technology,
            limit=limit
        )
        return {"result": solutions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MCP Protocol Endpoints (for MCP-compliant clients)
# Note: Standard MCP uses SSE transport for remote servers
# The /mcp POST endpoint below is a custom HTTP adapter for compatibility

# Azure AI Foundry requires a specific /runtime/webhooks/mcp/sse endpoint
# This is an Azure Functions-specific convention that we need to support
@app.get("/runtime/webhooks/mcp/sse")
async def foundry_mcp_sse_endpoint():
    """
    Azure AI Foundry expects MCP servers at this specific path
    This is for Azure Functions compatibility
    Returns tool metadata for Foundry to enumerate available tools
    """
    tools = await list_tools()
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "ISD MCP Server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {}
        },
        "tools": tools["tools"]
    }


@app.post("/runtime/webhooks/mcp/sse")
async def foundry_mcp_sse_post_endpoint(request: Request):
    """
    Azure AI Foundry MCP tool execution endpoint
    Handles tool calls from Foundry agents
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        
        if method == "tools/list":
            tools = await list_tools()
            return {"result": tools["tools"]}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "list_industries":
                industries = await isd_client.get_all_industries()
                result = [ind["name"] for ind in industries]
            elif tool_name == "list_technologies":
                technologies = await isd_client.get_all_technologies()
                result = [tech["name"] for tech in technologies]
            elif tool_name == "get_solutions_by_industry":
                result = await isd_client.get_solutions_by_industry(tool_args.get("industry"))
            elif tool_name == "get_solutions_by_technology":
                result = await isd_client.get_solutions_by_technology(tool_args.get("technology"))
            elif tool_name == "search_solutions":
                result = await isd_client.search_all_solutions(
                    query=tool_args.get("query"),
                    industry_filter=tool_args.get("industry"),
                    technology_filter=tool_args.get("technology"),
                    limit=tool_args.get("limit", 10)
                )
            else:
                raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown MCP method: {method}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP protocol endpoint for Azure AI Foundry integration
    Implements the MCP SSE (Server-Sent Events) transport
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        
        # Route to appropriate tool based on method
        if method == "tools/list":
            tools = await list_tools()
            return {"result": tools["tools"]}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "list_industries":
                industries = await isd_client.get_all_industries()
                result = [ind["name"] for ind in industries]
            elif tool_name == "list_technologies":
                technologies = await isd_client.get_all_technologies()
                result = [tech["name"] for tech in technologies]
            elif tool_name == "get_solutions_by_industry":
                result = await isd_client.get_solutions_by_industry(tool_args.get("industry"))
            elif tool_name == "get_solutions_by_technology":
                result = await isd_client.get_solutions_by_technology(tool_args.get("technology"))
            elif tool_name == "search_solutions":
                result = await isd_client.search_all_solutions(
                    query=tool_args.get("query"),
                    industry_filter=tool_args.get("industry"),
                    technology_filter=tool_args.get("technology"),
                    limit=tool_args.get("limit", 10)
                )
            else:
                raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown MCP method: {method}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    """
    MCP Server-Sent Events endpoint for real-time communication
    Used by MCP clients that support SSE transport
    """
    return JSONResponse({
        "message": "SSE endpoint - connect with EventSource client",
        "protocol": "MCP/1.0",
        "transport": "SSE"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
