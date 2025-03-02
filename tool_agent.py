import datetime
import json
import re
import llm

# Define the tool functions available to the agent

def search_web(query):
    """Searches the web for the given query."""
    return [
        {'title': 'Result 1', 'url': 'http://www.example.com/result1'},
        {'title': 'Result 2', 'url': 'http://www.example.com/result2'},
        {'title': 'Result 3', 'url': 'http://www.example.com/result3'}
    ]

def get_weather(zipcode):
    """Gets the weather for the given city."""
    return {
        'temperature': '75 F',
        'conditions': 'Sunny'
    }

def get_zipcode(city):
    """Gets the zipcode for the given city."""
    return {
        'zipcode': '90210'
    }

def get_datetime():
    """Gets the current date and time."""
    now = datetime.datetime.now()
    return {
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%I:%M %p')
    }

def calculate(expression):
    """Calculates the given mathematical expression."""
    try:
        result = eval(expression)
        return { 'result': result, 'status': 'success' }
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        return { 'result': None, 'status': 'fail' }


# Create a registry of tool functions available to the agent
api_functions = {
    'search_web': {
        'method': search_web,
        'description': 'Searches the web for the given query. Example: { "type": "call_function", "tool": "search_web", "param": "python programming" }',
        'response': 'Returns a list of search results with titles and urls. Example: [{"title": "Result 1", "url": "http://www.example.com/result1"}]'
    },
    'get_weather': {
        'method': get_weather,
        'description': 'Gets the weather for the given zipcode. Example: { "type": "call_function", "tool": "get_weather", "param": "90210" }',
        'response': 'Returns the temperature and conditions. Example: {"temperature": "75 F", "conditions": "Sunny"}'
    },
    'get_zipcode': {
        'method': get_zipcode,
        'description': 'Gets the zipcode for the given city. Example: { "type": "call_function", "tool": "get_zipcode", "param": "Beverly Hills" }',
        'response': 'Returns the zipcode. Example: {"zipcode": "90210"}'
    },
    'calculate': {
        'method': calculate,
        'description': 'Calculates the given mathematical expression. Example: { "type": "call_function", "tool": "calculate", "param": "2 + 2" }',
        'response': 'Returns the result of the calculation. Example: {"result": 4, "status": "success"}'
    },
    'get_datetime': {
        'method': get_datetime,
        'description': 'Gets the current date and time. Example: { "type": "call_function", "tool": "get_datetime" }',
        'response': 'Returns the current date and time. Example: {"date": "2022-01-01", "time": "12:00 PM"}'
    },
    },
}


# Extract the action from the response as JSON
def extract_action_from_response(response):
    action_raw = response.text().strip()
    print(f"Action raw: {action_raw}")

    # Remove fenced code block if it exists. Models don't obey the prompt format.
    action_raw = re.sub(r'^```json|```$', '', action_raw, flags=re.MULTILINE).strip()
    return json.loads(action_raw)


# Start the chat with the agent
def start_chat(model):
    tool_registry = '\n'.join([f"<tool><name>{name}</name><description>{details['description']}</description><response>{details['response']}</response></tool>" for name, details in api_functions.items()])
    tool_registry_xml = f"<tools>{tool_registry}</tools>"
    
    print(f"Tool registry: {tool_registry_xml}")

    initial_prompt = f"""
        You are a helpful assistant that can answer various tasks.
        User inputs will be passed as plain text.
        All responses MUST use JSON format. You can reply with output, for example {{"type": "output", "value": "text of your response"}}.
        Or you can request a function call by replying with {{"type": "call_function", "tool": "function_name", "param": "function_parameters"}}.
        Here are the set to tools you can call:
        {tool_registry_xml}
        """

    conversation = llm.get_model(model).conversation()
    response = conversation.prompt(initial_prompt)
    print(f"Agent Initial: {response.text()}")

    def chat_loop():
        while True:
            user_input = input('You: ')
            if user_input.lower().strip() in ['exit', 'quit', 'bye']:
                print('Goodbye!')
                break

            response = conversation.prompt(user_input)
            action = extract_action_from_response(response)

            # Check for API function calls
            while action['type'] == 'call_function':
                try:
                    # Extract the function call from the response
                    function_name = action.get('tool')
                    param = action.get('param')

                    if function_name in api_functions:
                        if param:
                            function_result = api_functions[function_name]['method'](param)
                        else:
                            function_result = api_functions[function_name]['method']()
                        function_result_json = json.dumps(function_result)
                        response = conversation.prompt(f"Function result: {function_result_json}")
                        print(f"Function result: {function_result_json}")
                    else:
                        response = conversation.prompt('Unknown function.')
                        print('Unknown function.')
                except Exception as e:
                    response = conversation.prompt(f"Error calling function: {e}")
                    print(f"Error calling function: {e}")

                action = extract_action_from_response(response)
            
            if action['type'] == 'output':
                print(f"Agent: {action['value']}")

    chat_loop()

if __name__ == '__main__':
    start_chat(model='gemini-2.0-flash')