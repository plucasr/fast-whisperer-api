import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

async def test_token_usage():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
    messages = [HumanMessage(content="Hello, tell me a very short joke.")]
    
    print("--- Invoking ---")
    response = await llm.ainvoke(messages)
    print(f"Response Metadata: {response.response_metadata}")
    if 'usage_metadata' in response.response_metadata:
        print(f"Token Usage (Invoke): {response.response_metadata['usage_metadata']}")
    else:
        print("No usage_metadata in invoke response request.")

    print("\n--- Streaming ---")
    async for event in llm.astream_events(messages, version="v1"):
        if event["event"] == "on_chat_model_end":
            print(f"Stream End Event Data: {event['data']}")
            output = event['data'].get('output')
            if output and hasattr(output, 'response_metadata'):
                 print(f"Token Usage (Stream): {output.response_metadata.get('usage_metadata')}")

if __name__ == "__main__":
    asyncio.run(test_token_usage())
