import sys
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from patient.agent import create_graph, init_condition

def test_patient():
    app = create_graph()

    state = init_condition(
        "common cold",
        ["runny nose", "sore throat", "mild cough", "congestion"]
    )

    state["messages"].append(HumanMessage("Hello"))
    state = app.invoke(state)

    assert state["convo_stage"] == "greeting"
    assert isinstance(state["messages"][-1].content, str)
    assert len(state["revealed_symptoms"]) == 0

    state["messages"].append(HumanMessage("How are you feeling?"))
    state = app.invoke(state)

    assert state["convo_stage"] == "symptom_inquiry"
    assert len(state["revealed_symptoms"]) == 2   

    state["messages"].append(HumanMessage("Tell me more about your symptoms"))
    state = app.invoke(state)

    assert state["convo_stage"] == "symptom_inquiry"
    assert len(state["revealed_symptoms"]) == 4  

    state["messages"].append(HumanMessage("I prescribe antibiotics"))
    state = app.invoke(state)

    assert state["convo_stage"] == "treatment_prescription"
    assert state["accepted"] is False  

    state["messages"].append(HumanMessage("What about rest and fluids?"))
    state = app.invoke(state)

    assert state["accepted"] is True   
    assert state["convo_stage"] == "treatment_prescription"

    assert isinstance(state["messages"][-1].content, str)
    assert "*" not in state["messages"][-1].content

    print("\nFINAL STATE:", state)
