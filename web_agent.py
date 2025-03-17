import time
import re
import datetime
import sys

from tool_provider import ToolProvider
from tool_agent import ToolAgent
from playwright.sync_api import sync_playwright

class PageManagerToolProvider(ToolProvider):
    """Tool provider that exposes web browser automation capabilities"""
    
    def __init__(self, headless=False):
        """Initialize the page manager with a browser instance"""
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

        self.page_content_maybe_dirty = True

        # Initialize the parent ToolProvider
        super().__init__()

    
    def _initialize_data(self):
        """Initialize the page manager with a browser instance"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
    
    def get_tools(self):
        """Return web automation tools"""
        return {
            'navigate': {
                'method': self.navigate,
                'description': 'Navigate to a URL. Parameter should be a string containing the URL. Example: { "type": "call_tool", "tool": "navigate", "param": "https://www.example.com" }',
                'response': 'Returns navigation result. Example: {"status": "success"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'URL to navigate to'
                }
            },
            'click': {
                'method': self.click,
                'description': 'Click on an element, like a "button" or "a" link. Parameter should be a string containing a CSS selector. Example: { "type": "call_tool", "tool": "click", "param": "#submit-button" }',
                'response': 'Returns click result. Example: {"status": "success"} or {"status": "error", "message": "Element not found"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'CSS selector for the element to click'
                }
            },
            'type_text': {
                'method': self.type_text,
                'description': 'Type text into an "input" or "textarea" field. Parameter should be an object with "selector" and "text" fields. Example: { "type": "call_tool", "tool": "type_text", "param": {"selector": "#search-input", "text": "search query"} }',
                'response': 'Returns typing result. Example: {"status": "success"} or {"status": "error", "message": "Element not found"}',
                'param_info': {
                    'required': True,
                    'type': 'object',
                    'description': 'Object containing selector and text to type',
                    'schema': {
                        'selector': 'CSS selector for the "input" or "textarea" element',
                        'text': 'Text to type into the element'
                    }
                }
            },
            'get_text': {
                'method': self.get_text,
                'description': 'Get inner text content from an element. Parameter should be a string containing a CSS selector. Example: { "type": "call_tool", "tool": "get_text", "param": ".article-title" }',
                'response': 'Returns the text content. Example: {"text": "Example Title"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'CSS selector for the element'
                }
            },
            'get_title': {
                'method': self.get_title,
                'description': 'Get the title of the current page. No parameter needed. Example: { "type": "call_tool", "tool": "get_title" }',
                'response': 'Returns the page title. Example: {"title": "Example Page"}',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'get_current_url': {
                'method': self.get_current_url,
                'description': 'Get the current URL of the page. No parameter needed. Example: { "type": "call_tool", "tool": "get_current_url" }',
                'response': 'Returns the current URL. Example: {"url": "https://www.example.com"}',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'wait_for_navigation': {
                'method': self.wait_for_navigation,
                'description': 'Wait for page navigation to complete. No parameter needed. Example: { "type": "call_tool", "tool": "wait_for_navigation" }',
                'response': 'Returns status after waiting. Example: {"status": "success"}',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'wait_seconds': {
                'method': self.wait_seconds,
                'description': 'Wait for a specified number of seconds. Parameter should be a number. Example: { "type": "call_tool", "tool": "wait_seconds", "param": 2 }',
                'response': 'Returns status after waiting. Example: {"status": "success"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Number of seconds to wait (integer)'
                }
            },
            'get_page_content': {
                'method': self.get_page_content,
                'description': 'Get the HTML content of the current page. No parameter needed. Example: { "type": "call_tool", "tool": "get_page_content" }',
                'response': 'Returns the HTML content. Example: {"content": "raw content of the page"}',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            }
        }
    
    def _get_locator_count(self, selector, expected_count=1):
        """Check if a selector returns the expected number of elements"""
        count = self.page.locator(selector).count()
        if count == 0:
            return False, 'Element not found'
        elif count > expected_count and expected_count == 1:
            return False, 'Multiple elements found. Please use a more specific selector.'
        return True, count
    
    def navigate(self, url):
        """Navigate to a URL"""
        try:
            self.page.goto(url)
            self.page_content_maybe_dirty = True
            return {"status": "success", "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def click(self, selector):
        """Click on an element"""
        check, result = self._get_locator_count(selector)
        if check:
            try:
                self.page.locator(selector).click()
                self.page_content_maybe_dirty = True
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": result}
    
    def type_text(self, param):
        """Type text into an input field"""
        selector = param.get('selector')
        text = param.get('text')
        
        if not selector or text is None:
            return {"status": "error", "message": "Both 'selector' and 'text' are required"}
        
        check, result = self._get_locator_count(selector)
        if check:
            try:
                self.page.locator(selector).fill(text)
                self.page_content_maybe_dirty = True
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": result}
    
    def get_text(self, selector):
        """Get text content from an element"""
        check, result = self._get_locator_count(selector)
        if check:
            try:
                text = self.page.locator(selector).inner_text()
                return {"text": text}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": result}
    
    def get_title(self):
        """Get the title of the current page"""
        try:
            title = self.page.title()
            return {"title": title}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_current_url(self):
        """Get the current URL of the page"""
        try:
            url = self.page.url
            return {"url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def wait_for_navigation(self):
        """Wait for page navigation to complete"""
        try:
            self.page.wait_for_load_state("networkidle")
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def wait_seconds(self, seconds):
        """Wait for a specified number of seconds"""
        try:
            # Convert to float in case it's passed as string
            seconds_float = float(seconds)
            time.sleep(seconds_float)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_page_content(self):
        """Get a simplified version of the page content with only essential interactive elements"""
        if not self.page_content_maybe_dirty:
            return {"status": "error", "message": "Use previously extracted page content"}
        
        try:
            # List of elements we want to extract
            selectors = [
                # Core interactive elements
                "button", "input", "a", "textarea", "select", "option",
                
                # Semantic elements 
                "[id]:not(script):not(style)", "[role]", "[aria-label]",
                
                # Common UI elements
                "h1", "h2", "h3", "label",
                ".btn", ".button", "[type='submit']", "[type='checkbox']", "[type='radio']"
            ]
            
            # Build a selector that combines all our target elements
            combined_selector = ", ".join(selectors)
            
            # Get all matching elements
            elements = self.page.query_selector_all(combined_selector)
            
            # Create a set to track elements we've already processed
            processed_elements = set()
            essential_elements = []
            
            # Process each element and extract relevant data via JavaScript
            for element in elements:
                try:
                    # Get all element data in a single call to page.evaluate
                    element_data = self.page.evaluate("""(el) => {
                        // Function to generate a unique selector
                        function getUniqueSelector(element) {
                            if (element.id) {
                                return `#${element.id}`;
                            }
                            if (element.tagName === 'HTML') {
                                return 'html';
                            }
                            if (element.tagName === 'BODY') {
                                return 'body';
                            }
                            
                            const parent = element.parentNode;
                            if (!parent) {
                                return element.tagName.toLowerCase();
                            }

                            const index = Array.from(parent.children).indexOf(element) + 1;
                            const baseSelector = `${element.tagName.toLowerCase()}:nth-child(${index})`;
                            const parentSelector = getUniqueSelector(parent);

                            return `${parentSelector} > ${baseSelector}`;
                        }
                        
                        // Get element attributes
                        const importantAttrs = ['id', 'class', 'type', 'name', 'role', 'aria-label', 'data-testid', 'placeholder', 'href', 'value'];
                        const filteredAttrs = {};
                        for (const attr of el.attributes) {
                            if (importantAttrs.includes(attr.name)) {
                                filteredAttrs[attr.name] = attr.value;
                            }
                        }
                        
                        // Get and truncate text content
                        let textContent = el.textContent ? el.textContent.trim() : '';
                        if (textContent.length > 100) {
                            textContent = textContent.substring(0, 100) + '...';
                        }
                        
                        const style = window.getComputedStyle(el);
                        const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                        // Return all element data at once
                        return {
                            uniqueSelector: getUniqueSelector(el),
                            tagName: el.tagName.toLowerCase(),
                            attributes: filteredAttrs,
                            textContent: textContent,
                            isVisible: isVisible,
                            isSelfClosing: ['input', 'img', 'br', 'hr', 'meta', 'link'].includes(el.tagName.toLowerCase())
                        };
                    }""", element)
                    
                    # Skip if we've already processed an element with this selector
                    if element_data['uniqueSelector'] in processed_elements:
                        continue
                    
                    if not element_data['isVisible']:
                        continue

                    processed_elements.add(element_data['uniqueSelector'])
                    
                    # Format the element attributes
                    attr_str = " ".join([f'{k}="{v}"' for k, v in element_data['attributes'].items()])
                    
                    # Format element HTML based on type
                    if element_data['isSelfClosing']:
                        element_html = f"<{element_data['tagName']} {attr_str} />"
                    elif element_data['textContent']:
                        element_html = f"<{element_data['tagName']} {attr_str}>{element_data['textContent']}</{element_data['tagName']}>"
                    else:
                        element_html = f"<{element_data['tagName']} {attr_str}></{element_data['tagName']}>"
                    
                    essential_elements.append(element_html)
                    
                except Exception as e:
                    # Skip elements that cause errors
                    print(f"Error processing element: {str(e)}")
                    continue
            
            # Mark page content as processed
            self.page_content_maybe_dirty = False
            
            # Join the extracted elements
            extracted_content = "\n".join(essential_elements)
            
            # Save extracted content to a debug file
            # debug_file_path = "web_agent_extracted_content.html"
            # with open(debug_file_path, "w", encoding="utf-8") as debug_file:
            #     debug_file.write(extracted_content)
            
            # Truncate if needed to avoid large inputs to the model
            truncated_content = extracted_content[:50000] + ("..." if len(extracted_content) > 50000 else "")
            return {"content": truncated_content}
            
        except Exception as e:
            return {"status": "error", "message": f"Error extracting page content: {str(e)}"}
            
    def close(self):
        """Close the browser and playwright instance"""
        try:
            self.browser.close()
            self.playwright.stop()
            return {"status": "success", "message": "Browser closed successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class WebAgent(ToolAgent):
    """Agent that uses ToolAgent architecture to control a web browser and complete tasks"""
    
    # Web-specific system prompt additions
    EXTRA_WEB_PROMPT_TEMPLATE = """
    You are a web agent that can control a web browser to complete tasks. Your goal is to follow the user's instructions precisely.

    BROWSER GUIDELINES:
    1. Use VALID CSS selectors to identify elements on the page.
    - ID selectors use a '#' before the ID name. For example, '#my-id'.
    - Class selectors use a '.' before the class name. For example, '.my-class'.
    - Attribute selectors use '[]' with the attribute name and value. For example, '[name="my-name"]'.
    2. Wait for navigation to complete when necessary.
    3. Get the updated page content after navigation or interaction.
    4. USE semantic ID, ROLE, and ARIA-LABEL attributes to identify elements in CSS selectors.

    STRATEGY:
    1. Think step-by-step about how a human would accomplish this task
    2. Explore the page to understand its structure
    3. Perform actions in a logical sequence 
    4. Verify results after important steps
    5. Extract the information requested in the task

    When you complete the task, do the following:
    - Provide a clear summary of what you found and the steps you took.
    - Indicate the completion of the task by outputting 'task complete'
    """
    
    def __init__(self, model_name="gemini-2.0-flash", headless=False):
        """Initialize the web agent"""
        # Initialize the parent ToolAgent
        super().__init__(model_name=model_name)
        
        # Create and register the PageManagerToolProvider
        self.web_provider = PageManagerToolProvider(headless=headless)
        self.register_provider(self.web_provider)
    
    def run_task(self, task, verbose=True):
        """Run a web task using the agent"""
        if verbose:
            print(f"Starting task: {task}")
        
        # Create a conversation with web-specific instructions
        conversation = self.create_conversation(extra_prompt=self.EXTRA_WEB_PROMPT_TEMPLATE)
        
        # Process the task message
        task_message = f"""TASK: {task}
        
        First, analyze the current page to understand what you're working with.
        Complete the task step by step, using the tools provided.
        When you've completed the task, clearly state "task complete" and summarize what you found.
        """
        
        # This single call will handle the entire conversation
        result = self.process_message(conversation, task_message)
        
        # Check if the task was completed
        completion_status = "complete" if "task complete" in result.get('text', '').lower() else "incomplete"
        
        if verbose and completion_status == "complete":
            print("\nTask completed!")
        
        # Prepare final result
        final_result = {
            "task": task,
            "status": completion_status,
            "final_response": result.get('text', ''),
            "token_usage": self.get_token_usage(),
            "log": result.get('log', [])
        }
        
        return final_result

    def close(self):
        """Close the browser and clean up resources"""
        self.web_provider.close()


def main():
    """Main function to run the web agent"""
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        task = "Use 'https://duckduckgo.com', search for 'python tutorial', and return the title of the first result found"
    
    agent = WebAgent()
    
    try:
        start_time = datetime.datetime.now()
        
        result = agent.run_task(task)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result["duration_seconds"] = duration
        
        print("\n===== TASK SUMMARY =====")
        print(f"Task: {result['task']}")
        print(f"Status: {result['status']}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Input tokens: {result['token_usage'].get('input', 0)}")
        print(f"Output tokens: {result['token_usage'].get('output', 0)}")
        print("\n===== FINAL RESPONSE =====")
        print(result.get('final_response', ''))
        
    finally:
        agent.close()


if __name__ == "__main__":
    main()
