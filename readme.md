# PatBot

PatBot is a simulated patient chatbot that allows doctors to practice structured consultations in a web-based interface. Each virtual patient has a hidden diagnosis and symptom set; the doctor must elicit symptoms, propose treatments, and observe how the patient responds in realistic chat-style conversations.

## Deployed Application

- **Live app**: https://patbot-9dti.onrender.com/

## Architecture

PatBot is built as a small FastAPI backend serving a single-page doctor console, with real-time doctor–patient conversations handled over WebSockets and powered by a LangGraph-based patient agent running on Anthropic models.

![Architecture](https://github.com/shubh-man007/PatBot/blob/main/assets/PatBot.png)

- **Backend**: `FastAPI` application in `src/main.py` exposes:
  - REST endpoints for creating patients per doctor and listing active patients.
  - A WebSocket endpoint (`/ws/patient/{patient_id}`) that streams doctor messages to the patient agent and returns structured patient responses.
- **Agent graph**: The patient logic in `src/patient/agent.py` and `src/patient/patient.py` uses LangGraph with a `PatientState` to:
  - Classify the doctor’s intent (greeting, symptom inquiry, treatment prescription, general question).
  - Reveal symptoms incrementally when the doctor asks the right kinds of questions.
  - Evaluate whether a proposed treatment is accepted or rejected for the underlying condition.
  - Generate natural patient replies via Anthropic’s chat model.
- **Frontend**: A static HTML/JS interface (`src/static/frontend.html`) rendered at `/` that:
  - Creates new patients via REST, opens WebSocket connections per patient, and maintains a list of active consultations.
  - Displays chat history, conversation status, and a live list of revealed symptoms for the selected patient.

![Agent Graph](https://github.com/shubh-man007/PatBot/blob/main/assets/graph.png)

## Tech Stack

- **Backend framework**: FastAPI (ASGI) with CORS middleware.
- **Realtime transport**: WebSockets for doctor–patient chat sessions.
- **LLM & orchestration**:
  - `langchain-anthropic` for Anthropic Claude-based chat models.
  - `langgraph` for the stateful patient conversation graph.
- **Web server / runtime**: `uvicorn` as the ASGI server (Render deployment via `render.yaml`).
- **Environment / configuration**:
  - `python-dotenv` for loading environment variables.
  - `ANTHROPIC_API_KEY` configured as a private environment variable on Render.
- **Frontend**:
  - Static HTML/CSS/JavaScript UI (no frontend framework) with a doctor panel and multi-patient sidebar.
  - `marked` for rendering patient markdown responses safely in the chat view.
- **Testing & logging**:
  - Basic unit tests under `src/test` (for patient logic).
  - Structured logging of conversations to `src/conversations.log`.
