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


# --- LLM and Tools setup ---
llm = ChatOllama(model="llama3")
browser_agent_tools = browser_tools


# --- Supervisor Chain definition ---
supervisor_prompt_str = """You are a supervisor in a multi-agent AI system. Your role is to oversee a team of specialized agents and route user requests.
Based on the last user message, you must select the next agent to act from the available list or decide if the task is complete.

Available agents:
- `Browser`: For tasks that require accessing the internet, searching for information, or scraping websites.
- `FINISH`: If the user's question has been fully answered and the task is complete.

Analyze the conversation and output *only* the name of the next agent to act.
Your response MUST BE exactly one word: `Browser` or `FINISH`.
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

browser_agent_node = create_agent_node(llm, browser_agent_tools, "Browser")
# ==================================================================


def supervisor_node(state: AgentState) -> dict:
    """Invokes the supervisor chain and formats the output for the graph."""
    # Get the supervisor's decision and clean it up
    result = supervisor_chain.invoke(state).strip()

    # THE FIX: If the supervisor gives an empty response, we assume it's finished.
    if not result:
        print("--- SUPERVISOR: (empty output, defaulting to FINISH) ---")
        return {"messages": ["FINISH"]}
    
    print(f"--- SUPERVISOR: (decided next step is {result}) ---")
    return {"messages": [result]}
# --- Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Browser", browser_agent_node)

def router(state):
    next_agent = state['messages'][-1]
    if "Browser" in next_agent:
        return "Browser"
    else:
        return END

workflow.add_conditional_edges("supervisor", router, {"Browser": "Browser", "__end__": END})
workflow.add_edge("Browser", "supervisor")
workflow.set_entry_point("supervisor")
graph = workflow.compile()