# AI Agent Chatbot

This repository contains an **AI agent chatbot** implemented in two variants:

- **Baseline Agent** – a simple, linear implementation  
- **LangGraph Agent** – a graph-based implementation with verification and recovery

Both implementations use **Google Gemini models** and a **Streamlit-based chat interface**.
They share the same prompts, models, and tools — the difference lies in how the
agent’s execution flow is structured.

The objective of this project is to demonstrate **core agent design principles**
with clear, explicit control flow and minimal hidden abstractions.

---

## 🚀 What this project does

The chatbot behaves like an AI agent that:

- Accepts user questions through a chat-style UI
- Decides whether a question can be answered directly or requires external search
- Uses DuckDuckGo search for real-world or time-sensitive queries
- Synthesizes a grounded final answer using retrieved information
- Verifies answers before returning them (LangGraph agent)
- Falls back across multiple models when a model is unavailable

---

## 🧠 Agent Capabilities

- **Decision routing** between direct answering and tool usage  
- **External search** using DuckDuckGo  
- **Answer synthesis** with strict formatting constraints  
- **Answer verification and recovery** (LangGraph agent)  
- **Multi-model fallback** (Gemini Flash, Flash Lite, Gemma)  
- **Defensive parsing** of model outputs  
- **Stateless backend design** (each query is handled independently)

---

## 🧠 Agent Implementations

### Baseline Agent
- Linear, single-pass execution
- No verification or retries
- Designed to clearly demonstrate core agent logic

### LangGraph Agent
- Explicit graph-based workflow using LangGraph
- Adds a verification step to validate grounding, routing correctness, and format
- Supports recovery by falling back to search when verification fails
- Makes control flow easier to visualize and extend

---

## 🖥️ User Interface

The frontend is implemented using **Streamlit** and provides a conversational
chatbot experience.

The UI is intentionally kept **thin and presentation-only**:
- No decision logic
- No tool handling
- No model routing

All intelligence, orchestration, and verification logic reside in the backend agent.

---

## ⚙️ Setup Instructions

### 1️. Clone the repository
```bash
git clone https://github.com/pratiksha-dhavane/ai_agent_chatbot.git
cd ai_agent_chatbot
```

### 2. Create and activate a virtual environment (recommended)

```bash
conda create -n search-engine-chatbot python=3.11
conda activate search-engine-chatbot
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
```

### 5. Run the Baseline Agent
```bash
streamlit run baseline_agent/app.py
```

### 6. Run the LangGraph Agent
```bash
streamlit run langgraph_agent/app.py
```

---

## 🎯 Purpose of this Project

This project is designed to:

- Focus on fundamental agent behavior
- Keep control flow explicit and debuggable
- Demonstrate both procedural and graph-based orchestration
- Serve as a clean foundation for more advanced agent patterns

The baseline implementation remains intentionally stable, while the LangGraph
implementation demonstrates how verification and recovery can be layered on
top without changing the core agent logic.

---

## 📝 Notes

- The agent backend is **stateless**
- External dependencies are kept **minimal and explicit**
- Verification logic exists only in the LangGraph agent
- This project is intended for **learning, experimentation, and portfolio use**


---

## 👩‍💻 Author

**Pratiksha Dhavane**  
Data Scientist | Generative AI Practitioner
