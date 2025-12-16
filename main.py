import os
import random
import logging
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json

from patient.patient import Patient
from patient.diagnosis import CONDITION_SYMPTOMS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONDITION_SYMPTOMS = {
#     "common cold": ["runny nose", "sore throat", "mild cough", "congestion", "fatigue", "sneezing"],
#     "fever": ["high temperature", "chills", "sweating", "headache", "body aches", "weakness"],
#     "dengue": ["high fever", "severe headache", "pain behind eyes", "joint pain", "muscle pain", "rash"],
#     "migraine": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "visual disturbances"],
#     "bacterial pneumonia": ["cough with phlegm", "fever", "chest pain", "difficulty breathing", "fatigue", "chills"],
#     "gastric acidity": ["heartburn", "chest discomfort", "bitter taste", "bloating", "nausea", "burping"]
# }


class ConnectionManager:
    def __init__(self):
        self.doctor_patients: Dict[str, list] = {}
        self.patient_connections: Dict[str, WebSocket] = {}
        self.patients: Dict[str, Patient] = {}
        self.patient_to_doctor: Dict[str, str] = {}
        
    def create_patient(self, doctor_id: str, patient_id: str) -> dict:
        condition = random.choice(list(CONDITION_SYMPTOMS.keys()))
        symptoms = CONDITION_SYMPTOMS[condition][:random.randint(4, 6)]
        
        patient = Patient(condition, symptoms)
        self.patients[patient_id] = patient
        
        if doctor_id not in self.doctor_patients:
            self.doctor_patients[doctor_id] = []
        self.doctor_patients[doctor_id].append(patient_id)
        self.patient_to_doctor[patient_id] = doctor_id
        
        logger.info(f"Created patient {patient_id} with {condition} for doctor {doctor_id}")
        
        return {
            "patient_id": patient_id,
            "condition": condition,
            "total_symptoms": len(symptoms)
        }
    
    async def connect_patient(self, patient_id: str, websocket: WebSocket):
        await websocket.accept()
        self.patient_connections[patient_id] = websocket
        logger.info(f"Patient {patient_id} connected")
    
    def disconnect_patient(self, patient_id: str):
        if patient_id in self.patient_connections:
            del self.patient_connections[patient_id]
        
        if patient_id in self.patients:
            del self.patients[patient_id]
        
        if patient_id in self.patient_to_doctor:
            doctor_id = self.patient_to_doctor[patient_id]
            if doctor_id in self.doctor_patients:
                self.doctor_patients[doctor_id].remove(patient_id)
            del self.patient_to_doctor[patient_id]
        
        logger.info(f"Patient {patient_id} disconnected and cleaned up")
    
    def get_patient(self, patient_id: str) -> Patient:
        return self.patients.get(patient_id)
    
    async def send_to_patient(self, patient_id: str, message: dict):
        if patient_id in self.patient_connections:
            await self.patient_connections[patient_id].send_json(message)
    
    def get_doctor_patients(self, doctor_id: str) -> list:
        return self.doctor_patients.get(doctor_id, [])


manager = ConnectionManager()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    with open("./static/frontend.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(html_content)


@app.post("/api/doctor/{doctor_id}/create-patient")
async def create_patient_for_doctor(doctor_id: str):
    patient_id = f"patient_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    patient_info = manager.create_patient(doctor_id, patient_id)
    return patient_info


@app.get("/api/doctor/{doctor_id}/patients")
async def get_doctor_patients(doctor_id: str):
    patient_ids = manager.get_doctor_patients(doctor_id)
    patients_info = []
    
    for patient_id in patient_ids:
        patient = manager.get_patient(patient_id)
        if patient:
            patients_info.append({
                "patient_id": patient_id,
                "condition": patient.condition,
                "accepted": patient.state.get("accepted", False),
                "revealed_symptoms": patient.state.get("revealed_symptoms", [])
            })
    
    return {"patients": patients_info}


@app.websocket("/ws/patient/{patient_id}")
async def patient_websocket(websocket: WebSocket, patient_id: str):
    await manager.connect_patient(patient_id, websocket)
    
    patient = manager.get_patient(patient_id)
    if not patient:
        await websocket.send_json({
            "type": "error",
            "content": "Patient not found. Please create patient first."
        })
        await websocket.close()
        return
    
    await websocket.send_json({
        "type": "system",
        "content": f"Patient connected. Condition: {patient.condition}",
        "patient_id": patient_id
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            doctor_message = message_data.get("message", "")
            
            logger.info(f"Patient {patient_id} - Doctor says: {doctor_message}")
            
            try:
                patient_response = patient.doc_turn(doctor_message)
                
                current_state = patient.state
                
                logger.info(f"Patient {patient_id} - Patient says: {patient_response}")
                logger.info(f"Patient {patient_id} - Stage: {current_state['convo_stage']}, Accepted: {current_state['accepted']}")
                
                response_data = {
                    "type": "patient_response",
                    "content": patient_response,
                    "revealed_symptoms": current_state.get("revealed_symptoms", []),
                    "stage": current_state.get("convo_stage", ""),
                    "accepted": current_state.get("accepted", False),
                    "patient_id": patient_id
                }
                
                await websocket.send_json(response_data)
                
                if current_state.get("accepted", False):
                    await websocket.send_json({
                        "type": "conversation_complete",
                        "content": "Patient has accepted treatment. Consultation complete.",
                        "patient_id": patient_id
                    })
                    logger.info(f"Patient {patient_id} - Consultation completed")
                    
            except Exception as e:
                logger.error(f"Error processing message for patient {patient_id}: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}",
                    "patient_id": patient_id
                })
                
    except WebSocketDisconnect:
        manager.disconnect_patient(patient_id)
        logger.info(f"Patient {patient_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for patient {patient_id}: {str(e)}")
        manager.disconnect_patient(patient_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)