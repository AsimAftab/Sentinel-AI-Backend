# src/utils/langgraph_router.py

from langchain_core.messages import HumanMessage
from src.graph.graph_builder import graph

def route_to_langgraph(command: str, verbose: bool = True) -> str:
    if verbose:
        print(f"\n🧠 Routing command to LangGraph: '{command}'")

    inputs = {"messages": [HumanMessage(content=command)]}
    last_state = None  # We will store the last seen state here

    for step_output in graph.stream(inputs, {"recursion_limit": 10}):
        for node_name, node_result in step_output.items():
            # THE FIX: Always capture the most recent state
            last_state = node_result

            if verbose:
                if node_name == "__end__":
                    print("\n✅ Graph execution finished.")
                else:
                    print(f"\n--- Executing Node: {node_name} ---")
                    # The output is now the entire state, let's print the last message
                    last_message = node_result['messages'][-1]
                    print(f"📤 Output:\n{last_message}")
    
    # Use the last captured state, which is guaranteed to exist.
    # Filter for AI messages from agents and get the last one for the final answer.
    ai_messages = [msg[1] for msg in last_state['messages'] if isinstance(msg, tuple) and msg[0] == 'ai']
    
    if ai_messages:
        final_answer = ai_messages[-1]
    else:
        # Fallback if no agent produced a final answer
        final_answer = "The task is complete, but I don't have a specific answer to show."
    
    if verbose:
        print(f"\n💬 Final Answer: {final_answer}")

    return final_answer