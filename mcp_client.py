"""
MCP Client utility for JSON-RPC communication with MCP server
Extracts common JSON-RPC patterns from agent.py
"""
import json
import subprocess
import sys
import logging
from typing import Dict, Any, Optional


class MCPClient:
    """Handles JSON-RPC communication with MCP server subprocess"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.logger = logging.getLogger('mcp_client')
        self._request_id = 0
    
    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC"""
        self._request_id += 1
        return self._request_id
    
    def _create_jsonrpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standard JSON-RPC 2.0 request"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method
        }
        if params:
            request["params"] = params
        return request
    
    def _create_jsonrpc_notification(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 notification (no response expected)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params:
            notification["params"] = params
        return notification
    
    def _send_request(self, request: Dict[str, Any]) -> None:
        """Send JSON-RPC request to MCP server"""
        if not self.process:
            raise RuntimeError("MCP server not started")
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
    
    def _read_response(self) -> Dict[str, Any]:
        """Read JSON-RPC response from MCP server"""
        if not self.process:
            raise RuntimeError("MCP server not started")
        
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        return json.loads(response_line)
    
    async def start_server(self) -> bool:
        """Start MCP server subprocess"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, "mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info("MCP server started")
            return await self.initialize_connection()
        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def initialize_connection(self) -> bool:
        """Initialize MCP protocol connection"""
        try:
            # Step 1: Send initialize request
            init_request = self._create_jsonrpc_request(
                method="initialize",
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "what-to-do-agent",
                        "version": "1.0.0"
                    }
                }
            )
            
            self._send_request(init_request)
            response = self._read_response()
            
            if "result" in response:
                # Step 2: Send initialized notification
                initialized_notification = self._create_jsonrpc_notification(
                    method="notifications/initialized"
                )
                self._send_request(initialized_notification)
                
                self.logger.info("MCP connection initialized successfully")
                return True
            else:
                self.logger.error(f"MCP initialization failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP connection: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via JSON-RPC"""
        if not self.process:
            return {"error": "MCP server not started"}
        
        try:
            # Create MCP tool call request
            tool_request = self._create_jsonrpc_request(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            self._send_request(tool_request)
            response_data = self._read_response()
            
            # Extract the tool result
            if "result" in response_data:
                content = response_data["result"]["content"][0]["text"]
                return json.loads(content)
            else:
                return {"error": "Invalid MCP response", "response": response_data}
                
        except Exception as e:
            return {"error": f"MCP tool call failed: {str(e)}"}
    
    def shutdown(self):
        """Clean up MCP server process"""
        if self.process:
            self.process.terminate()
            self.process = None
            self.logger.info("MCP server terminated")
    
    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.shutdown()