# Web Agent

The `WebAgent` is a browser automation agent built on `ToolAgent`. It uses an LLM along with Playwright to automate web interactions, allowing for complex web-based tasks to be completed through natural language instructions.

## Features

- **Browser Automation**: Navigate, click, type, and interact with web elements
- **Tool-Based Architecture**: Uses the `ToolAgent` and `ToolProvider` framework
- **Element Detection**: Tries to intelligently identify interactive elements on web pages
- **Content Extraction**: Extracts and formats page content for better LLM understanding, and minimizing input token usage
- **Structured Output**: Provides summarized results of web actions

## Architecture

The web agent system is composed of two main components:

### 1. PageManagerToolProvider

This class is a `ToolProvider` implementation that wraps Playwright's browser automation capabilities as tools:

- **Browser Management**: Handles browser initialization, page navigation, and cleanup
- **Element Interaction**: Provides tools to click, type, and extract data from web elements
- **Content Processing**: Extracts relevant elements from pages while filtering out noise
- **Visibility Detection**: Filters out invisible elements to focus on actionable content
- **CSS Selector Support**: Uses standard CSS selectors for element identification

### 2. WebAgent

This class extends the `ToolAgent` class to support running web automation tasks:

- **Task Execution**: Processes user tasks using the `run_task` method
- **Specialized Prompting**: Uses web-specific prompt templates to guide the LLM
- **Completion Indicators**: Detects task completion through specific output phrases
- **Performance Tracking**: Measures token usage and execution time

## Available Web Tools

The `PageManagerToolProvider` exposes the following tools:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `navigate` | Navigate to a URL | `string` URL to navigate to |
| `click` | Click on an element | `string` CSS selector |
| `type_text` | Type text into a field | `object` with `selector` and `text` |
| `get_text` | Get text from an element | `string` CSS selector |
| `get_title` | Get page title | None |
| `get_current_url` | Get current URL | None |
| `wait_for_navigation` | Wait for navigation to complete | None |
| `wait_seconds` | Wait for specified time | `number` seconds |
| `get_page_content` | Get simplified page content | None |

## How It Works

### Task Processing Flow

1. **Initialization**: The `WebAgent` initializes with a specified LLM model and registers the `PageManagerToolProvider`
2. **Task Submission**: User submits a task via the `run_task` method
3. **Conversation Creation**: A new conversation is created with web-specific instructions
4. **LLM Processing**: The task is sent to the LLM, which analyzes it and decides what actions to take
5. **Tool Execution**: The LLM calls appropriate web tools, which execute browser actions
6. **Result Processing**: The LLM receives tool results and uses them for subsequent decisions
7. **Task Completion**: When the task is complete, the LLM outputs a summary with "task complete"

### Page Content Extraction

The `get_page_content` tool:
1. Identifies important elements matching specific CSS selectors
2. Processes each element to extract tag name, attributes, and text content
3. Filters out invisible elements and duplicates
4. Creates simplified HTML representations
5. Returns a structured view of the page focused on interactive elements

## Usage Examples

### Basic Usage

```python
from web_agent import WebAgent

# Create a web agent with specified model
agent = WebAgent(model_name="gemini-2.0-flash")

try:
    # Run a task
    result = agent.run_task(
        "Navigate to duckduckgo.com, search for 'climate news', and return the titles of the first 3 results"
    )
    
    # Print the result
    print(result["final_response"])
finally:
    # Clean up resources
    agent.close()
```

### Command Line Usage
```bash
python web_agent.py "Go to wikipedia.org and find the featured article of the day"
```

### Usage with an Initial URL
```python
agent = WebAgent(model_name="gemini-2.0-flash")

# Navigate to a starting URL
agent.web_provider.navigate("https://www.example.com")

# Run a complex task
result = agent.run_task("Find the contact form, fill it out with mock data, and confirm submission")

# Analyze the interaction log
for entry in result["log"]:
    if entry["stage"] == "tool_call":
        print(f"Tool used: {entry['tool']}")

# Check token usage
print(f"Total tokens used: {result['token_usage']['input'] + result['token_usage']['output']}")
```
