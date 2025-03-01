# LLM Agents

This repository contains two main agents: `tool_agent.py` and `web_agent.py`. These agents are designed to perform specific tasks using large language models (LLMs). These scripts are really a basic exploration into the agent space. I want to learn some of the basic, hard truths of trying to build raw agents _before_ moving on to leverage full-blown frameworks that hide the details.

## Setup
### Using a Virtual Environment

It is a good practice to use a Python virtual environment to manage dependencies and avoid conflicts with other projects. To create and activate a virtual environment, run the following commands:

On macOS and Linux:
```
python3 -m venv env
source env/bin/activate
```

On Windows:
```
python -m venv env
.\env\Scripts\activate
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

The `tool_agent.py` script is designed to interact with various tools and perform automated tasks. Everything is self contained within the single Python script. The "tool" functions are mocked stand-ins for actual network connected tools. The purpose of the script is to visualize how to connect tools to an LLM and have the LLM use the tools to perform tasks and actions.

To run the tool agent, use the following command:

```
python tool_agent.py
```

### Web Agent

The `web_agent.py` script is designed to interact with web services and perform web-related tasks using a web browser. The agent is given the HTML content and a set of browser-automation tools it can use to interact with the web content. The purpose of the script is to evaluate how an LLM can manipulate _mostly_ unstructured content. Most web pages are *not* well structured.

To run the web agent, use the following command:

```
python web_agent.py
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

These are both very basic, almost remedial examples of building agents with LLMs, but contributions are welcome! Please open an issue or submit a pull request for any changes.
