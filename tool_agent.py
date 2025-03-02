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

def get_specialties():
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

def book_appointment(booking_data):
    """Books the given appointment."""
    for appointment in appointments_data:
        if appointment['open']:
            # Check if we're matching by ID or by date+time
            if ('id' in booking_data and appointment['id'] == booking_data['id']):
                appointment['open'] = False
                return { 'status': 'success', 'message': 'Appointment booked successfully.' }

            if ('date' in booking_data and 'time' in booking_data and appointment['date'] == booking_data['date'] and appointment['time'] == booking_data['time']):
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
    'get_specialties': {
        'method': get_specialties,
        'description': 'Gets the list of available specialties for scheduling appointments. Example: { "type": "call_function", "tool": "get_specialties" }',
        'response': 'Returns a list of specialties. Example: ["dentist", "vision"]'
    },
    'get_available_appointments': {
        'method': get_available_appointments,
        'description': 'Gets the available appointments for the given specialty. Example: { "type": "call_function", "tool": "get_available_appointments", "param": "dentist" }',
        'response': 'Returns a list of available appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM"}]'
    },
    'book_appointment': {
        'method': book_appointment,
        'description': 'Books the given appointment. Example: { "type": "call_function", "tool": "book_appointment", "param": {"date": "2022-01-01", "time": "10:00 AM"} }',
        'response': 'Returns the status of the booking. Example: {"status": "success", "message": "Appointment booked successfully."}'
    },
    'get_my_appointments': {
        'method': get_my_appointments,
        'description': 'Gets the appointments booked by the user. Example: { "type": "call_function", "tool": "get_my_appointments" }',
        'response': 'Returns a list of booked appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM", "specialty": "dentist"}]'
    },
    'cancel_appointment': {
        'method': cancel_appointment,
        'description': 'Cancels the appointment with the given ID. Example: { "type": "call_function", "tool": "cancel_appointment", "param": "1" }',
        'response': 'Returns the status of the cancellation. Example: {"status": "success", "message": "Appointment canceled successfully."}'
    }
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