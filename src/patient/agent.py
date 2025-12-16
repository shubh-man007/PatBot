import os
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from .state import PatientState
from .diagnosis import TREATMENT_OPTIONS

from dotenv import load_dotenv

load_dotenv()

model = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

helper = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def init_condition(condition: str, true_symptoms: List[str]) -> PatientState:
    return {
        "messages": [],
        "patient_condition": condition,
        "revealed_symptoms": [],
        "all_symptoms": true_symptoms,
        "convo_stage": "greeting",
        "accepted": False
    }

def intent_classifier(state: PatientState) -> dict:
    intent = ["greeting", "symptom_inquiry", "treatment_prescription", "general_question"]

    if isinstance(state["messages"][-1], HumanMessage):
        doc_message = state["messages"][-1].content
        system_prompt = (
            f"Given the message said by the Doctor: {doc_message}, determine its intent "
            f"based on these classifications: {', '.join(intent)}. "
            f"Do not add any other classes. Just send back the classification as a string."
        )
        stage = helper.invoke([HumanMessage(system_prompt)])
        return {"convo_stage": stage.content.strip()}
    
    return {}

def treatment_analysis(state: PatientState) -> dict:
    if state["convo_stage"] == "treatment_prescription":
        treatment = state["messages"][-1].content.lower()
        condition = state["patient_condition"]

        if condition not in TREATMENT_OPTIONS:
            return {"accepted": False}
        
        options = TREATMENT_OPTIONS[condition]

        has_accepted = any(keyword in treatment for keyword in options["accepted"])
        has_rejected = any(keyword in treatment for keyword in options["rejected"])

        if has_accepted:
            return {"accepted": True}
        elif has_rejected:
            return {"accepted": False}

    return {"accepted": False}


def disclosed_symptoms(state: PatientState) -> dict:
    doc_keywords = ["symptoms", "feeling", "experiencing", "what's wrong", "how are you"]
    
    if isinstance(state["messages"][-1], HumanMessage):
        doc_message = state["messages"][-1].content.lower()
        revealed = state["revealed_symptoms"]
        diagnosed = state["all_symptoms"]
        remaining = [item for item in diagnosed if item not in revealed]
        
        if len(revealed) == len(diagnosed):
            return {}
        
        exists = any(s in doc_message for s in doc_keywords)
        if exists:
            if len(remaining) >= 2:
                return {"revealed_symptoms": remaining[0:2]}
            return {"revealed_symptoms": remaining}
    
    return {}


def res_patient(state: PatientState) -> dict:
    condition = state["patient_condition"]
    symptoms = state["revealed_symptoms"]
    stage = state["convo_stage"]

    if stage == "greeting":
        system_prompt = (
            f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
            f" The doctor said: {state['messages'][-1].content}. "
            "If the doctor greets you or engages in casual, non-medical small talk, respond like a real person in a chat with their doctor."
            " Keep it brief, natural, and avoid stage directions (no asterisks or actions)."
            " Mention how you feel without listing specific symptoms yet."
        )

    elif stage == "general_question":
        system_prompt = (
            f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
            f" The doctor asked: {state['messages'][-1].content}. "
            "Respond naturally as a real patient would in a chat with their doctor."
            " Keep it concise, avoid stage directions, and stay on-topic."
        )

    elif stage == "treatment_prescription":
        if state["accepted"]:
            system_prompt = (
                f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
                f" The doctor prescribed: {state['messages'][-1].content}. "
                "Acknowledge and accept the treatment politely, keep it brief like a chat, and say goodbye."
                " Avoid stage directions or emotive actions."
            )
        else:
            system_prompt = (
                f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
                f" The doctor prescribed: {state['messages'][-1].content}. "
                "Politely decline and ask for an alternative in a concise chat response."
                " Avoid stage directions or emotive actions."
            )

    elif stage == "symptom_inquiry":
        if len(symptoms) == 0:
            system_prompt = (
                f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
                " Respond naturally to the doctor's small talk or symptom inquiries in a concise chat style."
                " Avoid stage directions or dramatized actions."
            )
        else:
            system_prompt = (
                f"You are chatting online as a patient. Do not reveal or name your underlying condition: {condition}."
                f" You can mention these symptoms only: {', '.join(symptoms)}."
                " Share them naturally in a concise chat reply and avoid stage directions."
            )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = model.invoke(messages)
    
    return {"messages": [AIMessage(content=response.content)]}


def node_router(state: PatientState) -> str:
    stage = state["convo_stage"]
    match stage:
        case "greeting":
            return "generate_response"
        case "treatment_prescription":
            return "evaluate_treatment"
        case "symptom_inquiry":
            return "analyze_symptoms"
        case "general_question":
            return "generate_response"


def create_graph():
    workflow = StateGraph(PatientState)

    workflow.add_node("analyze_symptoms", disclosed_symptoms)
    workflow.add_node("generate_response", res_patient)
    workflow.add_node("evaluate_treatment", treatment_analysis)
    workflow.add_node("conversation_stage", intent_classifier)
    
    workflow.set_entry_point("conversation_stage")
    workflow.add_conditional_edges("conversation_stage", node_router, {
        "analyze_symptoms": "analyze_symptoms",
        "evaluate_treatment": "evaluate_treatment",
        "generate_response": "generate_response"
    })
    workflow.add_edge("analyze_symptoms", "generate_response")
    workflow.add_edge("evaluate_treatment", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

if __name__ == "__main__":
    initial_state = init_condition(
        condition="common cold",
        true_symptoms=["runny nose", "sore throat", "mild fever", "fatigue"]
    )
    
    print("=== Initial State ===")
    print(f"Condition: {initial_state['patient_condition']}")
    print(f"All Symptoms: {initial_state['all_symptoms']}")
    print(f"Revealed Symptoms: {initial_state['revealed_symptoms']}")
    print()
    
    patient_graph = create_graph()
    
    print("=== Conversation Start ===\n")
    
    print("Doctor: Hello, how are you feeling today?")
    initial_state["messages"].append(HumanMessage(content="Hello, how are you feeling today?"))
    
    result = patient_graph.invoke(initial_state)
    print(f"Revealed Symptoms: {result['revealed_symptoms']}")
    print(f"Patient: {result['messages'][-1].content}\n")
    
    print("Doctor: What symptoms are you experiencing?")
    result["messages"].append(HumanMessage(content="What symptoms are you experiencing?"))
    
    result = patient_graph.invoke(result)
    print(f"Revealed Symptoms: {result['revealed_symptoms']}")
    print(f"Patient: {result['messages'][-1].content}\n")
    
    print("Doctor: How long have you had the runny nose?")
    result["messages"].append(HumanMessage(content="How long have you had the runny nose?"))
    
    result = patient_graph.invoke(result)
    print(f"Revealed Symptoms: {result['revealed_symptoms']}")
    print(f"Patient: {result['messages'][-1].content}\n")
    
    print("Doctor: Any other symptoms?")
    result["messages"].append(HumanMessage(content="Any other symptoms?"))
    
    result = patient_graph.invoke(result)
    print(f"Revealed Symptoms: {result['revealed_symptoms']}")
    print(f"Patient: {result['messages'][-1].content}\n")
    
    print("=== Final State ===")
    print(f"Total messages: {len(result['messages'])}")
    print(f"All symptoms revealed: {len(result['revealed_symptoms']) == len(result['all_symptoms'])}")