#!/usr/bin/env python3
import json
import sys
import traceback
import select
import time
import os
from typing import Dict, Any, List, Optional, Union

from tool_provider import ToolProvider
from mock_providers import UtilityToolProvider, AppointmentToolProvider, ProgramToolProvider, StoreLocatorToolProvider

# Toggle debugging
DEBUG_ENABLED = True
def debug(message): 
    if DEBUG_ENABLED:
        print(f"[DEBUG] {message}", file=sys.stderr)
        sys.stderr.flush()

class ToolProviderMCPServer:
    """MCP Server connecting tool providers to MCP Clients via JSON-RPC 2.0"""
    
    def __init__(self):
        """Initialize the MCP server with tool providers"""
        self.providers = {}
        self.tools = {}
        
        # Register all tool providers
        provider_classes = [UtilityToolProvider, AppointmentToolProvider, ProgramToolProvider, StoreLocatorToolProvider]
        
        for provider_class in provider_classes:
            provider = provider_class()
            self.register_provider(provider)
            
        debug(f"Server initialized with {len(self.tools)} tools from {len(self.providers)} providers")
    
    def register_provider(self, provider: ToolProvider) -> None:
        """Register a tool provider and its tools"""
        provider_name = provider.__class__.__name__
        self.providers[provider_name] = provider
        
        # Register all tools with MCP-compliant names: Must match the regex ^[a-zA-Z0-9_-]{1,64}$
        for tool_name, tool_info in provider.get_tools().items():
            qualified_name = f"{provider_name}_{tool_name}"
            self.tools[qualified_name] = {
                **tool_info,
                "provider": provider,
                "original_name": tool_name,
                "provider_name": provider_name
            }
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Generate tool schemas with correct structure"""
        schemas = []
        
        for tool_name, tool_info in self.tools.items():
            # Extract basic tool information
            provider_name = tool_info['provider_name']
            description = tool_info['description']
            param_info = tool_info["param_info"]
            param_type = param_info.get("type", "object")
            
            # Create base schema
            schema = {
                "name": tool_name,
                "description": f"{description} (from {provider_name})",
                "inputSchema": {
                    "type": "object", 
                    "properties": {}, 
                    "required": []
                },
                "annotations": {
                    "usage": f"Use this tool when you need to {description.lower()}",
                    "examples": [
                        {"description": f"Example of using {tool_name}", "arguments": {}}
                    ]
                }
            }
            
            # Handle parameter schema
            if param_type == "string":
                # String parameter type (simple)
                schema["inputSchema"]["properties"]["param"] = {
                    "type": "string", 
                    "description": param_info.get("description", "String parameter")
                }
                
                # Add required if needed
                if param_info.get("required", False):
                    schema["inputSchema"]["required"].append("param")
                    schema["annotations"]["examples"][0]["arguments"]["param"] = "example value"
                    
            elif param_type == "object":
                # Object parameter type (complex)
                properties = {}
                for prop_name, prop_desc in param_info.get("schema", {}).items():
                    properties[prop_name] = {
                        "type": "string", 
                        "description": str(prop_desc)
                    }
                    schema["annotations"]["examples"][0]["arguments"][prop_name] = f"example {prop_name}"
                
                schema["inputSchema"]["properties"] = properties
                
                # Add required fields if specified
                if param_info.get("required", False):
                    schema["inputSchema"]["required"] = param_info.get("required_fields", [])
            
            schemas.append(schema)
        
        return schemas
    
    def execute_tool(self, tool_name: str, params: Any) -> Dict[str, Any]:
        """Execute a tool with simplified error handling and parameter processing"""
        # Check if tool exists
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        # Get tool info
        tool_info = self.tools[tool_name]
        method = tool_info["method"]
        param_info = tool_info["param_info"]
        param_type = param_info.get("type", "object")
        
        debug(f"Executing tool: {tool_name} with params: {params}")
        
        try:
            # Process parameters based on type
            if param_type == "string" and isinstance(params, dict) and "param" in params:
                # String parameter wrapped in object
                param_value = params["param"]
                debug(f"Using string parameter: {param_value}")
                result = method(param_value)
            elif param_info.get("required", False) and params is not None:
                # Object parameter
                debug(f"Using object parameters: {params}")
                result = method(params)
            else:
                # No parameters needed
                debug("Calling method without parameters")
                result = method()
            
            # Log result type and preview
            result_preview = str(result)[:80] + ("..." if len(str(result)) > 80 else "")
            debug(f"Result: {type(result).__name__} = {result_preview}")
            
            # Return result based on type
            if isinstance(result, (dict, list, str, int, float, bool)) or result is None:
                return result
            else:
                # Convert non-JSON-serializable result to string
                return {"result": str(result)}
                    
        except Exception as e:
            # Handle errors
            debug(f"Tool execution error: {str(e)}")
            debug(traceback.format_exc())
            return {"error": f"Error executing tool: {str(e)}"}
    
    def handle_jsonrpc_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a JSON-RPC 2.0 message (request or notification)"""
        # Check if notification (no ID) or request
        if "id" not in message:
            self.handle_notification(message)
            return None
        else:
            return self.handle_request(message)
    
    def handle_notification(self, notification: Dict[str, Any]) -> None:
        """Handle a JSON-RPC 2.0 notification (no response needed)"""
        method = notification.get("method", "")
        debug(f"Processing notification: method={method}")
        
        if method == "notifications/initialized":
            debug("Client is ready - initialization complete")
        elif method == "exit":
            debug("Exit notification received")
            sys.exit(0)
        else:
            debug(f"Unknown notification method: {method}")
        
        # Explicitly flush any pending output to ensure client sees debug messages
        sys.stderr.flush()
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request with cleaner method dispatching"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        debug(f"Processing request: method={method}, id={request_id}")
        
        try:
            # Use dispatch pattern for cleaner method handling
            if method == "initialize":
                return self._handle_initialize(params, request_id)
            elif method in ["tools/list", "getToolDefinitions"]:
                return self._handle_tools_list(request_id)
            elif method in ["tools/call", "executeToolCall"]:
                return self._handle_tool_call(method, params, request_id)
            elif method == "shutdown":
                return self._handle_shutdown(request_id)
            elif method == "exit":
                return self._handle_exit(request_id)
            elif method == "ping":
                # Simple ping for health checks
                return self.create_jsonrpc_result({"status": "ok"}, request_id)
            else:
                return self.create_jsonrpc_error(-32601, "Method not found", f"Method '{method}' not found", request_id)
        except Exception as e:
            debug(f"Error processing request: {e}")
            debug(traceback.format_exc())
            return self.create_jsonrpc_error(-32603, "Internal error", str(e), request_id)
    
    def create_jsonrpc_result(self, result: Any, request_id: Union[str, int, None]) -> Dict[str, Any]:
        """Create a JSON-RPC success response"""
        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    def create_jsonrpc_error(self, code: int, message: str, data: Any = None, request_id: Union[str, int, None] = None) -> Dict[str, Any]:
        """Create a JSON-RPC error response"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        
        return {"jsonrpc": "2.0", "error": error, "id": request_id}
    
    def start_stdio_server(self) -> None:
        """Start a JSON-RPC server with I/O handling"""
        debug("MCP Server started")
        
        try:
            # Configure line buffering
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', 1)
            
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
            
            sys.stderr.flush()
            
            # Main server loop
            while True:
                try:
                    # Check for input with timeout
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if not rlist:
                        continue
                    
                    # Read input line
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    if not line.strip():
                        continue
                    
                    # Process request
                    request = json.loads(line)
                    request_id = request.get("id", "none")
                    method = request.get("method", "unknown")
                    debug(f"Request: {method}, id={request_id}")
                    
                    # Handle the request
                    response = self.handle_jsonrpc_message(request)
                    
                    # Send response for non-notifications
                    if response is not None:
                        # Compact JSON encoding
                        response_json = json.dumps(response, separators=(',', ':'))
                        
                        # Send and flush
                        sys.stdout.write(response_json + "\n")
                        sys.stdout.flush()
                        debug(f"Response sent for id={request_id}")
                
                except json.JSONDecodeError as e:
                    # JSON parse error
                    self._send_error(-32700, "Parse error", str(e))
                
                except Exception as e:
                    # Unexpected error
                    debug(f"Error processing request: {e}")
                    debug(traceback.format_exc())
                    self._send_error(-32603, "Internal error", str(e))
        
        except KeyboardInterrupt:
            debug("Keyboard interrupt received")
            sys.exit(0)
        
        except Exception as e:
            debug(f"Fatal server error: {e}")
            debug(traceback.format_exc())
            sys.exit(1)

    def _send_error(self, code: int, message: str, data: Any = None) -> None:
        """Send an error response to stdout"""
        error_response = self.create_jsonrpc_error(code, message, data, None)
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()
        debug(f"Error response sent: {message}")

    def _handle_initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle initialization request"""
        protocol_version = params.get("protocolVersion", "unknown")
        
        result = self.create_jsonrpc_result({
            "capabilities": {
                "supportsToolDefinitions": True,
                "supportsToolCalls": True,
                "supportedToolDefinitionProtocols": ["2024-11-05"],
                "tools": {"listChanged": True}
            },
            "serverInfo": {
                "name": "ToolProvider MCP Server",
                "version": "0.1.0"
            },
            "protocolVersion": protocol_version
        }, request_id)
        
        debug(f"Initialize response sent (protocol: {protocol_version})")
        return result

    def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools list request"""
        debug("Generating tool schemas")
        schemas = self.get_tool_schemas()
        
        result = self.create_jsonrpc_result({"tools": schemas}, request_id)
        debug(f"tools/list response created ({len(schemas)} tools)")
        return result

    def _handle_tool_call(self, method: str, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tool call request"""
        # Extract tool name and arguments based on protocol
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
        else:  # executeToolCall
            tool_call = params.get("toolCall", {})
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
        
        debug(f"Tool call: {tool_name}")
        
        # Validate tool name
        if not tool_name:
            return self.create_jsonrpc_error(-32602, "Invalid params", "Tool name is required", request_id)
        
        # Execute the tool
        result = self.execute_tool(tool_name, arguments)
        
        # Process result
        if isinstance(result, dict) and "error" in result:
            # Handle error result
            error_message = result["error"]
            debug(f"Tool returned error: {error_message}")
            return self.create_jsonrpc_result({
                "content": [{"type": "text", "text": error_message}],
                "isError": True
            }, request_id)
        
        # Format successful result
        content = []
        if isinstance(result, (dict, list)):
            # JSON result
            json_str = json.dumps(result, indent=2)
            content.append({"type": "text", "text": json_str})
        else:
            # String or other simple result
            content.append({"type": "text", "text": str(result)})
        
        return self.create_jsonrpc_result({
            "content": content, 
            "isError": False
        }, request_id)

    def _handle_shutdown(self, request_id: Any) -> Dict[str, Any]:
        """Handle shutdown request"""
        debug("Shutdown request received")
        return self.create_jsonrpc_result(None, request_id)

    def _handle_exit(self, request_id: Any) -> Dict[str, Any]:
        """Handle exit request"""
        debug("Exit request received")
        # For exit, immediately send response before exiting
        response = self.create_jsonrpc_result(None, request_id)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
        
        # Give a moment for the response to be sent
        time.sleep(0.1)
        sys.exit(0)

if __name__ == "__main__":    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            DEBUG_ENABLED = True
        elif sys.argv[1] == "--no-debug":
            DEBUG_ENABLED = False
    
    # Start the server
    server = ToolProviderMCPServer()
    server.start_stdio_server()