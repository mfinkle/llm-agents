# Tool Agent

The `ToolAgent` class implements a conversational agent with tool-calling capabilities and a "Reasoning & Action" (ReAct) reasoning strategy. It allows users to interact with an AI assistant that can access various tools or functions to help answer queries and solve tasks.

## Features

- **Reusable Class** - Modular design that can be extended and integrated into other applications
- **Tool Provider & Registry** - Organized collection of tools via provider classes. Tools registered with detailed metadata and structured XML documentation
- **ReAct Reasoning** - Transparent step-by-step reasoning process for better problem-solving  
- **Validation** - Handles JSON parsing errors and schema validation with multiple retry attempts
- **Token Usage Tracking** - Built-in tracking of input and output tokens for monitoring usage and costs

## Tool Provider System

The `ToolAgent` uses a plugin architecture, "Tool Providers", that makes it easy to add, remove, and organize tools:

```python
# Register tool providers
agent = ToolAgent(model_name='gemini-2.0-flash')
agent.register_provider(UtilityToolProvider())
agent.register_provider(AppointmentToolProvider())
```

Each provider implements a standard interface:

- `get_tools()` - Returns a dictionary of tools with metadata
- `_initialize_data()` - Sets up any data needed by the provider

## Reasoning & Action (ReAct)
The tool agent implements a ReAct reasoning strategy, combined with Few-shot prompting, which enables more reliable problem-solving:

1. Explicit Reasoning: The model articulates its step-by-step thinking process
2. Transparent Decision Making: The reasoning process is visible to users via the "thought" field
3. Better Problem Decomposition: Complex queries are broken down into manageable steps

## Token Usage Tracking
The agent tracks token usage for all LLM interactions:
```python
# Get token usage statistics
usage = agent.get_token_usage()
print(f"Input tokens: {usage['input']}")
print(f"Output tokens: {usage['output']}")
print(f"Total tokens: {usage['input'] + usage['output']}")

# Reset token usage counters
agent.reset_token_usage()
```

## Conversation Flow
The main components of the tool agent are:

1. Initialization: The agent initializes a conversation with the language model, providing available tools
2. User Input: The agent processes user input
3. LLM Response Processing: The user query is sent to the language model, which returns a response
4. Validation: The response is validated for proper JSON formatting and required fields
5. Chain of Thought Display: The model's reasoning process is displayed if present
6. Action Extraction: The JSON response is parsed to determine if it's a direct answer or a tool call
7. Tool Handling: If a tool call is requested:
- The tool name and parameters are extracted and validated
- The appropriate function is called with the provided parameters
- The function result is sent back to the language model
- This process continues until the model provides a final answer
8. Output Display: The final answer is displayed to the user

## Response Format
The agent expects responses from the language model in a specific JSON format:
* For direct responses to the user:
```json
{
  "thought": "Reasoning process for this response...",
  "type": "output",
  "value": "text of your response"
}
```

* For tool calls:
```json
{
  "thought": "Reasoning process for this response...",
  "type": "call_tool",
  "tool": "function_name",
  "param": "parameters"
}
```

## Error Handling
The agent includes error handling for:

- Invalid tool names
- Parameter validation and conversion
- Errors during function execution
- Improper JSON formatting in responses
- Multiple retry attempts for validation failures

## Testing and Benchmarking Tools
### Interactive Testing
You can use the interactive test mode to chat with the agent:
```bash
python tool_agent_test.py
```
This launches a chat session in a terminal window where you can test the agent with various queries.

### Benchmarking
The tool_agent_benchmark.py script provides a basic benchmarking system:
```bash
python tool_agent_benchmark.py --verbose
```

Features of the benchmark tool:

- **Test Cases**: Run multiple predefined test cases
- **Success Metrics**: Track success rates, execution times, and token usage
- **Reporting**: Get detailed reports on test results
- **CSV/JSON Export**: Export results for further analysis
- **Token Usage**: Track and analyze token consumption

Example benchmark output:
```bash
=== BENCHMARK SUMMARY ===
Model: gemini-2.0-flash
Total Tests: 12
Successful Tests: 10
Success Rate: 83.33%
Average Execution Time: 3.47s

=== TOKEN USAGE SUMMARY ===
Total Input Tokens: 24,532
Total Output Tokens: 8,764
Total Tokens: 33,296
Average Tokens per Successful Test: 2,774.50
```

## API Usage
You can integrate the `ToolAgent` into your own applications:
```python
from tool_agent import ToolAgent

# Create an instance
agent = ToolAgent(model_name='gemini-2.0-flash')

# Create a conversation
conversation = agent.create_conversation()

# Process messages
result = agent.process_message(conversation, 'What is the weather in San Francisco?')

# Access the result
print(result['text'])  # The response text
print(result['log'])   # The interaction log
print(result['token_usage'])  # Token usage statistics
```

## Creating Custom Tool Providers
You can create your own tool providers by extending the `ToolProvider` base class:
```python
class MyCustomProvider(ToolProvider):
    def _initialize_data(self):
        # Initialize your tool's data
        self.my_data = {...}
    
    def get_tools(self):
        return {
            'my_custom_tool': {
                'method': self.my_custom_tool_method,
                'description': 'Description of what this tool does',
                'response': 'Example response format',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Parameter description'
                }
            }
        }
        
    def my_custom_tool_method(self, param):
        # Implement your tool functionality
        return {'result': 'custom result'}
```
Then register your provider with the agent:

```python
agent.register_provider(MyCustomProvider())
```