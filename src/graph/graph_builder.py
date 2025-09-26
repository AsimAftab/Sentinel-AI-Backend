# src/graph/graph_builder.py

# Ensure this import is at the top
from langchain_core.messages import BaseMessage

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

from src.graph.agent_state import AgentState
from src.tools.browser_tools import browser_tools
from src.tools.music_tools import music_tools # <--- MODIFIED: Import new music tools


# --- LLM and Tools setup ---
llm = ChatOllama(model="llama3")
browser_agent_tools = browser_tools
music_agent_tools = music_tools # <--- MODIFIED: Define music tools list


# --- Supervisor Chain definition ---
# <--- MODIFIED: Updated the supervisor prompt to include the Music agent
supervisor_prompt_str = """You are a supervisor in a multi-agent AI system. Your role is to oversee a team of specialized agents and route user requests.
Based on the last user message, you must select the next agent to act from the available list or decide if the task is complete.

Available agents:
- `Browser`: For tasks that require accessing the internet, searching for information, or scraping websites.
- `Music`: For tasks related to searching for and playing songs on Spotify.
- `FINISH`: If the user's question has been fully answered and the task is complete.

Analyze the conversation and output *only* the name of the next agent to act.
Your response MUST BE exactly one word: `Browser`, `Music`, or `FINISH`.
"""
supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", supervisor_prompt_str),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

supervisor_chain = supervisor_prompt | llm | StrOutputParser()


# ==================================================================
# CORRECTED AGENT NODE FUNCTION
# This is the corrected function that finds the right message.
# ==================================================================
react_prompt = hub.pull("hwchase17/react")

def create_agent_node(llm, tools, agent_name: str):
    """
    Creates a node for a ReAct agent. This has been updated to find the
    correct input message for the agent.
    """
    agent = create_react_agent(llm, tools, react_prompt)
    executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True)

    def agent_node(state: AgentState):
        # Search backwards through the messages to find the last message that is
        # a HumanMessage or AIMessage, not the supervisor's plain string output.
        last_content_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, BaseMessage):
                last_content_message = message
                break

        if last_content_message is None:
            raise ValueError("No valid message found in state for the agent to process.")

        # Invoke the agent with the correct content
        print(f"--- EXECUTING AGENT: {agent_name} ---")
        result = executor.invoke({"input": last_content_message.content})
        
        return {"messages": [("ai", f"({agent_name} agent): {result['output']}")]}

    return agent_node

# --- Create Agent Nodes ---
browser_agent_node = create_agent_node(llm, browser_agent_tools, "Browser")
music_agent_node = create_agent_node(llm, music_agent_tools, "Music") # <--- MODIFIED: Create music agent node
# ==================================================================


def supervisor_node(state: AgentState) -> dict:
    """Invokes the supervisor chain and formats the output for the graph."""
    # Get the supervisor's decision and clean it up
    result = supervisor_chain.invoke(state).strip()

    # THE FIX: If the supervisor gives an empty response, we assume it's finished.
    if not result or not result in ["Browser", "Music", "FINISH"]: # <--- MODIFIED: More robust check
        print(f"--- SUPERVISOR: (invalid output '{result}', defaulting to FINISH) ---")
        return {"messages": ["FINISH"]}
    
    print(f"--- SUPERVISOR: (decided next step is {result}) ---")
    return {"messages": [result]}


# --- Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Browser", browser_agent_node)
workflow.add_node("Music", music_agent_node) # <--- MODIFIED: Add the Music node to the graph

def router(state):
    """Routes to the correct agent based on the supervisor's decision.""" # <--- MODIFIED: Docstring and logic
    next_agent = state['messages'][-1]
    if "Browser" in next_agent:
        return "Browser"
    elif "Music" in next_agent: # <--- MODIFIED: Add routing for Music agent
        return "Music"
    else:
        return END

# <--- MODIFIED: Add "Music" to the conditional edges mapping
workflow.add_conditional_edges("supervisor", router, {"Browser": "Browser", "Music": "Music", "__end__": END})

workflow.add_edge("Browser", END)
workflow.add_edge("Music", END) # <--- MODIFIED: Add edge from Music back to supervisor

workflow.set_entry_point("supervisor")
graph = workflow.compile()