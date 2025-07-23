# src/graph/agent_state.py
from typing import TypedDict, Annotated, Sequence, Union
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # Allow simple strings in the message sequence for supervisor output
    messages: Annotated[Sequence[Union[BaseMessage, str]], operator.add]
    next: str # This field is no longer used by the Llama3 supervisor but can be kept for other uses