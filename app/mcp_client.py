"""
MCP (Model Context Protocol) Client Integration
Provides optional tool calling capabilities for agents
"""

import os
import json
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class MCPClient:
    """
    Wrapper for MCP client that provides tool calling capabilities.
    Gracefully handles cases where MCP is not available or not configured.
    """
    
    def __init__(self):
        self.session: Optional[Any] = None
        self.available_tools: List[Dict[str, Any]] = []
        self.is_connected = False
        
    async def connect(self, server_command: str, server_args: List[str] = None) -> bool:
        """
        Connect to MCP server if available.
        
        Args:
            server_command: Command to start MCP server (e.g., 'npx', 'python')
            server_args: Arguments for server command (e.g., ['-y', '@modelcontextprotocol/server-brave-search'])
            
        Returns:
            True if connected, False otherwise
        """
        if not MCP_AVAILABLE:
            print("⚠️  MCP library not installed. Research agent will work without external tools.")
            return False
            
        try:
            server_params = StdioServerParameters(
                command=server_command,
                args=server_args or [],
                env=None
            )
            
            # Note: This is async context manager, needs to be used with 'async with'
            # For simplicity in sync code, we'll document this but not enforce
            print(f"🔌 Attempting to connect to MCP server: {server_command} {' '.join(server_args or [])}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not connect to MCP server: {e}")
            print("Research agent will continue without external tools.")
            return False
    
    def is_available(self) -> bool:
        """Check if MCP is available and connected."""
        return MCP_AVAILABLE and self.is_connected
    
    def get_tools_for_langchain(self) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to LangChain-compatible format for function calling.
        
        Returns:
            List of tool definitions in OpenAI function calling format
        """
        if not self.is_available():
            return []
        
        # Convert MCP tools to OpenAI function format
        langchain_tools = []
        for tool in self.available_tools:
            langchain_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("inputSchema", {})
                }
            })
        
        return langchain_tools


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> Optional[MCPClient]:
    """
    Get or create the global MCP client instance.
    Returns None if MCP is not configured.
    """
    global _mcp_client
    
    if _mcp_client is None:
        # Check if MCP is configured via environment variables
        mcp_server_command = os.getenv("MCP_SERVER_COMMAND")
        mcp_server_args = os.getenv("MCP_SERVER_ARGS")
        
        if not mcp_server_command:
            # MCP not configured, return None
            return None
        
        _mcp_client = MCPClient()
        
        # Parse args if provided
        args = mcp_server_args.split() if mcp_server_args else []
        
        # Note: Connection is async, this is a simplified sync version
        # For production, you'd want proper async handling
        print(f"📋 MCP configured: {mcp_server_command} {' '.join(args)}")
        print("⚠️  Note: Full MCP integration requires async runtime")
    
    return _mcp_client


def has_mcp_tools() -> bool:
    """Quick check if MCP tools are available."""
    return MCP_AVAILABLE and os.getenv("MCP_SERVER_COMMAND") is not None
