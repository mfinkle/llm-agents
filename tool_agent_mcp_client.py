#!/usr/bin/env python3
import json
import sys
import subprocess
import time
from typing import Dict, Any, List, Optional
import tempfile
import os
import argparse

from tool_agent import ToolAgent

# Toggle debugging
DEBUG_ENABLED = True
def debug(message): 
    if DEBUG_ENABLED:
        print(f"[DEBUG] {message}", file=sys.stderr)
        sys.stderr.flush()

def load_mcp_config(config_file=None):
    """Load MCP server configuration with cleaner file handling"""
    # Default config locations
    default_locations = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_config.json"),
        os.path.expanduser("~/.config/mcp_config.json"),
        os.path.expanduser("~/Library/Application Support/MCP/mcp_config.json")
    ]
    
    # Add user-specified file if provided
    search_paths = [config_file] if config_file else []
    search_paths.extend(default_locations)
    
    # Try each path
    for path in search_paths:
        if not path:
            continue
            
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    config = json.load(f)
                    debug(f"Loaded config from {path}")
                    return config
        except Exception as e:
            debug(f"Error loading config from {path}: {e}")
    
    # No config found
    debug("No config file found, using empty config")
    return {"mcpServers": {}}

class MCPToolProvider:
    """Provider that connects to an MCP server and makes tools available to ToolAgent"""
    
    def __init__(self, server_command, server_args=None):
        """Initialize with the command to start the MCP server"""
        self.server_command = server_command
        self.server_args = server_args or []
        self.server_process = None
        self.tools = {}
        self.server_name = "MCP_Server"
        self.server_version = "Unknown"
        self.tool_definitions = []
        self.request_id = 0
        
        # Create log file for server output
        self.log_file = tempfile.NamedTemporaryFile(prefix="mcp_server_", suffix=".log", delete=False, mode="w").name
        debug(f"MCP server log file: {self.log_file}")
    
    def start_server(self):
        """Start the MCP server subprocess with enhanced error handling"""
        command = [self.server_command] + self.server_args
        debug(f"Starting MCP server: {' '.join(command)}")
        
        # Open the log file for server output
        log_fd = open(self.log_file, "w")
        
        try:
            # On Unix systems, use a process group for better cleanup
            preexec_fn = os.setsid if hasattr(os, 'setsid') else None
            
            # Start the server process
            debug("Launching process")
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log_fd,
                text=True,
                bufsize=1,  # Line buffered
                preexec_fn=preexec_fn
            )
            
            debug(f"Process started with PID: {self.server_process.pid}")
            
            # Check if process started successfully
            if self.server_process.poll() is not None:
                debug(f"Process failed to start, exit code: {self.server_process.poll()}")
                return False
            
            # Initialize server with timeout
            debug("Initializing server")
            if not self.initialize_server():
                debug("Server initialization failed")
                self._check_log_file()
                self.stop_server()
                return False
            
            # Fetch tool definitions with timeout
            debug("Fetching tool definitions")
            if not self.fetch_tool_definitions():
                debug("Failed to fetch tool definitions")
                self._check_log_file()
                self.stop_server()
                return False
            
            debug(f"Server started successfully with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            debug(f"Error starting server: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            if self.server_process:
                self.stop_server()
            return False
    
    def get_next_request_id(self):
        """Get a unique request ID for JSON-RPC requests"""
        self.request_id += 1
        return self.request_id
    
    def initialize_server(self):
        """Initialize server with cleaner protocol handling"""
        debug("Initializing MCP server")
        
        # Create initialization request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "ToolAgent MCP Client",
                    "version": "1.0.0"
                }
            },
            "id": self.get_next_request_id()
        }
        
        # Send request
        response = self.send_request(init_request)
        
        # Process response
        if not response or "result" not in response:
            debug("Failed to initialize server")
            return False
        
        # Extract server info
        result = response["result"]
        server_info = result.get("serverInfo", {})
        
        self.server_name = server_info.get("name", "Unknown Server")
        self.server_version = server_info.get("version", "Unknown")
        
        debug(f"Server information: {self.server_name} v{self.server_version}")
        
        # Send initialized notification
        debug("Sending initialized notification")
        self.send_notification({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })
        
        # Wait briefly for server to process notification
        time.sleep(0.5)
        
        return True
    
    def fetch_tool_definitions(self):
        """Fetch tool definitions from the MCP server with improved error handling"""
        debug("Fetching tool definitions")
        
        tool_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": self.get_next_request_id()
        }
        
        # Send request with detailed logging
        debug("Sending tools/list request")
        response = self.send_request(tool_request)
        
        if not response:
            debug("No response received for tools/list request")
            return False
        
        if "error" in response:
            debug(f"Error in tools/list response: {response['error']}")
            return False
        
        if "result" not in response:
            debug(f"Missing 'result' field in response: {response}")
            return False
        
        result = response["result"]
        
        if "tools" not in result:
            debug(f"Missing 'tools' field in result: {result}")
            return False
        
        # Successfully received tools
        self.tool_definitions = result["tools"]
        debug(f"Received {len(self.tool_definitions)} tool definitions")
        
        # Create tool wrappers
        debug("Creating tool wrappers")
        self.create_tool_wrappers()
        debug(f"Created {len(self.tools)} tool wrappers")
        return True
    
    def create_tool_wrappers(self):
        """Create wrapper functions for each tool with simplified parameter handling"""
        # Reset tools dictionary
        self.tools = {}
        
        # Process each tool definition
        for tool_def in self.tool_definitions:
            # Extract basic info
            tool_name = tool_def.get("name")
            if not tool_name:
                continue
                
            description = tool_def.get("description", "No description")
            input_schema = tool_def.get("inputSchema", {})
            
            # Determine parameter type
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            is_string_param = len(properties) == 1 and "param" in properties
            
            # Create function that wraps this tool
            def make_wrapper(name, is_string):
                def wrapper(*args, **kwargs):
                    if args:
                        # Handle positional arguments
                        arg = args[0]
                        if is_string:
                            return self.execute_tool(name, {"param": str(arg)})
                        elif isinstance(arg, dict):
                            return self.execute_tool(name, arg)
                        else:
                            return self.execute_tool(name, {"param": str(arg)})
                    elif kwargs:
                        # Handle keyword arguments
                        return self.execute_tool(name, kwargs)
                    else:
                        # No arguments
                        return self.execute_tool(name, {})
                return wrapper
            
            # Create the wrapper function with proper closure
            wrapper = make_wrapper(tool_name, is_string_param)
            wrapper.__name__ = tool_name
            wrapper.__doc__ = description
            
            # Store tool information
            param_info = {
                "type": "string" if is_string_param else "object",
                "required": bool(required)
            }
            
            self.tools[tool_name] = {
                "method": wrapper,
                "description": description,
                "param_info": param_info,
                "response": f"Example response from {tool_name}"
            }
        
        debug(f"Created {len(self.tools)} tool wrappers")
    
    def execute_tool(self, tool_name, params):
        """Execute a tool on the MCP server with simplified parameter handling"""
        # Process parameters based on tool type
        mcp_params = params
        param_info = self.tools.get(tool_name, {}).get("param_info", {})
        
        # Handle string parameters more efficiently
        if param_info.get("type") == "string":
            if isinstance(params, dict):
                if "param" in params:
                    # Already in correct format
                    pass
                else:
                    # Take first value
                    mcp_params = {"param": next(iter(params.values()), "")}
            else:
                # Convert non-dict to string param
                mcp_params = {"param": str(params) if params is not None else ""}
        
        # Send the tool call
        tool_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": mcp_params
            },
            "id": self.get_next_request_id()
        }
        
        # Execute the request
        response = self.send_request(tool_request)
        
        # Handle no response
        if not response:
            return {"error": f"No response from server for tool: {tool_name}"}
        
        # Handle JSON-RPC errors
        if "error" in response:
            error = response["error"]
            return {"error": f"Server error: {error.get('message', 'Unknown error')}"}
        
        # Handle tool execution result
        if "result" in response:
            result = response["result"]
            
            # Check if tool reported an error
            if result.get("isError"):
                content = result.get("content", [])
                error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
                return {"error": error_text}
            
            # Process successful result content
            content = result.get("content", [])
            
            # Empty content
            if not content:
                return {"result": "Operation completed successfully"}
            
            # Process text content
            if content[0].get("type") == "text":
                text = content[0]["text"]
                
                # Try parsing as JSON
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
            
            # Return content for other types
            return content
        
        # Unexpected response format
        return {"error": "Invalid response format from server"}
    
    def send_request(self, request):
        """Send a JSON-RPC request to the MCP server with optimized error handling"""
        # Check server process
        if not self.server_process:
            debug("No server process exists")
            return None
        
        if self.server_process.poll() is not None:
            debug(f"Server process terminated with exit code: {self.server_process.poll()}")
            self._check_log_file()
            return None
        
        try:
            # Extract request info
            method = request.get("method", "unknown")
            request_id = request.get("id", "none")
            
            # Send request
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            debug(f"Sent request: method={method}, id={request_id}")
            
            # Set timeout based on request type
            timeout = 30 if method == "tools/list" else 10
            debug(f"Waiting for response (timeout: {timeout}s)")
            
            # Read response with timeout
            start_time = time.time()
            response_str = None
            
            # Wait for response
            while time.time() - start_time < timeout:
                # Check if server is still running
                if self.server_process.poll() is not None:
                    debug(f"Server terminated during request, exit code: {self.server_process.poll()}")
                    self._check_log_file()
                    return None
                
                # Log wait status occasionally
                elapsed = time.time() - start_time
                if int(elapsed) % 3 == 0 and elapsed > 1:
                    debug(f"Still waiting after {int(elapsed)}s")
                
                # Try to read from stdout
                line = self.server_process.stdout.readline()
                if line and line.strip():
                    response_str = line.strip()
                    debug(f"Received response after {elapsed:.1f}s")
                    break
                
                time.sleep(0.1)
            
            # Handle timeout
            if not response_str:
                debug(f"No response after {timeout}s")
                self._check_log_file()
                return None
            
            # Parse and return response
            try:
                return json.loads(response_str)
            except json.JSONDecodeError as e:
                debug(f"Invalid JSON response: {e}")
                debug(f"Response data: {response_str[:100]}...")
                return None
                
        except Exception as e:
            debug(f"Error in send_request: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None
    
    def send_notification(self, notification):
        """Send a JSON-RPC notification to the MCP server (no response expected)"""
        if not self.server_process or self.server_process.poll() is not None:
            return False
        
        try:
            # Send the notification
            notification_str = json.dumps(notification) + "\n"
            self.server_process.stdin.write(notification_str)
            self.server_process.stdin.flush()
            return True
        except Exception:
            return False
    
    def stop_server(self):
        """Stop the MCP server with some cleanup logic"""
        if not self.server_process:
            return
            
        debug(f"Stopping MCP server (PID: {self.server_process.pid})")
        
        try:
            # Only attempt graceful shutdown if server is running
            if self.server_process.poll() is None:
                # Try shutdown request
                debug("Sending shutdown request")
                shutdown_request = {
                    "jsonrpc": "2.0",
                    "method": "shutdown",
                    "id": self.get_next_request_id()
                }
                
                # Send shutdown with short timeout
                try:
                    self.server_process.stdin.write(json.dumps(shutdown_request) + "\n")
                    self.server_process.stdin.flush()
                    
                    # Send exit notification
                    self.server_process.stdin.write(json.dumps({
                        "jsonrpc": "2.0", 
                        "method": "exit"
                    }) + "\n")
                    self.server_process.stdin.flush()
                    
                    # Wait briefly for graceful exit
                    for _ in range(5):
                        if self.server_process.poll() is not None:
                            break
                        time.sleep(0.2)
                except:
                    # Ignore errors during shutdown request
                    pass
                
                # Force termination if still running
                if self.server_process.poll() is None:
                    debug("Terminating server process")
                    self.server_process.terminate()
                    time.sleep(0.5)
                    
                    # Force kill if needed
                    if self.server_process.poll() is None:
                        debug("Killing server process")
                        self.server_process.kill()
        
        except Exception as e:
            debug(f"Error stopping server: {e}")
        finally:
            self.server_process = None
    
    def get_tools(self):
        """Return the tools dictionary for the ToolProvider interface"""
        return self.tools

    def _check_log_file(self):
        """Check log file for diagnostic information"""
        # Verify log file exists
        if not hasattr(self, 'log_file') or not os.path.exists(self.log_file):
            debug("No log file available")
            return None
            
        try:
            # Read log content
            with open(self.log_file, "r") as f:
                lines = f.readlines()
            
            if not lines:
                debug("Log file is empty")
                return None
            
            # Get just the last few lines
            tail_lines = lines[-10:] if len(lines) > 10 else lines
            debug("Server log tail:")
            for line in tail_lines:
                line = line.strip()
                if line:
                    debug(f"  LOG: {line}")
                    
            return "".join(lines)
        except Exception as e:
            debug(f"Error reading log: {e}")
            return None

class ToolAgentMCPClient:
    """ToolAgent-based MCP Client that connects to MCP servers"""
    
    def __init__(self, model_name="gemini-2.0-flash"):
        """Initialize the Client with a ToolAgent instance"""
        self.agent = ToolAgent(model_name=model_name)
        self.mcp_providers = []
        
        debug(f"Initialized ToolAgent MCP Client with model: {model_name}")
    
    def connect_mcp_server(self, server_command, server_args=None):
        """
        Connect to an MCP server and register its tools
        
        Args:
            server_command: Command to start the server (e.g., "python mcp_server.py")
            server_args: Optional list of arguments to pass to the server
            
        Returns:
            MCPToolProvider instance if successful, None otherwise
        """
        # Create and start a new MCP tool provider
        provider = MCPToolProvider(server_command, server_args)
        
        if provider.start_server():
            # Register the provider with the agent
            self.agent.register_provider(provider)
            self.mcp_providers.append(provider)
            
            debug(f"Connected to MCP server: {provider.server_name}")
            debug(f"Registered {len(provider.tools)} tools from the server")
            
            return provider
        else:
            debug("Failed to connect to MCP server")
            return None
    
    def create_conversation(self):
        """Create a new conversation with the agent"""
        return self.agent.create_conversation()
    
    def send_message(self, conversation, message):
        """Send a message to the agent and get the response"""
        return self.agent.process_message(conversation, message)
    
    def get_tools_info(self):
        """Get information about all registered tools"""
        return [
            {"name": name, "description": info["description"]}
            for name, info in self.agent.api_functions.items()
        ]
    
    def cleanup(self):
        """Clean up all MCP server connections"""
        for provider in self.mcp_providers:
            provider.stop_server()
        
        self.mcp_providers = []
        debug("Cleaned up all MCP server connections")

def run_example(config_file=None, server_name=None, model_name="gemini-2.0-flash"):
    """Run a simplified example using the MCP client"""
    # Load config
    config = load_mcp_config(config_file)
    servers_config = config.get("mcpServers", {})
    
    if not servers_config:
        print("No server configurations found. Please check your config file.")
        return
    
    # Create client
    client = ToolAgentMCPClient(model_name=model_name)
    connected_servers = []
    
    try:
        # Connect to server(s)
        for name, server_config in servers_config.items():
            if (server_name and name == server_name) or not server_name:
                print(f"Connecting to MCP server: {name}")
                provider = client.connect_mcp_server(
                    server_config["command"], 
                    server_config.get("args", [])
                )
                if provider:
                    print(f"Connected to {provider.server_name} v{provider.server_version}")
                    print(f"Available tools: {len(provider.tools)}")
                    connected_servers.append(name)
        
        if not connected_servers:
            print("Failed to connect to any server")
            return
        
        # Create a conversation
        conversation = client.create_conversation()
        
        # Print available tool count
        tools = client.get_tools_info()
        print(f"\nAvailable Tools ({len(tools)}):")
        
        # Chat loop with simplified commands
        print("\nChat with the agent (type 'exit' to quit, 'tools' to list tools):")
        while True:
            user_input = input("> ")
            cmd = user_input.lower().strip()
            
            # Handle exit commands
            if cmd in ["exit", "quit", "bye"]:
                break
            
            # Handle tools command
            if cmd == "tools":
                print("\nAvailable Tools:")
                for tool in sorted(tools, key=lambda x: x['name']):
                    print(f"- {tool['name']}: {tool['description']}")
                continue
            
            # Skip empty input
            if not cmd:
                continue
            
            # Process normal user input
            try:
                result = client.send_message(conversation, user_input)
                if isinstance(result, dict) and "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"Agent: {result.get('text', str(result))}")
            except Exception as e:
                print(f"Error processing message: {e}")
                if DEBUG_ENABLED:
                    import traceback
                    traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        if DEBUG_ENABLED:
            import traceback
            traceback.print_exc()
    finally:
        # Clean up
        print("Cleaning up...")
        client.cleanup()
        print("Done")

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='ToolAgent MCP Client')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--server', help='Name of server to connect to')
    parser.add_argument('--model', default="gemini-2.0-flash", help='Model name to use')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Set debug mode
    DEBUG_ENABLED = args.debug
    
    # Run the example
    run_example(config_file=args.config, server_name=args.server, model_name=args.model)