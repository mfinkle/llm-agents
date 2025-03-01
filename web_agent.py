from playwright.sync_api import sync_playwright
import llm
import time
import json
import re

# Class to manage a web page and interact with it
class PageManager:
    def __init__(self, headless=False):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def _get_locator_count(self, selector, expected_count=1):
        count = self.page.locator(selector).count()
        if count != expected_count:
            if count == 0:
                return False, 'FAILED: Element not found. Is this a valid CSS selector?'
            elif count > expected_count and expected_count == 1:
                return False, 'FAILED: Multiple elements found. Please use a better CSS selector.'
        return True, ''

    def goto(self, url):
        self.page.goto(url)

    def click(self, selector):
        check, err = self._get_locator_count(selector)
        if check:
            self.page.locator(selector).click()
            return {"action": "click", "result": None}
        else:
            return {"action": "click", "result": err}

    def type(self, selector, text):
        check, err = self._get_locator_count(selector)
        if check:
            self.page.locator(selector.strip()).fill(text.strip())
            return {"action": "type", "result": None}
        else:
            return {"action": "type", "result": err}

    def get_value(self, selector):
        check, err = self._get_locator_count(selector)
        if check:
            value = self.page.locator(selector).input_value()
            return {"action": "get value", "result": value}
        else:
            return {"action": "get value", "result": err}

    def get_text(self, selector):
        check, err = self._get_locator_count(selector)
        if check:
            text = self.page.locator(selector).inner_text()
            return {"action": "get text", "result": text}
        else:
            return {"action": "get text", "result": err}

    def get_title(self):
        title = self.page.title()
        return {"action": "get title", "result": title}

    def wait(self, seconds):
        time.sleep(seconds)
        return {"action": "wait", "result": None}

    def get_content(self):
        return self.page.content()

    def close(self):
        self.browser.close()
        self.playwright.stop()

    def execute_action(self, action):
        try:
            if action['action'] == "click":
                target = action['selector']
                return self.click(target)
            elif action['action'] == "type":
                target = action['selector']
                text = action['value']
                return self.type(target, text)
            elif action['action'] == "navigate":
                url = action['value']
                self.goto(url)
                return {"action": "navigate", "result": None}
            elif action['action'] == "get value":
                target = action['selector']
                return self.get_value(target)
            elif action['action'] == "get text":
                target = action['selector']
                return self.get_text(target)
            elif action['action'] == "get title":
                return self.get_title()
            elif action['action'] == "wait":
                seconds = int(action['value'])
                return self.wait(seconds)
            elif action['action'] == "done":
                return {"action": "done", "result": action['result'], "status": action['status']}
            else:
                return {"action": "unknown", "result": "Unknown action."}
        except Exception as e:
            return {"action": "error", "result": f"Action failed: {e}"}


def extract_action_from_response(response):
    action_raw = response.text().strip()

    # Remove fenced code block if it exists. Models don't obey the prompt format.
    action_raw = re.sub(r'^```json|```$', '', action_raw, flags=re.MULTILINE).strip()
    return json.loads(action_raw)


# Function to interact with a web page to complete a task
def web_agent(model, task, initial_url=None):
    page_manager = PageManager(headless=False)
    current_state = {}

    if initial_url:
        page_manager.goto(initial_url)

    def generate_next_action(current_state, task):
        prompt = f"""
            You are using a web browser to complete a task. You MUST ONLY use the provided HTML content of the current page.
            In order to complete your task, you need to specify actions to take. You can click on buttons and links, type text into inputs, and navigate to new pages.

            You MUST return a SINGLE action that should be done next. Use simple PLAIN TEXT.
            Here are the allowable actions:
            "click <valid CSS selector>", used for clicking on an element like a button or link element
            "type <valid CSS selector> with <text>", used to enter text into an input or textarea element
            "navigate to <url>", used to navigate to a new page
            "get value <valid CSS selector>", used to get the value of an input, textarea, or select element
            "get text <valid CSS selector>", used to get the inner text of an element
            "get title", used to get the title of the HTML document
            "wait <seconds>", used to wait for a certain amount of time
            "done <status> <result>", used to indicate that the task is completed. 'status' should be 'success' or 'failed'. 'result' should contain the requested information of the task.

            Actions MUST be returned in lowercase and in PLAIN TEXT. do not use JSON or MARKDOWN.
            Don't hallucinate actions. Only perform actions that are necessary to complete the task.
            If you can complete the task by extracting text out of the HTML content, you can do that as well.
            
            Selectors MUST be VALID CSS selector format. Look for semantic ID, ROLE, and ARIA-LABEL attributes to identify elements.
            Use 'ID' selectors or very specific selectors to limit conflicts.
            ID selectors use a '#' before the ID name. For example, '#my-id'.
            Class selectors use a '.' before the class name. For example, '.my-class'.
            Attribute selectors use '[]' with the attribute name and value. For example, '[name="my-name"]'.
            If can't find an element, try a different selector or use a different approach.

            If you completed the task, you MUST respond with 'done' action, the status, and result of the task.
            Don't hallucinate results. Only provide information that you have found on the HTML page. Do not create hypothetical results.
            Make sure you include everything you found out for the ultimate task in the done result parameter. Do not just say you are done, but include the requested information of the task.

            Task: {task}
            Current page HTML content: {current_state['content']}
            Previous action: {current_state['previous_action'] if 'previous_action' in current_state else ['None']}
            Previous result: {current_state['previous_result'] if 'previous_result' in current_state else ['None']}
        """

        response = llm.get_model(model).prompt(prompt)
        return response.text().strip()

    current_state['content'] = page_manager.get_content()
    action = generate_next_action(current_state, task)

    while True:
        current_state['previous_action'] = action
        print(f"Action: {action}")
        result = page_manager.execute_action(action)
        if result['action'] == "done":
            print("Task completed.")
            print(f"Status: {result['status']}")
            print(f"Result: {result['result']}")
            break
        elif result['result'] is not None:
            current_state['previous_result'] = result
            print(f"Result: {result['result']}")
        elif 'previous_result' in current_state:
            # remove previous_result from current_state
            del current_state['previous_result']

        time.sleep(1)
        current_state['content'] = page_manager.get_content()
        action = generate_next_action(current_state, task)

    page_manager.close()


# Function to interact with a web page to complete a task using conversation mode
def web_agent_conversation(model, task, initial_url=None):
    page_manager = PageManager(headless=False)

    if initial_url:
        page_manager.goto(initial_url)

    conversation = llm.get_model(model).conversation() #Creates a new conversation.

    page_content = page_manager.get_content()

    initial_prompt = f"""
        You are using a web browser to complete a task. You MUST ONLY use the provided HTML content of the current page.
        In order to complete your task, you need to specify actions to take. You can click on buttons and links, type text into inputs, and navigate to new pages.

        You MUST return a SINGLE action that should be done. One action will be executed at a time.
        Return the action as a VALID JSON object in the format: {{"action": "type of action", "selector": "valid CSS selector", "value": "value to type"}}.
        "selector" and "value" are optional depending on the action.
        Response format MUST ALWAYS be only the raw JSON, NO string delimiters wrapping it, NO yapping, NO markdown, NO fenced code blocks.
        What you return will be passed to json.loads() directly.

        Here are the allowable actions:
        "click" is used for clicking on an element like a button or link. For example, "{{'action': 'click', 'selector': 'valid CSS selector'}}"
        "type" is used to enter text into an input or textarea element. For example, "{{'action': 'type', 'selector': 'valid CSS selector', 'value': 'text to type'}}"
        "navigate" is used to navigate to a new page. For example, "{{'action': 'navigate', 'value': 'https://www.example.com'}}"
        "get value" is used to get the value of an input, textarea, or select element. For example, "{{'action': 'get value', 'selector': 'valid CSS selector'}}"
        "get text" is used to get the inner text of an element. For example, "{{'action': 'get text', 'selector': 'valid CSS selector'}}"
        "get title" is used to get the title of the HTML document. For example, "{{'action': 'get title'}}"
        "wait" is used to wait for a certain amount of time. For example, "{{'action': 'wait', 'value': 5}}"
        "done" is used to indicate that the task is completed. For example, "{{'action': 'done', 'status': 'success or failure', 'result': 'result of the task'}}"

        Don't hallucinate actions. Only perform actions that are necessary to complete the task.
        If you can complete the task by extracting text out of the HTML content, you can do that as well.
        
        Selectors MUST be VALID CSS selector format. Look for semantic ID, ROLE, and ARIA-LABEL attributes to identify elements.
        Use 'ID' selectors or very specific selectors to limit conflicts.
        ID selectors use a '#' before the ID name. For example, '#my-id'.
        Class selectors use a '.' before the class name. For example, '.my-class'.
        Attribute selectors use '[]' with the attribute name and value. For example, '[name="my-name"]'.
        If can't find an element, try a different selector or use a different approach.

        If you completed the task, you MUST respond with 'done' action, the status, and result of the task.
        Don't hallucinate results. Only provide information that you have found on the HTML page. Do not create hypothetical results.
        Make sure you include everything you found out for the ultimate task in the done result parameter. Do not just say you are done, but include the requested information of the task.

        Task: {task}
        Current HTML content: {page_content}
    """

    verify_prompt = """
        Verify that the task result exists in the HTML content.
        If the result does not exist in the HTML, keep the task going and return the next action.
        If the result is found, repeat the done action again.
    """

    response = conversation.prompt(initial_prompt)
    action = extract_action_from_response(response)

    while True:
        print(f"Action: {json.dumps(action)}")
        result = page_manager.execute_action(action)

        if result['action'] == "done":
            response = conversation.prompt(verify_prompt)
            verify_action = extract_action_from_response(response)
            if verify_action['action'] == "done":
                print("Task completed.")
                print(f"Status: {result['status']}")
                print(f"Result: {result['result']}")
                break
            else:
                action = verify_action

         # Store the result in the conversation
        conversation.prompt(f"The result of the last action was: {result['result']}")
        print(f"Result: {result['result']}")

        time.sleep(1)

        page_content = page_manager.get_content()
        response = conversation.prompt(f"Current HTML content: {page_content}. What single action should I do next?")
        action = extract_action_from_response(response)
    
    responses = conversation.responses #Get all responses from the conversation.
    for response in responses:
        print(response)
    print()
    response = conversation.prompt('Explain how you completed the task')
    print(response.text().strip())

    page_manager.close()

# Example usage:
task = "Search for 'LLM agents' and return the first result's title."
# web_agent("gemini-2.0-flash", task, "https://duckduckgo.com/")
web_agent_conversation("gemini-2.0-flash", task, "https://duckduckgo.com/")
