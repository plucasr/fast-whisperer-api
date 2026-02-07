import operator
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the state
class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

# Initialize LLM
# Using gemini-2.0-flash-exp as per common usage, or fall back to 1.5-flash
# Assuming env vars are set: GOOGLE_API_KEY
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

# --- System Prompt ---
SYSTEM_PROMPT = """You are a helpful AI assistant specialized in theological matters, biblical studies, and sermon preparation. 
Your goal is to assist users in understanding biblical texts, theological concepts, and church history.

Guidelines:
1. **Biblical Accuracy**: Prioritize accuracy in biblical references and theological definitions. Use standard citation formats (e.g., John 3:16).
2. **Theological Depth**: When asked about a concept, provide a balanced view, mentioning different theological perspectives (e.g., Reformed, Arminian, Catholic, Orthodox) when relevant and appropriate, unless asked for a specific viewpoint.
3. **Sermon Structure**: If asked to help with a sermon, suggest clear structures (e.g., Expository, Topical) and provide homiletical outlines.
4. **Tone**: Maintain a respectful, scholarly, yet accessible tone.
5. **Context**: Always consider the historical and literary context of biblical passages.

If a user asks about non-theological topics, politely answer but try to steer the conversation back to how it might relate to faith or theology if possible, or just be a helpful assistant while maintaining your persona.
"""

# --- Nodes ---

def chatbot_node(state: ChatState):
    """Generates a response using the LLM."""
    messages = state["messages"]
    
    # Ensure system message is at the start (or appended to context effectively)
    # LangGraph state stores history. We can prepend the system prompt if it's not there,
    # or just pass it to the invoke call. 
    # Here we'll create a call sequence.
    
    prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm.invoke(prompt_messages)
    return {"messages": [response]}

# --- Graph Construction ---

workflow = StateGraph(ChatState)

workflow.add_node("chatbot", chatbot_node)
workflow.set_entry_point("chatbot")
workflow.add_edge("chatbot", END)

app = workflow.compile()
