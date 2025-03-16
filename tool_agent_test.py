from tool_agent import ToolAgent


# Standalone chat function for testing
def start_chat(model):
    """Start an interactive chat session with the agent"""
    agent = ToolAgent(model_name=model)
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
    start_chat('gemini-2.0-flash')