# Tool Agent

The `tool_agent` is a Python script that implements a conversational agent with tool-calling capabilities. It allows users to interact with an AI assistant that can access various tools or functions to help answer queries and solve tasks.

## How It Works

### Tool Functions

The agent has access to a set of tool functions that enable it to perform specific tasks:

- `search_web(query)`: Simulates searching the web for a given query and returns search results
- `get_weather(zipcode)`: Simulates retrieving weather information for a specified zip code
- `get_zipcode(city)`: Simulates retrieving zip code for a specified city
- `calculate(expression)`: Evaluates mathematical expressions safely
- `get_datetime()`: Returns the current date and time

### API Function Registry

Each tool function is registered in an `api_functions` dictionary with metadata including:
- The implementation method
- A description of what the function does
- Example usage format
- Expected response format

### Conversation Loop

The main components of the tool agent are:

1. **Initialization**: The agent initializes a conversation with the language model, providing a list of available tools
2. **User Input**: The agent waits for user input in a continuous loop
3. **LLM Response Processing**: When the user enters a query, it's sent to the language model, which returns a response in JSON format
4. **Action Extraction**: The JSON response is parsed to determine if it's a direct answer or a tool call
5. **Tool Handling**: If a tool call is requested:
   - The tool name and parameters are extracted
   - The appropriate function is called with the provided parameters
   - The function result is sent back to the language model
   - This process continues until the model provides a final answer
6. **Output Display**: The final answer is displayed to the user

### Response Format

The agent expects responses from the language model in a specific JSON format:
- For direct answers: `{"type": "output", "value": "text response"}`
- For tool calls: `{"type": "call_function", "tool": "function_name", "param": "parameters"}`

### Error Handling

The agent includes error handling for:
- Invalid tool names
- Errors during function execution
- Improper JSON formatting in responses

## Example Usage

To start the tool agent:

```python
python tool_agent.py
```

Sample conversation:
```
You: What's the weather in Beverly Hills?
Function result: {'zipcode': '90210'}
Function result: {'temperature': '75 F', 'conditions': 'Sunny'}
Agent: The weather in Beverly Hills (zipcode 90210) is 75 F and Sunny.
```

The agent will continue running until the user types "exit", "quit", or "bye" to end the conversation.