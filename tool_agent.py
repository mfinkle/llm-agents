import datetime
import json
import re
import llm

# TODO: Add a human feedback mechanism (thumbs up/down) to improve the model
# TODO: Save positive & negative feedback to a file for future training
# TODO: Improve the get_relevant_program_topics_from_input system prompt and pass in more context

# Define the tool functions available to the agent

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
        result = eval(expression, {'__builtins__': {}}, {})
        return { 'result': result, 'status': 'success' }
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        return { 'result': None, 'status': 'fail' }

today = datetime.datetime.now()
tomorrow = today + datetime.timedelta(days=1)
next_week = today + datetime.timedelta(days=7)
appointments_data = [
    {'id': '1', 'date': today.strftime('%Y-%m-%d'), 'time': '10:00 AM', 'specialty': 'dentist', 'open': True},
    {'id': '2', 'date': today.strftime('%Y-%m-%d'), 'time': '11:00 AM', 'specialty': 'dentist', 'open': True},
    {'id': '3', 'date': tomorrow.strftime('%Y-%m-%d'), 'time': '11:00 AM', 'specialty': 'dentist', 'open': True},
    {'id': '4', 'date': tomorrow.strftime('%Y-%m-%d'), 'time': '3:00 PM', 'specialty': 'dentist', 'open': True},
    {'id': '5', 'date': next_week.strftime('%Y-%m-%d'), 'time': '1:00 PM', 'specialty': 'dentist', 'open': True},
    {'id': '6', 'date': next_week.strftime('%Y-%m-%d'), 'time': '2:00 PM', 'specialty': 'dentist', 'open': True},
    {'id': '7', 'date': tomorrow.strftime('%Y-%m-%d'), 'time': '2:00 PM', 'specialty': 'vision', 'open': True},
    {'id': '8', 'date': next_week.strftime('%Y-%m-%d'), 'time': '2:00 PM', 'specialty': 'vision', 'open': True},
    {'id': '9', 'date': next_week.strftime('%Y-%m-%d'), 'time': '4:00 PM', 'specialty': 'vision', 'open': True},
    {'id': '10', 'date': today.strftime('%Y-%m-%d'), 'time': '10:30 AM', 'specialty': 'hair', 'open': True},
    {'id': '11', 'date': tomorrow.strftime('%Y-%m-%d'), 'time': '2:00 PM', 'specialty': 'hair', 'open': True},
    {'id': '12', 'date': next_week.strftime('%Y-%m-%d'), 'time': '11:00 AM', 'specialty': 'hair', 'open': True},
    {'id': '13', 'date': next_week.strftime('%Y-%m-%d'), 'time': '3:00 PM', 'specialty': 'hair', 'open': True},
]

def get_appointment_specialties():
    """Gets the list of available specialties."""
    specialties = list(set([appointment['specialty'] for appointment in appointments_data]))
    return specialties

def get_available_appointments(specialty):
    """Gets the available appointments for the given specialty."""
    open_appointments = [
        { 'id': appointment['id'], 'date': appointment['date'], 'time': appointment['time'] }
        for appointment in appointments_data
        if appointment['specialty'] == specialty and appointment['open']
    ]
    return open_appointments

def book_appointment(appointment_id):
    """Books the given appointment."""
    for appointment in appointments_data:
        if appointment['open'] and appointment['id'] == appointment_id:
            appointment['open'] = False
            return { 'status': 'success', 'message': 'Appointment booked successfully.' }
    return { 'status': 'fail', 'message': 'Appointment not available.' }

def get_my_appointments():
    """Gets the appointments booked by the user."""
    my_appointments = [
        { 'id': appointment['id'], 'date': appointment['date'], 'time': appointment['time'], 'specialty': appointment['specialty'] }
        for appointment in appointments_data
        if not appointment['open']
    ]
    return my_appointments

def cancel_appointment(appointment_id):
    """Cancels the appointment with the given ID."""
    for appointment in appointments_data:
        if not appointment['open'] and appointment['id'] == appointment_id:
            appointment['open'] = True
            return { 'status': 'success', 'message': 'Appointment canceled successfully.' }
    return { 'status': 'fail', 'message': 'Appointment not found.' }


# Create a registry of tool functions available to the agent
api_functions = {
    'get_weather': {
        'method': get_weather,
        'description': 'Gets the weather for the given zipcode. Example: { "type": "call_tool", "tool": "get_weather", "param": "90210" }',
        'response': 'Returns the temperature and conditions. Example: {"temperature": "75 F", "conditions": "Sunny"}'
    },
    'get_zipcode': {
        'method': get_zipcode,
        'description': 'Gets the zipcode for the given city. Example: { "type": "call_tool", "tool": "get_zipcode", "param": "Beverly Hills" }',
        'response': 'Returns the zipcode. Example: {"zipcode": "90210"}'
    },
    'calculate': {
        'method': calculate,
        'description': 'Calculates the given mathematical expression. Example: { "type": "call_tool", "tool": "calculate", "param": "2 + 2" }',
        'response': 'Returns the result of the calculation. Example: {"result": 4, "status": "success"}'
    },
    'get_datetime': {
        'method': get_datetime,
        'description': 'Gets the current date and time. Example: { "type": "call_tool", "tool": "get_datetime" }',
        'response': 'Returns the current date and time. Example: {"date": "2022-01-01", "time": "12:00 PM"}'
    },
    'get_appointment_specialties': {
        'method': get_appointment_specialties,
        'description': 'Gets the list of available specialties for scheduling appointments. Example: { "type": "call_tool", "tool": "get_appointment_specialties" }',
        'response': 'Returns a list of specialties. Example: ["dentist", "vision"]'
    },
    'get_available_appointments': {
        'method': get_available_appointments,
        'description': 'Gets the available appointments for the given specialty. Example: { "type": "call_tool", "tool": "get_available_appointments", "param": "dentist" }',
        'response': 'Returns a list of available appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM"}]'
    },
    'book_appointment': {
        'method': book_appointment,
        'description': 'Books the given appointment with the given ID. Example: { "type": "call_tool", "tool": "book_appointment", "param": "1" }',
        'response': 'Returns the status of the booking. Example: {"status": "success", "message": "Appointment booked successfully."}'
    },
    'get_my_appointments': {
        'method': get_my_appointments,
        'description': 'Gets the appointments booked by the user. Example: { "type": "call_tool", "tool": "get_my_appointments" }',
        'response': 'Returns a list of booked appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM", "specialty": "dentist"}]'
    },
    'cancel_appointment': {
        'method': cancel_appointment,
        'description': 'Cancels the appointment with the given ID. Example: { "type": "call_tool", "tool": "cancel_appointment", "param": "1" }',
        'response': 'Returns the status of the cancellation. Example: {"status": "success", "message": "Appointment canceled successfully."}'
    }
}


# Extract the action from the response as JSON
def extract_action_from_response(response):
    action_raw = response.text().strip()
    print(f"Action raw: {action_raw}")

    try:
        # Remove fenced code block if it exists. Models don't always obey the prompt format.
        action_raw = re.sub(r'^```json|```$', '', action_raw, flags=re.MULTILINE).strip()
        
        # Try to parse the JSON
        action = json.loads(action_raw)
        return action, True
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return None, False


# Validate the LLM response so we can give it corrective feedback
def validate_action(action):
    if not isinstance(action, dict):
        return False, 'Response must be a JSON object'
    
    if 'type' not in action:
        return False, 'Response must have a "type" field'
    
    if action['type'] not in ['output', 'call_tool']:
        return False, 'Type field must be "output" or "call_tool"'
    
    # Thought is optional but recommended
    
    if action['type'] == 'call_tool':
        if 'tool' not in action:
            return False, 'Tool call must have a "tool" field'
    
    if action['type'] == 'output':
        if 'value' not in action:
            return False, 'Output must have a "value" field'
    
    return True, ''


# Process and validate a model response, with multiple attempts if needed
def validate_model_response(conversation, response, max_attempts=3):
    attempts = 0
    
    while attempts < max_attempts:
        extracted_action, json_success = extract_action_from_response(response)
        
        # If JSON parsing failed
        if not json_success:
            attempts += 1
            if attempts >= max_attempts:
                # Return fallback action
                return {'type': 'output', 'value': 'I apologize, but I\'m having trouble understanding. Could you rephrase your request?'}, False
            
            # Ask for correctly formatted JSON
            correction_prompt = "Your response was not valid JSON. Please provide a valid JSON response with the required structure."
            response = conversation.prompt(correction_prompt)
            continue
        
        # JSON parsed successfully, now validate the structure
        valid, error_message = validate_action(extracted_action)
        if valid:
            return extracted_action, True
        else:
            attempts += 1
            if attempts >= max_attempts:
                # Return fallback action
                return {'type': 'output', 'value': 'I apologize, but I\'m having trouble processing your request.'}, False
            
            # Ask for correctly structured response
            correction_prompt = f"Your response format was invalid: {error_message}. Please provide a valid JSON response with the correct structure."
            response = conversation.prompt(correction_prompt)
    
    # This should never be reached but just in case
    return {'type': 'output', 'value': 'Something went wrong with my processing.'}, False


# Start the chat with the agent
def start_chat(model):
    tool_registry = '\n'.join([f"<tool><name>{name}</name><description>{details['description']}</description><response>{details['response']}</response></tool>" for name, details in api_functions.items()])
    tool_registry_xml = f"<tools>{tool_registry}</tools>"
    
    print(f"Tool registry: {tool_registry_xml}")

    initial_prompt = f"""
        You are a helpful assistant that can answer various tasks.
        User inputs will be passed as plain text.
        
        
        All responses MUST use JSON format with this structure:
        {{
          "thought": "Your step-by-step reasoning here, analyzing the problem and determining what to do...",
          "type": "output or call_tool",
          ... other fields depending on type
        }}
        
        For tool calls, use:
        {{
          "thought": "Your reasoning for choosing this tool...",
          "type": "call_tool",
          "tool": "tool_name",
          "param": "tool_parameters"
        }}
        
        For direct responses to the user, use:
        {{
          "thought": "Your reasoning for this response...",
          "type": "output",
          "value": "text of your response"
        }}
        
        Here are the tools you can call:
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

            # Get initial response
            response = conversation.prompt(user_input)
            
            # Validate the initial response
            action, success = validate_model_response(conversation, response)
            
            try:
                # Display the thought process if present
                if 'thought' in action:
                    print(f"Thought: {action['thought']}")
                
                # Process tool calls
                while action['type'] == 'call_tool':
                    function_name = action.get('tool')
                    param = action.get('param')
                    
                    try:
                        if function_name in api_functions:
                            if param:
                                function_result = api_functions[function_name]['method'](param)
                            else:
                                function_result = api_functions[function_name]['method']()
                            
                            function_result_json = json.dumps(function_result)
                            print(f"Tool result: {function_result_json}")
                            response = conversation.prompt(f"Tool result: {function_result_json}")
                        else:
                            print("Unknown tool.")
                            response = conversation.prompt('Unknown tool. Please try a different approach.')
                            
                    except Exception as e:
                        print(f"Error calling tool: {e}")
                        response = conversation.prompt(f"Error calling tool: {e}. Please try a different approach.")

                    # Validate next action after tool call - reuse the validation helper
                    action, success = validate_model_response(conversation, response)
                    
                    # Display updated thought process
                    if 'thought' in action:
                        print(f"Thought: {action['thought']}")
                    
                    # Break out if we switched to output type or validation failed
                    if action['type'] != 'call_tool' or not success:
                        break

                # Handle the final output
                if action['type'] == 'output':
                    print(f"Agent: {action['value']}")
                                            
            except Exception as e:
                print(f"Error in processing: {str(e)}")

    chat_loop()

if __name__ == '__main__':
    start_chat(model='gemini-2.0-flash')