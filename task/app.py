# task/app.py

import asyncio
from task.clients.client import DialClient
from task.constants import DEFAULT_SYSTEM_PROMPT, API_KEY  # Make sure API_KEY is set
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role

async def start(stream: bool) -> None:
    # 1. Create DialClient instance
    client = DialClient("gpt-4o", api_key=API_KEY)
    
    # 2. Create Conversation object
    conversation = Conversation()
    
    # 3. Get System prompt from console or use default
    system_prompt = input("Enter system prompt (or press Enter to use default): ").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    conversation.add_message(Message(role=Role.SYSTEM, content=system_prompt))
    
    # 4. Conversation loop
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # 6. Add user message to conversation history
        conversation.add_message(Message(role=Role.USER, content=user_input))
        
        # 7. Call completion method
        if stream:
            print("DIAL (streaming): ", end="", flush=True)
            response = ""
            async for chunk in client.stream_completion(conversation.messages):
                print(chunk, end="", flush=True)
                response += chunk
            print()
        else:
            response = await client.get_completion(conversation.messages)
            print(f"DIAL: {response}")
        
        # 8. Add generated message to history
        conversation.add_message(Message(role=Role.AI, content=response))

# Run the async start function with streaming enabled
if __name__ == "__main__":
    asyncio.run(start(True))