import datetime
import json
import re
import llm

from tool_provider import ToolProvider

class UtilityToolProvider(ToolProvider):
    """Provider for basic utility tools"""
    
    def get_tools(self):
        """Return utility tools"""
        return {
            'get_weather': {
                'method': self.get_weather,
                'description': 'Gets the weather for the given zipcode. Parameter should be a string containing the zipcode. Example: { "type": "call_tool", "tool": "get_weather", "param": "90210" }',
                'response': 'Returns the temperature and conditions. Example: {"temperature": "75 F", "conditions": "Sunny"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Zipcode as a string (e.g., "90210")'
                }
            },
            'get_zipcode': {
                'method': self.get_zipcode,
                'description': 'Gets the zipcode for the given location. Parameter should be a string containing the city name and state abbreviation. Example: { "type": "call_tool", "tool": "get_zipcode", "param": "Beverly Hills, CA" }',
                'response': 'Returns the zipcode. Example: {"zipcode": "90210"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Location name as a string (e.g., "Beverly Hills, CA")'
                }
            },
            'calculate': {
                'method': self.calculate,
                'description': 'Calculates the given mathematical expression. Parameter should be a string containing a valid mathematical expression. Example: { "type": "call_tool", "tool": "calculate", "param": "2 + 2" }',
                'response': 'Returns the result of the calculation. Example: {"result": 4, "status": "success"}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Mathematical expression as a string (e.g., "2 + 2")'
                }
            },
            'get_datetime': {
                'method': self.get_datetime,
                'description': 'Gets the current date and time. No parameter is needed for this tool. Example: { "type": "call_tool", "tool": "get_datetime" }',
                'response': 'Returns the current date and time. Example: {"date": "2022-01-01", "time": "12:00 PM"}',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            }
        }
    
    def get_weather(self, zipcode):
        """Gets the weather for the given zipcode."""
        return {
            'temperature': '75 F',
            'conditions': 'Sunny'
        }
    
    def get_zipcode(self, location):
        """Gets the zipcode for the given location."""
        return {
            'zipcode': '90210'
        }
    
    def get_current_location(self):
        """Gets the zipcode for the given city."""
        return {
            'location': 'Springfield, IL'
        }

    def get_datetime(self):
        """Gets the current date and time."""
        now = datetime.datetime.now()
        return {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%I:%M %p')
        }
    
    def calculate(self, expression):
        """Calculates the given mathematical expression."""
        try:
            result = eval(expression, {'__builtins__': {}}, {})
            return { 'result': result, 'status': 'success' }
        except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
            return { 'result': None, 'status': 'fail' }


class AppointmentToolProvider(ToolProvider):
    """Provider for appointment-related tools"""
    
    def _initialize_data(self):
        """Initialize appointment data"""
        # Current date for appointments
        self.today = datetime.datetime.now()
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.next_week = self.today + datetime.timedelta(days=7)
        
        # Common location data - reused to reduce repetition
        locations = {
            'dentist': {
                'address': '123 Main St, Springfield, IL 62701',
                'coordinates': {'lat': 39.781, 'long': -89.650}
            },
            'vision': {
                'address': '456 Oak Ave, Springfield, IL 62702',
                'coordinates': {'lat': 39.776, 'long': -89.645}
            },
            'hair': {
                'address': '789 Elm Blvd, Springfield, IL 62704',
                'coordinates': {'lat': 39.792, 'long': -89.655}
            }
        }
        
        # Appointment data with clearer structure
        self.appointments_data = [
            # Dentist appointments
            {
                'id': '1', 
                'date': self.today.strftime('%Y-%m-%d'), 
                'time': '10:00 AM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            {
                'id': '2', 
                'date': self.today.strftime('%Y-%m-%d'), 
                'time': '11:00 AM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            {
                'id': '3', 
                'date': self.tomorrow.strftime('%Y-%m-%d'), 
                'time': '11:00 AM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            {
                'id': '4', 
                'date': self.tomorrow.strftime('%Y-%m-%d'), 
                'time': '3:00 PM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            {
                'id': '5', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '1:00 PM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            {
                'id': '6', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '2:00 PM', 
                'specialty': 'dentist', 
                'open': True,
                'address': locations['dentist']['address'],
                'coordinates': locations['dentist']['coordinates']
            },
            
            # Vision appointments
            {
                'id': '7', 
                'date': self.tomorrow.strftime('%Y-%m-%d'), 
                'time': '2:00 PM', 
                'specialty': 'vision', 
                'open': True,
                'address': locations['vision']['address'],
                'coordinates': locations['vision']['coordinates']
            },
            {
                'id': '8', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '2:00 PM', 
                'specialty': 'vision', 
                'open': True,
                'address': locations['vision']['address'],
                'coordinates': locations['vision']['coordinates']
            },
            {
                'id': '9', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '4:00 PM', 
                'specialty': 'vision', 
                'open': True,
                'address': locations['vision']['address'],
                'coordinates': locations['vision']['coordinates']
            },
            
            # Hair appointments
            {
                'id': '10', 
                'date': self.today.strftime('%Y-%m-%d'), 
                'time': '10:30 AM', 
                'specialty': 'hair', 
                'open': True,
                'address': locations['hair']['address'],
                'coordinates': locations['hair']['coordinates']
            },
            {
                'id': '11', 
                'date': self.tomorrow.strftime('%Y-%m-%d'), 
                'time': '11:00 AM', 
                'specialty': 'hair', 
                'open': True,
                'address': locations['hair']['address'],
                'coordinates': locations['hair']['coordinates']
            },
            {
                'id': '12', 
                'date': self.tomorrow.strftime('%Y-%m-%d'), 
                'time': '2:00 PM', 
                'specialty': 'hair', 
                'open': True,
                'address': locations['hair']['address'],
                'coordinates': locations['hair']['coordinates']
            },
            {
                'id': '13', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '11:00 AM', 
                'specialty': 'hair', 
                'open': True,
                'address': locations['hair']['address'],
                'coordinates': locations['hair']['coordinates']
            },
            {
                'id': '14', 
                'date': self.next_week.strftime('%Y-%m-%d'), 
                'time': '3:00 PM', 
                'specialty': 'hair', 
                'open': True,
                'address': locations['hair']['address'],
                'coordinates': locations['hair']['coordinates']
            }
        ]
    
    def get_tools(self):
        """Return appointment-related tools"""
        return {
            'get_appointment_specialties': {
                'method': self.get_appointment_specialties,
                'description': 'Gets the list of available specialties for scheduling appointments. No parameter is needed. Example: { "type": "call_tool", "tool": "get_appointment_specialties" }',
                'response': 'Returns a list of specialties. Example: ["dentist", "vision"]',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'get_available_appointments': {
                'method': self.get_available_appointments,
                'description': 'Gets the available appointments for the given specialty. Parameter should be a string containing the specialty name. Example: { "type": "call_tool", "tool": "get_available_appointments", "param": "dentist" }',
                'response': 'Returns a list of available appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM"}]',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Specialty name as a string (e.g., "dentist")'
                }
            },
            'get_appointment_details': {
                'method': self.get_appointment_details,
                'description': 'Gets the details of the appointment with the given ID. Parameter should be a string containing the appointment ID. Example: { "type": "call_tool", "tool": "get_appointment_details", "param": "1" }',
                'response': 'Returns the details of the appointment. Example: {"id": "1", "date": "2022-01-01", "time": "10:00 AM", "specialty": "dentist", "open": true, "address": "123 Main St, Springfield, IL", "coordinates": {"lat": 39.781, "long": -89.650}}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Appointment ID as a string (e.g., "1")'
                }
            },
            'book_appointment': {
                'method': self.book_appointment,
                'description': 'Books the appointment with the given ID. Parameter should be a string containing the appointment ID. Example: { "type": "call_tool", "tool": "book_appointment", "param": "1" }',
                'response': 'Returns the status of the booking. Example: {"status": "success", "message": "Appointment booked successfully."}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Appointment ID as a string (e.g., "1")'
                }
            },
            'cancel_appointment': {
                'method': self.cancel_appointment,
                'description': 'Cancels the appointment with the given ID. Parameter should be a string containing the appointment ID. Example: { "type": "call_tool", "tool": "cancel_appointment", "param": "1" }',
                'response': 'Returns the status of the cancellation. Example: {"status": "success", "message": "Appointment canceled successfully."}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Appointment ID as a string (e.g., "1")'
                }
            },
            'get_my_appointments': {
                'method': self.get_my_appointments,
                'description': 'Gets the appointments booked by the user. No parameter is needed. Example: { "type": "call_tool", "tool": "get_my_appointments" }',
                'response': 'Returns a list of booked appointments. Example: [{"id": "1", "date": "2022-01-01", "time": "10:00 AM", "specialty": "dentist"}]',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            }
        }

    def get_appointment_specialties(self):
        """Gets the list of available specialties."""
        specialties = list(set([appointment['specialty'] for appointment in self.appointments_data]))
        return specialties

    def get_available_appointments(self, specialty):
        """Gets the available appointments for the given specialty."""
        open_appointments = [
            { 'id': appointment['id'], 'date': appointment['date'], 'time': appointment['time'] }
            for appointment in self.appointments_data
            if appointment['specialty'] == specialty and appointment['open']
        ]
        return open_appointments

    def get_appointment_details(self, appointment_id):
        """Gets the details of the appointment with the given ID."""
        for appointment in self.appointments_data:
            if appointment['id'] == appointment_id:
                return appointment
        return None
    
    def book_appointment(self, appointment_id):
        """Books the given appointment."""
        for appointment in self.appointments_data:
            if appointment['open'] and appointment['id'] == appointment_id:
                appointment['open'] = False
                return { 'status': 'success', 'message': 'Appointment booked successfully.' }
        return { 'status': 'fail', 'message': 'Appointment not available.' }

    def cancel_appointment(self, appointment_id):
        """Cancels the appointment with the given ID."""
        for appointment in self.appointments_data:
            if not appointment['open'] and appointment['id'] == appointment_id:
                appointment['open'] = True
                return { 'status': 'success', 'message': 'Appointment canceled successfully.' }
        return { 'status': 'fail', 'message': 'Appointment not found.' }

    def get_my_appointments(self):
        """Gets the appointments booked by the user."""
        my_appointments = [
            { 'id': appointment['id'], 'date': appointment['date'], 'time': appointment['time'], 'specialty': appointment['specialty'] }
            for appointment in self.appointments_data
            if not appointment['open']
        ]
        return my_appointments


class ProgramToolProvider(ToolProvider):
    """Provider for program-related tools"""
    
    def _initialize_data(self):
        """Initialize program data"""
        # Program library data
        self.program_library = [
            {'id': '1', 'name': 'Python Basics', 'description': 'Learn the fundamentals of Python', 
             'topics': ['python', 'programming', 'beginner'],
             'steps': [
                 {'id': '1', 'name': 'Introduction to Python', 'description': 'Learn about Python and its uses'},
                 {'id': '2', 'name': 'Variables and Data Types', 'description': 'Understand variables and data types in Python'},
                 {'id': '3', 'name': 'Control Structures', 'description': 'Learn about loops and conditional statements'},
                 {'id': '4', 'name': 'Functions and Modules', 'description': 'Understand functions and modules in Python'},
             ]},
            {'id': '2', 'name': 'Web Development with Flask', 'description': 'Build web applications with Flask', 'topics': ['python', 'web', 'flask'],
             'steps': [
                 {'id': '1', 'name': 'Setting Up Flask', 'description': 'Install and configure Flask for web development'},
                 {'id': '2', 'name': 'Creating Routes', 'description': 'Define routes for handling web requests'},
                 {'id': '3', 'name': 'Templates and Forms', 'description': 'Use templates and forms for user interaction'},
                 {'id': '4', 'name': 'Database Integration', 'description': 'Integrate databases with Flask applications'},
             ]},
            {'id': '3', 'name': 'Data Science with Pandas', 'description': 'Analyze data using Pandas', 'topics': ['python', 'data science', 'pandas'],
             'steps': [
                 {'id': '1', 'name': 'Introduction to Pandas', 'description': 'Learn about Pandas and its uses'},
                 {'id': '2', 'name': 'Data Wrangling', 'description': 'Clean and transform data using Pandas'},
                 {'id': '3', 'name': 'Data Analysis', 'description': 'Perform data analysis with Pandas'},
                 {'id': '4', 'name': 'Data Visualization', 'description': 'Visualize data using Pandas and Matplotlib'},
             ]},
            {'id': '4', 'name': 'Machine Learning Fundamentals', 'description': 'Introduction to machine learning concepts', 'topics': ['machine learning', 'data science', 'ai'],
             'steps': [
                 {'id': '1', 'name': 'Introduction to ML', 'description': 'Learn about machine learning and its applications'},
                 {'id': '2', 'name': 'Supervised Learning', 'description': 'Understand supervised learning algorithms'},
                 {'id': '3', 'name': 'Unsupervised Learning', 'description': 'Explore unsupervised learning techniques'},
                 {'id': '4', 'name': 'Model Evaluation', 'description': 'Evaluate machine learning models'},
             ]},
            {'id': '5', 'name': 'JavaScript for Beginners', 'description': 'Learn JavaScript basics', 'topics': ['javascript', 'programming', 'web'],
             'steps': [
                 {'id': '1', 'name': 'Introduction to JavaScript', 'description': 'Learn about JavaScript and its uses'},
                 {'id': '2', 'name': 'Variables and Data Types', 'description': 'Understand variables and data types in JavaScript'},
                 {'id': '3', 'name': 'Functions and Objects', 'description': 'Explore functions and objects in JavaScript'},
                 {'id': '4', 'name': 'DOM Manipulation', 'description': 'Manipulate the Document Object Model with JavaScript'},
             ]},
            {'id': '6', 'name': 'React Development', 'description': 'Build user interfaces with React', 'topics': ['javascript', 'react', 'web'],
             'steps': [
                 {'id': '1', 'name': 'Setting Up React', 'description': 'Install and configure React for web development'},
                 {'id': '2', 'name': 'Components and Props', 'description': 'Create components and pass props in React'},
                 {'id': '3', 'name': 'State and Lifecycle', 'description': 'Manage state and lifecycle methods in React'},
                 {'id': '4', 'name': 'Routing and Hooks', 'description': 'Implement routing and hooks in React applications'},
             ]},
            {'id': '7', 'name': 'Cloud Computing with AWS', 'description': 'Learn AWS services', 'topics': ['cloud', 'aws', 'devops'],
             'steps': [
                 {'id': '1', 'name': 'Introduction to AWS', 'description': 'Learn about AWS and its cloud services'},
                 {'id': '2', 'name': 'EC2 and S3', 'description': 'Deploy virtual servers and store data in the cloud'},
                 {'id': '3', 'name': 'Lambda Functions', 'description': 'Run code without provisioning or managing servers'},
                 {'id': '4', 'name': 'DynamoDB', 'description': 'Build applications with a fully managed NoSQL database'},
             ]},
        ]
        
        # User programs
        self.user_programs = [
            {'id': '1', 'program_id': '1', 'current_step': '2', 'completed_steps': ['1']},
        ]
    
    def get_tools(self):
        """Return program-related tools"""
        return {
            'get_relevant_program_topics_from_input': {
                'method': self.get_relevant_program_topics_from_input,
                'description': 'Extracts topics from the input text. Parameter should be a string containing the user\'s input text. Example: { "type": "call_tool", "tool": "get_relevant_program_topics_from_input", "param": "I want to learn Python programming" }',
                'response': 'Returns a list of topics extracted from the text. Example: ["python", "programming"]',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'User input text as a string'
                }
            },
            'get_program_topics': {
                'method': self.get_program_topics,
                'description': 'Gets the list of available program topics. No parameter is needed. Example: { "type": "call_tool", "tool": "get_program_topics" }',
                'response': 'Returns a list of program topics. Example: ["python", "web", "data science"]',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'get_programs_for_topics': {
                'method': self.get_programs_for_topics,
                'description': 'Gets the programs related to the given topics. Parameter should be an array of topic strings. Example: { "type": "call_tool", "tool": "get_programs_for_topics", "param": ["python", "web"] }',
                'response': 'Returns a list of programs. Example: [{"id": "1", "name": "Python Basics", "description": "Learn the fundamentals of Python", "topics": ["python", "programming", "beginner"]}]',
                'param_info': {
                    'required': True,
                    'type': 'array',
                    'description': 'List of topic strings (e.g., ["python", "web"])',
                    'item_type': 'string'
                }
            },
            'enroll_in_program': {
                'method': self.enroll_in_program,
                'description': 'Enrolls the user in the program with the given ID. Parameter should be a string containing the program ID. Example: { "type": "call_tool", "tool": "enroll_in_program", "param": "1" }',
                'response': 'Returns the status of the enrollment. Example: {"status": "success", "message": "Enrolled in program successfully."}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Program ID as a string (e.g., "1")'
                }
            }
        }

    # TODO: Improve the get_relevant_program_topics_from_input system prompt and pass in more context
    def get_relevant_program_topics_from_input(self, input_text):
        """Uses a separate model and LLM to extract topics from the input text."""
        prompt = f"""
            You are a helpful assistant that can extract relevant topics from text supplied by a user.
            User inputs will be passed as plain text.
            All responses MUST use JSON format. You can reply with a list of applicable topics, for example ["topic 1", "topic 2", "..."].
            Here are the set to topics available:
            {json.dumps(self.get_program_topics())}
            Input text: "{input_text}"
            """
        model = 'gemini-2.0-flash'
        response = llm.get_model(model).prompt(prompt)
        topics = self._extract_action_from_response(response)
        return topics
    
    def _extract_action_from_response(self, response):
        """Helper method to extract topics from LLM response"""
        action_raw = response.text().strip()
        try:
            # Remove fenced code block if it exists
            action_raw = re.sub(r'^```json|```$', '', action_raw, flags=re.MULTILINE).strip()
            
            # Try to parse the JSON
            action = json.loads(action_raw)
            return action
            
        except json.JSONDecodeError:
            return []

    def get_program_topics(self):
        """Gets the list of available program topics."""
        # Extract all topics from all programs
        all_topics = []
        for program in self.program_library:
            all_topics.extend(program['topics'])
        
        # Return unique topics
        return list(set(all_topics))

    def get_programs_for_topics(self, topics):
        """Gets the programs related to the given topics."""
        # Find programs that match any of the requested topics
        matching_programs = []
        for program in self.program_library:
            if any(topic in program['topics'] for topic in topics):
                matching_programs.append({
                    'id': program['id'],
                    'name': program['name'],
                    'description': program['description'],
                    'topics': program['topics']
                })
        return matching_programs

    def enroll_in_program(self, program_id):
        """Enrolls the user in the program with the given ID."""
        for program in self.program_library:
            if program['id'] == program_id:
                self.user_programs.append({
                    'id': str(len(self.user_programs) + 1),
                    'program_id': program_id,
                    'current_step': '1',
                    'completed_steps': []
                })
                return { 'status': 'success', 'message': 'Enrolled in program successfully.' }
        return { 'status': 'fail', 'message': 'Program not found.' }


class StoreLocatorToolProvider(ToolProvider):
    """Provider for store location tools"""
    
    def _initialize_data(self):
        """Initialize store location data"""
        # Store data with name, type, address, and coordinates (lat, long)
        self.stores_data = [
            {
                'id': '1',
                'name': 'Super Foods',
                'type': 'grocery',
                'address': '123 Main St, Springfield, IL',
                'coordinates': {'lat': 39.78, 'long': -89.65},
                'hours': '8:00 AM - 10:00 PM',
                'phone': '555-123-4567',
                'services': ['Deli', 'Bakery', 'Pharmacy']
            },
            {
                'id': '2',
                'name': 'Fresh Market',
                'type': 'grocery',
                'address': '456 Oak Ave, Springfield, IL',
                'coordinates': {'lat': 39.76, 'long': -89.64},
                'hours': '7:00 AM - 9:00 PM',
                'phone': '555-234-5678',
                'services': ['Organic Produce', 'Wine Selection']
            },
            {
                'id': '3',
                'name': 'Luxury Furnishings',
                'type': 'furniture',
                'address': '789 Elm Blvd, Springfield, IL',
                'coordinates': {'lat': 39.79, 'long': -89.68},
                'hours': '10:00 AM - 8:00 PM',
                'phone': '555-345-6789',
                'services': ['Interior Design', 'Delivery']
            },
            {
                'id': '4',
                'name': 'Home Essentials',
                'type': 'furniture',
                'address': '101 Pine St, Springfield, IL',
                'coordinates': {'lat': 39.77, 'long': -89.66},
                'hours': '9:00 AM - 7:00 PM',
                'phone': '555-456-7890',
                'services': ['Assembly', 'Financing']
            },
            {
                'id': '5',
                'name': 'Tech World',
                'type': 'electronics',
                'address': '202 Maple Dr, Springfield, IL',
                'coordinates': {'lat': 39.75, 'long': -89.63},
                'hours': '10:00 AM - 9:00 PM',
                'phone': '555-567-8901',
                'services': ['Repairs', 'Tech Support']
            },
            {
                'id': '6',
                'name': 'Gadget Zone',
                'type': 'electronics',
                'address': '303 Cedar Ln, Springfield, IL',
                'coordinates': {'lat': 39.74, 'long': -89.67},
                'hours': '9:00 AM - 8:00 PM',
                'phone': '555-678-9012',
                'services': ['Trade-ins', 'Custom Orders']
            },
            {
                'id': '7',
                'name': 'Organic Grocers',
                'type': 'grocery',
                'address': '404 Birch Rd, Shelbyville, IL',
                'coordinates': {'lat': 39.81, 'long': -89.70},
                'hours': '8:00 AM - 8:00 PM',
                'phone': '555-789-0123',
                'services': ['Organic Produce', 'Bulk Foods']
            },
            {
                'id': '8',
                'name': 'Modern Home',
                'type': 'furniture',
                'address': '505 Walnut Ave, Shelbyville, IL',
                'coordinates': {'lat': 39.82, 'long': -89.71},
                'hours': '10:00 AM - 7:00 PM',
                'phone': '555-890-1234',
                'services': ['Design Consultation', 'Custom Orders']
            },
            {
                'id': '9',
                'name': 'Electronics Emporium',
                'type': 'electronics',
                'address': '606 Spruce St, Shelbyville, IL',
                'coordinates': {'lat': 39.83, 'long': -89.72},
                'hours': '9:00 AM - 9:00 PM',
                'phone': '555-901-2345',
                'services': ['Extended Warranties', 'Installation']
            },
            {
                'id': '10',
                'name': 'Discount Grocers',
                'type': 'grocery',
                'address': '707 Aspen Blvd, Shelbyville, IL',
                'coordinates': {'lat': 39.84, 'long': -89.73},
                'hours': '7:00 AM - 11:00 PM',
                'phone': '555-012-3456',
                'services': ['Bulk Foods', 'Hot Food Bar']
            }
        ]
    
    def get_tools(self):
        """Return store location tools"""
        return {
            'get_store_types': {
                'method': self.get_store_types,
                'description': 'Gets the list of available store types. No parameter is needed. Example: { "type": "call_tool", "tool": "get_store_types" }',
                'response': 'Returns a list of store types. Example: ["grocery", "furniture", "electronics"]',
                'param_info': {
                    'required': False,
                    'type': None,
                    'description': 'No parameter needed'
                }
            },
            'get_stores_by_type': {
                'method': self.get_stores_by_type,
                'description': 'Gets the stores of a specific type. Parameter should be a string containing the store type. Example: { "type": "call_tool", "tool": "get_stores_by_type", "param": "grocery" }',
                'response': 'Returns a list of stores of the specified type. Example: [{"id": "1", "name": "Super Foods", "address": "123 Main St, Springfield, IL"}]',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Store type as a string (e.g., "grocery", "furniture", "electronics")'
                }
            },
            'get_stores_by_name': {
                'method': self.get_stores_by_name,
                'description': 'Gets the stores of a specific name. Parameter should be a string containing the store name. Example: { "type": "call_tool", "tool": "get_stores_by_name", "param": "Super Foods" }',
                'response': 'Returns a list of stores with the specified name. Example: [{"id": "1", "name": "Super Foods", "address": "123 Main St, Springfield, IL"}]',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Store name as a string'
                }
            },
            'find_nearest_store': {
                'method': self.find_nearest_store,
                'description': 'Finds the nearest store based on the provided location and optional store type. Parameters should be provided as an object with "location" (required) and "store_type" (optional) fields. Example: { "type": "call_tool", "tool": "find_nearest_store", "param": {"location": "Springfield, IL", "store_type": "grocery"} }',
                'response': 'Returns the nearest store. Example: {"id": "1", "name": "Super Foods", "address": "123 Main St, Springfield, IL", "distance": "0.5 miles"}',
                'param_info': {
                    'required': True,
                    'type': 'object',
                    'description': 'An object with "location" (required) and "store_type" (optional) fields',
                    'schema': {
                        'location': 'String representing the location (e.g., "Springfield, IL")',
                        'store_type': 'Optional string representing the store type (e.g., "grocery")'
                    }
                }
            },
            'get_store_details': {
                'method': self.get_store_details,
                'description': 'Gets detailed information about a specific store. Parameter should be a string containing the store ID. Example: { "type": "call_tool", "tool": "get_store_details", "param": "1" }',
                'response': 'Returns detailed information about the store. Example: {"id": "1", "name": "Super Foods", "type": "grocery", "address": "123 Main St, Springfield, IL", "hours": "8:00 AM - 10:00 PM", "phone": "555-123-4567", "services": ["Deli", "Bakery", "Pharmacy"]}',
                'param_info': {
                    'required': True,
                    'type': 'string',
                    'description': 'Store ID as a string (e.g., "1")'
                }
            }
        }

    def get_store_types(self):
        """Gets the list of available store types."""
        types = list(set([store['type'] for store in self.stores_data]))
        return types
    
    def get_stores_by_type(self, store_type):
        """Gets the stores of a specific type."""
        matching_stores = [
            {
                'id': store['id'],
                'name': store['name'],
                'address': store['address']
            }
            for store in self.stores_data
            if store['type'].lower() == store_type.lower()
        ]
        return matching_stores
    
    def get_stores_by_name(self, store_name):
        """Gets the stores of a specific name."""
        matching_stores = [
            {
                'id': store['id'],
                'name': store['name'],
                'address': store['address']
            }
            for store in self.stores_data
            if store['name'].lower() == store_name.lower()
        ]
        return matching_stores

    def find_nearest_store(self, param):
        """Finds the nearest store based on the provided location and optional type."""
        location = param.get('location')
        store_type = param.get('store_type')
        
        # Validate we have a location
        if not location:
            return {'error': 'Location is required to find nearest store'}
        
        # In a real implementation, we would use geocoding to convert the location to coordinates
        # For this example, we'll simulate by assuming the location is in Springfield
        # and we'll just rank stores by a simple distance calculation
        
        # Simulate coordinates for the given location (centered in Springfield)
        location_coords = {'lat': 39.78, 'long': -89.65}
        
        # Filter by store type if provided
        filtered_stores = self.stores_data
        if store_type and store_type.lower() in [t.lower() for t in self.get_store_types()]:
            filtered_stores = [store for store in self.stores_data if store['type'].lower() == store_type.lower()]
        
        # Calculate distances (simplified)
        stores_with_distance = []
        for store in filtered_stores:
            # Calculate Euclidean distance (simplified for demonstration)
            lat_diff = store['coordinates']['lat'] - location_coords['lat']
            long_diff = store['coordinates']['long'] - location_coords['long']
            distance = ((lat_diff ** 2) + (long_diff ** 2)) ** 0.5
            
            # Convert to miles (very rough approximation for demonstration)
            distance_miles = distance * 69
            
            stores_with_distance.append({
                'id': store['id'],
                'name': store['name'],
                'address': store['address'],
                'type': store['type'],  # Include type for more informative results
                'distance': f"{distance_miles:.1f} miles"
            })
        
        # Sort by distance and return the closest
        stores_with_distance.sort(key=lambda x: float(x['distance'].split()[0]))
        return stores_with_distance[0] if stores_with_distance else {'error': 'No stores found'}
    
    def get_store_details(self, store_id):
        """Gets detailed information about a specific store."""
        for store in self.stores_data:
            if store['id'] == store_id:
                # Return all details except coordinates which aren't needed by the user
                return {
                    'id': store['id'],
                    'name': store['name'],
                    'type': store['type'],
                    'address': store['address'],
                    'hours': store['hours'],
                    'phone': store['phone'],
                    'services': store['services']
                }
        return {'error': 'Store not found.'}

