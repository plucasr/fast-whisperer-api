import operator
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from config import GEMINI_MODEL

# Load environment variables
load_dotenv()

# Define the state
class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

# Define Tool Models
from pydantic import BaseModel, Field

class DictionaryEntry(BaseModel):
    """
    Detailed information about a Greek or Hebrew word, including its original form,
    transliteration, phonetic pronunciation, definition, and usage examples.
    """
    word: str = Field(description="The word in English or the target language.")
    original: str = Field(description="The original Greek or Hebrew word.")
    transliteration: str = Field(description="The transliteration of the original word.")
    phonetic: str = Field(description="The phonetic pronunciation of the word.")
    definition: str = Field(description="The definition of the word.")
    usage: str = Field(description="Examples of how the word is used in context or theological significance.")
    suggestions: List[str] = Field(description="A list of 2-3 short, relevant follow-up questions for the user to ask, such as 'Where else does this appear?' or 'Compare with X'.")

# Initialize LLM
# Using GEMINI_MODEL from config
# Assuming env vars are set: GOOGLE_API_KEY
# using streaming=True to ensure on_chat_model_stream events are emitted via astream_events
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.7, streaming=True)
llm_with_tools = llm.bind_tools([DictionaryEntry])

# --- System Prompt ---
SYSTEM_PROMPT = """You are a helpful AI assistant specialized in theological matters, biblical studies, and sermon preparation. 
Your goal is to assist users in understanding biblical texts, theological concepts, and church history.

Guidelines:
1. **Biblical Accuracy**: Prioritize accuracy in biblical references and theological definitions. Use standard citation formats (e.g., John 3:16).
2. **Theological Depth**: When asked about a concept, provide a balanced view, mentioning different theological perspectives (e.g., Reformed, Arminian, Catholic, Orthodox) when relevant and appropriate, unless asked for a specific viewpoint.
3. **Sermon Structure**: If asked to help with a sermon, suggest clear structures (e.g., Expository, Topical) and provide homiletical outlines.
4. **Tone**: Maintain a respectful, scholarly, yet accessible tone.
5. **Context**: Always consider the historical and literary context of biblical passages.
6. **Dictionary Lookups**: You MUST use the `DictionaryEntry` tool in the following cases:
   - The user asks for the meaning, definition, or translation of a specific Greek or Hebrew word.
   - The user asks to identify a word in a specific verse (e.g., "What is the first word in John 1:1?", "What is the Greek word for 'love' in this verse?").
   - A detailed word study is appropriate.
   Do not simple describe it in text; call the tool to provide the structured data.

If a user asks about non-theological topics, politely answer but try to steer the conversation back to how it might relate to faith or theology if possible, or just be a helpful assistant while maintaining your persona.
"""

from langchain_core.runnables import RunnableConfig

# --- Nodes ---

async def chatbot_node(state: ChatState, config: RunnableConfig):
    """Generates a response using the LLM."""
    messages = state["messages"]
    
    # Ensure system message is at the start (or appended to context effectively)
    # LangGraph state stores history. We can prepend the system prompt if it's not there,
    # or just pass it to the invoke call. 
    # Here we'll create a call sequence.
    
    prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = await llm_with_tools.ainvoke(prompt_messages, config=config)
    return {"messages": [response]}

# --- Graph Construction ---

workflow = StateGraph(ChatState)

workflow.add_node("chatbot", chatbot_node)
workflow.set_entry_point("chatbot")
workflow.add_edge("chatbot", END)

app = workflow.compile()

