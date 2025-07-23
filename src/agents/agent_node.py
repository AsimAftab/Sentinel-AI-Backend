# src/agents/agent_node.py

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import ToolMessage
from .agent_node import AgentState

def create_agent_node(llm, tools, system_prompt: str):
    """
    Creates a node for a specific agent. This node executes the agent's logic.
    """
    agent = create_openai_tools_agent(llm, tools, system_prompt)
    executor = AgentExecutor(agent=agent, tools=tools)

    def agent_node(state: AgentState):
        result = executor.invoke(state)
        return {"messages": [ToolMessage(content=result["output"], tool_call_id="supervisor")]}
    
    return agent_node