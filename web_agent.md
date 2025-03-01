# Web Agent

The `web_agent` is a Python script designed to automate interactions with web pages using the Playwright library. It leverages a language model (LLM) to generate actions based on the HTML content of the current page and the specified task. The agent can perform various actions such as clicking buttons, typing text, navigating to new pages, and extracting information from the page.

## How It Works

### PageManager Class

The `PageManager` class is responsible for managing the Playwright browser and page interactions. It provides methods to perform common actions on web pages:

- `goto(url)`: Navigates to the specified URL.
- `click(selector)`: Clicks on an element identified by the CSS selector.
- `type(selector, text)`: Types the specified text into an input element identified by the CSS selector.
- `get_value(selector)`: Retrieves the value of an input element identified by the CSS selector.
- `get_text(selector)`: Retrieves the inner text of an element identified by the CSS selector.
- `get_title()`: Retrieves the title of the current page.
- `wait(seconds)`: Waits for the specified number of seconds.
- `get_content()`: Retrieves the HTML content of the current page.
- `close()`: Closes the browser and stops Playwright.

### web_agent Function

The `web_agent` function interacts with a web page to complete a specified task. It uses the `PageManager` class to perform actions on the page and an LLM to generate the next action based on the current state of the page and the task.

1. **Initialization**: The function initializes the `PageManager` and navigates to the initial URL if provided.
2. **Generate Next Action**: The function generates the next action by prompting the LLM with the current state of the page and the task. The LLM returns a single action in plain text.
3. **Execute Action**: The function executes the generated action using the `PageManager` and updates the current state with the result.
4. **Repeat**: The function repeats the process of generating and executing actions until the task is completed.

### web_agent_conversation Function

The `web_agent_conversation` function is similar to `web_agent` but uses the LLM's conversation mode to maintain context across multiple interactions. It follows these steps:

1. **Initialization**: The function initializes the `PageManager` and navigates to the initial URL if provided.
2. **Initial Prompt**: The function sends an initial prompt to the LLM to start the conversation.
3. **Generate and Execute Actions**: The function generates and executes actions in a loop, updating the conversation with the results of each action.
4. **Verify Task Completion**: The function verifies if the task is completed by checking the HTML content. If the task is completed, it ends the conversation.
5. **Print Responses**: The function prints all responses from the conversation and explains how the task was completed.

### Example Usage

```python
task = "Search for 'LLM agents' and return the first result's title."
web_agent_conversation("gemini-2.0-flash", task, "https://duckduckgo.com/")
```

In this example, the `web_agent_conversation` function is used to search for "LLM agents" on DuckDuckGo and return the title of the first result. The function initializes the `PageManager`, starts a conversation with the LLM, and performs actions to complete the task.