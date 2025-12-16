from typing import List
from langchain_core.messages import HumanMessage
from .agent import init_condition, create_graph

class Patient:
    def __init__(self, condition: str, true_symptoms: List[str]):
        self.condition = condition
        self.state = init_condition(condition, true_symptoms)
        self.graph = create_graph()
    
    def doc_turn(self, message: str):
        self.state["messages"].append(HumanMessage(content=message))
        result = self.graph.invoke(self.state)
        self.state = result
        return result['messages'][-1].content
