import os
import operator
from typing import Annotated, TypedDict, List, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the state
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    hub_url: str
    discovered_links: List[str]
    current_repo: str
    resources_found: List[dict]

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

from tools.github_tools import get_readme_content, list_repo_files

# --- Nodes ---

def read_readme_node(state: AgentState):
    """Reads the README of the hub and extracts potential resource links."""
    print(f"Reading README for {state['hub_url']}...")
    
    readme_content = get_readme_content(state['hub_url'])
    
    if "Error" in readme_content:
        print(f"Failed to read README: {readme_content}")
        return {"discovered_links": []}

    prompt = f"""
    You are a theological resource scout. Analyze the following README content and extract GitHub repository URLs that likely contain raw theological data (lexicons, bibles, dictionaries).
    
    README Content:
    {readme_content[:15000]} # Truncate to avoid context limits
    
    Return a comma-separated list of URLs. Only return the URLs, nothing else.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    links = [link.strip() for link in response.content.split(',') if "github.com" in link]
    print(f"Discovered {len(links)} links.")
    return {"discovered_links": links}

def inspect_repo_node(state: AgentState):
    """Inspects a specific repository for resource files."""
    if not state.get('discovered_links'):
        return {"resources_found": [], "current_repo": None}

    # Queue processing logic (simplistic for this example, just process head)
    # In a real cycle, we'd pop from the list.
    repo_url = state['discovered_links'][0] 
    print(f"Inspecting {repo_url}...")
    
    target_extensions = ['.sqlite', '.db', '.json', '.xml', '.txt', '.md', '.doc', '.xlsx']
    found_files = list_repo_files(repo_url, extensions=target_extensions)
    print(f"Found {len(found_files)} relevant files in {repo_url}")
    
    return {"resources_found": found_files, "current_repo": repo_url}

from tools.db_tools import save_resource

def catalog_node(state: AgentState):
    """Saves the found resources to the database."""
    resources = state.get('resources_found', [])
    print(f"Cataloging {len(resources)} resources...")
    
    saved_count = 0
    for res in resources:
        save_resource(res)
        saved_count += 1
        
    return {"messages": [SystemMessage(content=f"Cataloging complete. Saved {saved_count} resources.")]}

# --- Graph Construction ---

workflow = StateGraph(AgentState)

workflow.add_node("read_readme", read_readme_node)
workflow.add_node("inspect_repo", inspect_repo_node)
workflow.add_node("catalog", catalog_node)

workflow.set_entry_point("read_readme")

workflow.add_edge("read_readme", "inspect_repo")
workflow.add_edge("inspect_repo", "catalog")
workflow.add_edge("catalog", END)

app = workflow.compile()
