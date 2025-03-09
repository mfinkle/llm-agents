# Tool Agent

The `tool_agent` is a Python script that implements a conversational agent with tool-calling capabilities and Chain of Thought reasoning. It allows users to interact with an AI assistant that can access various tools or functions to help answer queries and solve tasks.

## How It Works

### Tool Functions

The agent has access to a set of tool functions that enable it to perform specific tasks:

- `get_weather(zipcode)`: Retrieves weather information for a specified zip code
- `get_zipcode(city)`: Retrieves zip code for a specified city
- `calculate(expression)`: Evaluates mathematical expressions safely
- `get_datetime()`: Returns the current date and time
- `get_appointment_specialties()`: Retrieves a list of available specialties for scheduling appointments
- `get_available_appointments(specialty)`: Retrieves available appointments for a given specialty
- `book_appointment(booking_data)`: Books an appointment based on provided booking data
- `get_my_appointments()`: Retrieves the list of appointments booked by the user
- `cancel_appointment(appointment_id)`: Cancels a booked appointment based on the provided appointment ID

### API Function Registry

Each tool function is registered in an `api_functions` dictionary with metadata including:
- The implementation method
- A description of what the function does
- Example usage format
- Expected response format

The metadata is used to build context for the system prompt as an XML-formatted tool registry.

### Chain of Thought Reasoning

The tool agent implements Chain of Thought (CoT) reasoning, which enables more reliable problem-solving:

1. **Explicit Reasoning**: The model articulates its step-by-step thinking process
2. **Transparent Decision Making**: The reasoning process is visible to users via the "thought" field
3. **Better Problem Decomposition**: Complex queries are broken down into manageable steps

### Conversation Loop

The main components of the tool agent are:

1. **Initialization**: The agent initializes a conversation with the language model, providing available tools
2. **User Input**: The agent waits for user input in a continuous loop
3. **LLM Response Processing**: The user query is sent to the language model, which returns a response
4. **Validation**: The response is validated for proper JSON formatting and required fields
5. **Chain of Thought Display**: The model's reasoning process is displayed if present
6. **Action Extraction**: The JSON response is parsed to determine if it's a direct answer or a tool call
7. **Tool Handling**: If a tool call is requested:
   - The tool name and parameters are extracted and validated
   - The appropriate function is called with the provided parameters
   - The function result is sent back to the language model
   - This process continues until the model provides a final answer
8. **Output Display**: The final answer is displayed to the user

### Response Format

The agent expects responses from the language model in a specific JSON format:

- For direct responses to the user:
```json
{
  "thought": "Reasoning process for this response...",
  "type": "output",
  "value": "text of your response"
}
```

- For tool calls:
```json
{
  "thought": "Reasoning process for this response...",
  "type": "call_tool",
  "tool": "function_name",
  "param": "parameters"
}
```

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
Thought: The user wants to know the weather in Beverly Hills. First, I need to get the zipcode for Beverly Hills, then I can use that to get the weather.
Tool result: {"zipcode": "90210"}
Thought: Now that I have the zipcode for Beverly Hills, I can get the weather.
Tool result: {"temperature": "75 F", "conditions": "Sunny"}
Thought: I have the weather information. Now I need to present it to the user.
Agent: The weather in Beverly Hills is 75 F and Sunny.
```

The agent will continue running until the user types "exit", "quit", or "bye" to end the conversation.