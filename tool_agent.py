import datetime
import json
import re
import llm

from tool_providers import UtilityToolProvider, AppointmentToolProvider, ProgramToolProvider, StoreLocatorToolProvider

# TODO: Add a human feedback mechanism (thumbs up/down) to improve the model
# TODO: Save positive & negative feedback to a file for future training

class ToolAgent:
    """Class to manage LLM agent tools, validation, and execution"""
    
    # System prompt templates
    SYSTEM_PROMPT_TEMPLATE = """
    You are a helpful assistant that can answer various tasks.
    User inputs will be passed as plain text.
    
    ALWAYS use reasoning. First think through the problem step-by-step, then decide what action to take.
    ALWAYS use the tools provided.
    
    All responses MUST use JSON format without preamble with a schema structure.

    For tool calls, use this JSON schema structure:
    {{
      "thought": "Your reasoning for choosing this tool...",
      "type": "call_tool",
      "tool": "tool_name",
      "param": "tool_parameters"
    }}
    
    IMPORTANT: Pay careful attention to the expected parameter formats for each tool:
    - String parameters should be passed as simple strings: "param": "90210"
    - For tools that expect lists, use proper JSON arrays: "param": ["python", "web"]
    - For tools that expect objects, use proper JSON objects: "param": {{"location": "Springfield, IL", "store_type": "grocery"}}
    - Some tools don't need parameters - omit the "param" field or set to null

    IMPORTANT: Do not assume or guess or hallucinate information. Call the tools to get ALL needed information.
    - You DO NOT know the current date or time. Use tools to determine the current date and time.
    - You CANNOT do math. Use tools to calculate math.
    
    For direct responses to the user, use this JSON schema structure:
    {{
      "thought": "Your reasoning for this response...",
      "type": "output",
      "value": "text of your response"
    }}
    
    {extra_prompt}

    Here are the tools you can call:
    {tool_registry_xml}

    WAIT for the user to provide input before responding.
    """
    
    def __init__(self, model_name, temperature=0.0):
        """Initialize the tool agent with the specified model"""
        self.model_name = model_name
        self.temperature = temperature
        self.api_functions = {}
        
        # Initialize token usage tracking
        self.token_usage = {
            'input': 0,
            'output': 0
        }
        
        # Register default tool providers
        self.register_provider(UtilityToolProvider())
        self.register_provider(AppointmentToolProvider())
        self.register_provider(ProgramToolProvider())
        self.register_provider(StoreLocatorToolProvider())
    
    def register_provider(self, provider):
        """Register a provider's tools with the agent"""
        
        # Register all tools from the provider
        tools = provider.get_tools()
        for name, tool in tools.items():
            self.api_functions[name] = tool

    def register_tool(self, name, method, description, response, 
                      required=True, param_type='string', 
                      description_text='', item_type='any', schema=None):
        """Register an individual tool with the agent
        
        Args:
            name (str): The name of the tool
            method: The method to call
            description (str): Description of the tool
            response (str): Example response
            required (bool): Whether parameter is required
            param_type (Optional[str]): Type of parameter ('string', 'array', 'object', None)
            description_text (str): Description of the parameter
            item_type (str): For arrays, the type of items
            schema (dict): For objects, a dictionary mapping field names to descriptions
        """
        param_info = {
            'required': required,
            'type': param_type,
            'description': description_text,
        }
        
        # Add type-specific information
        if param_type == 'array':
            param_info['item_type'] = item_type
        elif param_type == 'object' and schema is not None:
            param_info['schema'] = schema
        
        self.api_functions[name] = {
            'method': method,
            'description': description,
            'response': response,
            'param_info': param_info
        }
    
    def get_tool_registry_xml(self):
        """Get the tool registry in XML format for LLM context"""
        
        def param_to_xml(param_info):
            """Helper to convert param info to XML string"""
            param_type = param_info.get('type')
            required = str(param_info.get('required', True)).lower()
            desc = param_info.get('description', '')
            
            if param_type is None:
                return "<param>No parameter needed</param>"
            elif param_type == 'string':
                return f"<param type='string' required='{required}'>{desc}</param>"
            elif param_type == 'array':
                item_type = param_info.get('item_type', 'any')
                return f"<param type='array' item_type='{item_type}' required='{required}'>{desc}</param>"
            elif param_type == 'object':
                schema = param_info.get('schema', {})
                fields = ''.join(f"<field name='{k}'>{v}</field>" for k, v in schema.items())
                return f"<param type='object' required='{required}'>{desc}<schema>{fields}</schema></param>"
            
            return "<param>Invalid parameter type</param>"
        
        # Generate tool XML entries
        tools_xml = [
            f"""<tool>
                <name>{name}</name>
                <description>{details['description']}</description>
                <response>{details['response']}</response>
                {param_to_xml(details.get('param_info', {}))}
            </tool>"""
            for name, details in self.api_functions.items()
        ]
        
        return f"<tools>{''.join(tools_xml)}</tools>"
    
    def extract_action_from_response(self, response):
        """Extract the action from an LLM response as JSON, handling extraneous text"""
        action_raw = response.text().strip()
        print(f"Raw response: {action_raw}")

        # Try various JSON extraction methods in order
        for extractor in [
            # Direct parsing
            lambda text: json.loads(text),
            
            # Code block extraction
            lambda text: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text).group(1).strip()),
            
            # Braced content extraction
            lambda text: json.loads(re.search(r'(\{[\s\S]*\})', text).group(1).strip())
        ]:
            try:
                return extractor(action_raw), True
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return None, False
    
    def validate_action(self, action):
        """Validate the structure of an LLM action"""
        if not isinstance(action, dict):
            return False, 'Response must be a JSON object'
        
        if 'type' not in action:
            return False, 'Response must have a "type" field'
        
        if action['type'] not in ['output', 'call_tool']:
            return False, 'Type field must be "output" or "call_tool"'
        
        if action['type'] == 'call_tool' and 'tool' not in action:
            return False, 'Tool call must have a "tool" field'
        
        if action['type'] == 'output' and 'value' not in action:
            return False, 'Output must have a "value" field'
        
        return True, ''
    
    def validate_model_response(self, conversation, response, max_attempts=3):
        """Process and validate a model response, with multiple attempts if needed"""
        attempts = 0
        
        while attempts < max_attempts:
            extracted_action, json_success = self.extract_action_from_response(response)
            
            # If JSON parsing failed
            if not json_success:
                attempts += 1
                if attempts >= max_attempts:
                    # Return fallback action
                    return { 'type': 'output', 'value': 'I apologize, but I\'m having trouble understanding. Could you rephrase your request?' }, False
                
                # Ask for correctly formatted JSON
                correction_prompt = 'Your response was not valid JSON. Please provide a valid JSON response with the required structure.'
                response = conversation.prompt(correction_prompt, temperature=self.temperature)
                self.track_token_usage(response)
                continue
            
            # JSON parsed successfully, now validate the structure
            valid, error_message = self.validate_action(extracted_action)
            if valid:
                return extracted_action, True
            else:
                attempts += 1
                if attempts >= max_attempts:
                    # Return fallback action
                    return { 'type': 'output', 'value': 'I apologize, but I\'m having trouble processing your request.' }, False
                
                # Ask for correctly structured response
                correction_prompt = f"Your response format was invalid: {error_message}. Please provide a valid JSON response with the correct structure."
                response = conversation.prompt(correction_prompt, temperature=self.temperature)
                self.track_token_usage(response)
        
        # This should never be reached but just in case
        return {'type': 'output', 'value': 'Something went wrong with my processing.'}, False
    
    def validate_and_convert_param(self, function_name, param):
        """Validate and convert parameter for a specific function"""
        if function_name not in self.api_functions:
            return False, None, f"Unknown function: {function_name}"
        
        param_info = self.api_functions[function_name].get('param_info', {})
        required = param_info.get('required', True)
        param_type = param_info.get('type')
        description = param_info.get('description', '')
        
        # Functions that don't need parameters
        if not required or param_type is None:
            return True, None, None
            
        # Check if parameter is missing but required
        if param is None:
            return False, None, f"This tool requires a parameter: {description}"
        
        # Type conversion based on expected type
        try:
            if param_type == 'string':
                return True, str(param), None
                
            elif param_type == 'array':
                # Convert to array if string
                if isinstance(param, str):
                    if '[' in param and ']' in param:
                        param = json.loads(param)
                    else:
                        param = [param]
                elif not isinstance(param, list):
                    param = [param]
                    
                # Handle item type conversion if needed
                item_type = param_info.get('item_type', 'any')
                if item_type == 'string':
                    param = [str(item) for item in param]
                    
                return True, param, None
                
            elif param_type == 'object':
                # Parse JSON string if provided
                if isinstance(param, str):
                    try:
                        parsed = json.loads(param)
                        if isinstance(parsed, dict):
                            param = parsed
                        else:
                            return False, None, f"String must parse to an object. {description}"
                    except:
                        return False, None, f"Invalid JSON format. {description}"
                        
                # Must be a dict at this point
                if not isinstance(param, dict):
                    return False, None, f"Parameter must be an object. {description}"
                    
                # Validate required fields in schema
                schema = param_info.get('schema', {})
                missing = [k for k, v in schema.items() 
                          if 'optional' not in v.lower() and k not in param]
                if missing:
                    return False, None, f"Missing required fields: {', '.join(missing)}. {description}"
                    
                return True, param, None
                
            # Default case for unknown types
            return True, param, None
            
        except Exception as e:
            return False, None, f"Parameter conversion error: {str(e)}. {description}"
    
    def execute_tool(self, function_name, param=None):
        """Execute a tool with validation and conversion"""
        if function_name not in self.api_functions:
            return { 'error': f"Unknown tool: {function_name}" }
        
        # Validate and convert parameter
        valid, converted_param, error_message = self.validate_and_convert_param(function_name, param)
        if not valid:
            return {'error': error_message}
        
        try:
            # Execute the tool
            if converted_param is not None:
                return self.api_functions[function_name]['method'](converted_param)
            else:
                return self.api_functions[function_name]['method']()
        except Exception as e:
            return { 'error': f"Tool execution failed: {str(e)}" }
    
    def create_conversation(self, extra_prompt=''):
        """Create a new conversation with the initial system prompt"""
        conversation = llm.get_model(self.model_name).conversation()
        
        # Build the initial prompt
        tool_registry_xml = self.get_tool_registry_xml()
        initial_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(tool_registry_xml=tool_registry_xml, extra_prompt=extra_prompt)
        
        # Initialize the conversation
        # NOTE: You need to force the response to execute, or the system prompt will be ignored
        response = conversation.prompt(initial_prompt, temperature=self.temperature)
        print(f"Initial response: {response.text()}")
        
        # Track token usage for system prompt
        self.track_token_usage(response)
        return conversation
        
    def process_message(self, conversation, user_message):
        """Process a user message and return the appropriate response"""
        # Track tool calls and responses for debugging and analysis
        interaction_log = []

        # Get initial response and validate
        response = conversation.prompt(user_message, temperature=self.temperature)
        self.track_token_usage(response)
        action, success = self.validate_model_response(conversation, response)
                
        try:
            if 'thought' in action:
                interaction_log.append({ 'stage': 'initial_thought', 'content': action['thought'] })
            
            # Process tool calls
            while action['type'] == 'call_tool' and success:
                function_name = action.get('tool')
                param = action.get('param')
                
                interaction_log.append({ 'stage': 'tool_call', 'tool': function_name, 'param': param })
                result = self.execute_tool(function_name, param)
                interaction_log.append({ 'stage': 'tool_result', 'result': result })
                
                # If there was an error
                if 'error' in result:
                    response = conversation.prompt(f"Tool call failed: {result['error']}", temperature=self.temperature)
                else:
                    # Format the result as JSON
                    result_json = json.dumps(result)
                    response = conversation.prompt(f"Tool result: {result_json}", temperature=self.temperature)
                self.track_token_usage(response)
                action, success = self.validate_model_response(conversation, response)
                
                if 'thought' in action:
                    interaction_log.append({ 'stage': 'updated_thought', 'content': action['thought'] })
                
                # Break out if we're no longer doing tool calls or validation failed
                if action['type'] != 'call_tool' or not success:
                    break
            
            # Output response
            if action['type'] == 'output' and 'value' in action:
                final_response = { 
                    'text': action['value'], 
                    'log': interaction_log,
                    'token_usage': self.get_token_usage()
                }
                
                # Copy any additional fields from the action
                for key in ['replies', 'card']:
                    if key in action:
                        response[key] = action[key]
                
                return final_response
                
            return { 
                'text': "I'm sorry, I couldn't process that properly.", 
                'log': interaction_log,
                'token_usage': self.get_token_usage()
            }
                
        except Exception as e:
            return { 
                'error': f"Error processing message: {str(e)}", 
                'log': interaction_log,
                'token_usage': self.get_token_usage()
            }
    
    def track_token_usage(self, response):
        """Track token usage from a response object"""
        try:
            # Get usage statistics from the response
            usage = response.usage()
            self.token_usage['input'] += usage.input
            self.token_usage['output'] += usage.output
        except Exception as e:
            print(f"Error tracking token usage: {str(e)}")

    def get_token_usage(self):
        """Get the current token usage statistics"""
        return {
            'input': self.token_usage['input'],
            'output': self.token_usage['output'],
        }

    def reset_token_usage(self):
        """Reset token usage statistics"""
        self.token_usage = {
            'input': 0,
            'output': 0
        }
