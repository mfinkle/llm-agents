
class ToolProvider:
    """Base class for tool providers that can register tools with the agent"""
    
    def __init__(self):
        """Initialize the tool provider"""
        self._initialize_data()

    def _initialize_data(self):
        """Initialize any data needed by the tools - override in subclasses"""
        pass
        
    def get_tools(self):
        """Return a dictionary of tools provided by this provider"""
        return {}