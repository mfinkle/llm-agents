# LLM Agents

This repository contains two agents: `tool_agent.py` and `web_agent.py`. These agents are designed to perform specific tasks using large language models (LLMs). The project is really a basic exploration into the agent space. I wanted to learn some of the basic, hard truths of trying to build raw agents _before_ moving on to leverage full-blown frameworks that hide the details. These agents are purposefully using the bare minimum number of dependencies.

Some background and details on the project:
- [Exploring LLMs as Agents: A Minimalist Approach](https://starkravingfinkle.org/blog/2025/03/exploring-llms-as-agents-a-minimalist-approach/)
- [Exploring LLMs as Agents: Taking Action](https://starkravingfinkle.org/blog/2025/03/exploring-llms-as-agents-taking-action/)
- [Exploring LLMs as Agents: Planning via Prompting](https://starkravingfinkle.org/blog/2025/03/exploring-llms-as-agents-planning-via-prompting/)

## Setup
### Using a Virtual Environment

It is a good practice to use a Python virtual environment to manage dependencies and avoid conflicts with other projects. To create and activate a virtual environment, run the following commands:

On macOS and Linux:
```
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```
python -m venv venv
.\venv\Scripts\activate
```

Once the virtual environment is activated, you can install the necessary dependencies.

## Dependencies
The agent scripts use `llm` to interact with different LLM models. More information on setting up and using `llm` can be found in its [documentation](https://llm.datasette.io/en/stable/index.html). You'll need to make sure `llm` is configured to work with at least one LLM.

The agent in `web_agent.py` uses `playwright` to launch and automate a web browser. More information on setting up and using `playwright` can be found in its Python [documentation](https://playwright.dev/python/docs/intro). You'll need to make sure `playwright` is setup to work with at least one we browser. I installed `chromium` since I do not use that for my primary web browser. That removes any conflicts between running the script and my actual browsing.

To install the necessary dependencies, run:

```
pip install -r requirements.txt
```

## Agents

### Tool Agent

The `tool_agent.py` script provides a reusable `ToolAgent` class that can interact with various tools and perform automated tasks. The class is designed to be modular, extensible, and easy to integrate into other applications.

Features of the Tool Agent:

- **Class-Based Architecture** - Modular design that can be extended and integrated into other applications
- **Tool Provider & Registry** - Organized collection of tools via provider classes. Tools registered with detailed metadata and structured XML documentation
- **ReAct Reasoning** - Transparent step-by-step reasoning process for better problem-solving  
- **Validation** - Handles JSON parsing errors and schema validation with multiple retry attempts
- **Token Usage Tracking** - Built-in tracking of input and output tokens for monitoring usage and costs

[ToolAgent readme](tool_agent.md)

#### Running the Tool Agent

You can use the Tool Agent in several ways:

1. Interactive chat mode:
```
python tool_agent_test.py
```

2. Benchmark the agent's performance with a simple set of tests:
```
python tool_agent_benchmark.py --verbose
```

3. Import the class in your own scripts:
```python
from tool_agent import ToolAgent

agent = ToolAgent(model_name='gemini-2.0-flash')
conversation = agent.create_conversation()
result = agent.process_message(conversation, "What is the weather in 94105?")
print(result['text'])
```

### Web Agent

The `web_agent.py` script provides a browser automation agent (`WebAgent`) built on top of the `ToolAgent` architecture. It combines the power of LLMs with Playwright's browser automation capabilities, allowing complex web tasks to be performed through natural language instructions.

Features of the Web Agent:

- **Browser Automation** - Navigate, click, type, and interact with web elements through natural language commands
- **Built on ToolAgent** - Uses the `ToolAgent` and `ToolProvider` architecture for tool management and reasoning
- **Element Detection**: Tries to intelligently identify interactive elements on web pages
- **Visibility Filtering** - Focus on visible elements for better task completion
- **Clean Output** - Returns well-structured responses with task summaries

[WebAgent readme](web_agent.md)

#### Running the Web Agent

You can use the Web Agent in several ways:

1. Run a web task from the command line:
```
python web_agent.py "Navigate to wikipedia.org and find the featured article of the day"
```

2. Import and use in your own scripts:
```python
from web_agent import WebAgent

agent = WebAgent(model_name='gemini-2.0-flash')

try:
    # Navigate to a starting URL
    agent.web_provider.navigate('https://www.example.com')
    
    # Run a task
    result = agent.run_task('Fill out the contact form with dummy data')
    
    # Print the result
    print(result['final_response'])
finally:
    agent.close()  # Always close the browser when done
```

3. Extract task performance metrics:
```python
result = agent.run_task("Find the pricing information on the website")

print(f"Task Status: {result['status']}")
print(f"Duration: {result['duration_seconds']:.2f} seconds")
print(f"Input tokens: {result['token_usage'].get('input', 0)}")
print(f"Output tokens: {result['token_usage'].get('output', 0)}")
```

### MCP Server and Client

This repository also includes a Model Context Protocol (MCP) implementation, using the `stdio` transport:

- **`tool_provider_mcp_server.py`** - A server that exposes `ToolProvider` tools via the Model Context Protocol
- **`tool_agent_mcp_client.py`** - A client that connects to MCP servers and makes their tools available to `ToolAgent`

The Model Context Protocol (MCP) allows language models to discover and invoke tools provided by external servers. This implementation  attempts to follow the [MCP specification](https://spec.modelcontextprotocol.io/specification/2025-03-26/).

#### Running the MCP Server

The MCP server exposes tools from various providers through a standardized protocol. You will likely not launch the server yourself, but will config an MCP Client to launch:

```bash
python tool_provider_mcp_server.py [--debug]
```

#### Running the MCP Client

The MCP client connects to one or more MCP servers and registers their tools with a ToolAgent:

```bash
python tool_agent_mcp_client.py
```

Configuration options:
- `--config` - Path to a custom config file
- `--server` - Name of a specific server to connect to
- `--model` - Model name to use (default: gemini-2.0-flash)
- `--debug` - Enable debug output

#### MCP Configuration

The client looks for server configurations in a file called `mcp_config.json`. By default, it searches in:
1. The current directory
2. `~/.config/mcp_config.json`
3. `~/Library/Application Support/MCP/mcp_config.json`

Example configuration:
```json
{
  "mcpServers": {
    "mock": {
      "command": "python",
      "args": ["/Path/To/Server/tool_provider_mcp_server.py"]
    }
  }
}
```

Each entry in mcpServers defines a named server with a command to start it and optional arguments.

**NOTE:** If you're running your Python-based MCP Server in a virtual environment, use the full path to the python binary, and it's always best to use the absolute path to the server, since you don't really know what the working directory will be:
```json
{
  "mcpServers": {
    "mock": {
      "command": "/Path/To/Server/venv/bin/python",
      "args": ["/Path/To/Server/tool_provider_mcp_server.py"]
    }
  }
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

These are both very basic, almost remedial examples of building agents with LLMs, but contributions are welcome! Please open an issue or submit a pull request for any changes.
