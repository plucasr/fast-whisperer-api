
import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from chat_agent import app as chat_agent_app

# Load environment variables
load_dotenv()

async def test_agent():
    print("=" * 60)
    print("Testing Theological Chat Agent")
    print("=" * 60)
    
    # Test query
    query = "What is the difference between justification and sanctification?"
    print(f"Query: {query}")
    print("-" * 60)
    
    try:
        initial_state = {"messages": [HumanMessage(content=query)]}
        result = await chat_agent_app.ainvoke(initial_state)
        
        last_message = result["messages"][-1]
        print(f"Response:\n{last_message.content}")
        print("-" * 60)
        
        if len(last_message.content) > 50:
            print("✅ Test Passed: Agent returned a substantial response.")
        else:
            print("⚠️ Test Warning: Response seems too short.")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
