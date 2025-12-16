from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class PatientState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    patient_condition: str
    revealed_symptoms: Annotated[List[str], operator.add]
    all_symptoms: List[str]
    convo_stage: str
    accepted: bool