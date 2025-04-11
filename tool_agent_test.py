import llm

from tool_agent import ToolAgent
from mock_providers import UtilityToolProvider, AppointmentToolProvider, ProgramToolProvider, StoreLocatorToolProvider


# Standalone chat function for testing
def start_chat(model):
    """Start an interactive chat session with the agent"""
    agent = ToolAgent(model_name=model)

    # Register default tool providers
    agent.register_provider(UtilityToolProvider())
    agent.register_provider(AppointmentToolProvider())
    agent.register_provider(ProgramToolProvider())
    agent.register_provider(StoreLocatorToolProvider())

    conversation = agent.create_conversation()
    
    print("Chat initialized. Type 'exit', 'quit', or 'bye' to end the session.")
    
    while True:
        user_input = input('You: ')
        if user_input.lower().strip() in ['exit', 'quit', 'bye']:
            print('Goodbye!')
            break
        
        result = agent.process_message(conversation, user_input)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Agent: {result['text']}")

    # After chat loop is done, print token usage
    usage = agent.get_token_usage()
    print("\nToken Usage Summary:")
    print(f"  Input tokens: {usage.get('input', 0)}")
    print(f"  Output tokens: {usage.get('output', 0)}")
    print(f"  Total tokens: {usage.get('input', 0) + usage.get('output', 0)}")

if __name__ == '__main__':
    try:
        model_alias = 'gemini-2.0-flash'
        start_chat(model=model_alias)

    except llm.UnknownModelError as e:
        print(f"\nThe model alias {model_alias} provided in the test is not supported. Error: {e}\n")
        print(f"Supported models are: {ToolAgent.get_supported_models()}")