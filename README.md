# AI Agent Chatbot

This repository contains an **AI agent chatbot** implemented in two variants:

- **Baseline Agent** – a simple, linear implementation  
- **LangGraph Agent** – a graph-based implementation with verification, retries, and safety controls  

Both agents use **Google Gemini models** and a **Streamlit-based chat interface**.  
They share the same prompts, models, and tools — the difference lies in **how execution flow, verification, and recovery are handled**.

The goal of this project is to demonstrate **production-oriented agent design principles** with **explicit control flow**, **defensive handling**, and **minimal hidden abstractions**.

---

## 🚀 What this project does

The chatbot behaves like a real-world AI agent that:

- Accepts natural language questions via a chat-style UI
- Decides whether a query can be answered directly or requires external search
- Uses DuckDuckGo search for real-world and time-sensitive information
- Synthesizes grounded answers using retrieved context
- Verifies answers before returning them (LangGraph agent)
- Handles failures, retries, and hallucinations explicitly
- Falls back across multiple LLMs when needed

---

## 🧠 Agent Capabilities

- **Decision routing** between direct answering and tool usage  
- **External search** via DuckDuckGo  
- **Answer synthesis** with controlled formatting  
- **Answer verification** (grounding, hallucination, routing, format)  
- **Failure-aware retries** with bounded limits  
- **Hallucination abort mechanism** for safety  
- **Multi-model fallback** (Gemini Flash, Flash Lite, Gemma)  
- **Confidence scoring** based on verification outcome  
- **Latency tracking** per user query  
- **Stateless backend design** (each query is independent)

---

## 🧠 Agent Implementations

### 1️⃣ Baseline Agent

**Purpose:** Demonstrate core agent logic with minimal complexity.

- Linear, single-pass execution
- Decision → (optional search) → answer
- No verification or retries
- Easy to understand and reason about
- Useful as a learning and comparison baseline

---

### 2️⃣ LangGraph Agent (Production-Oriented)

**Purpose:** Demonstrate a robust, verifiable agent workflow.

Key characteristics:

- Explicit graph-based orchestration using **LangGraph**
- Separate nodes for decision, search, synthesis, and verification
- Verification layer checks:
  - grounding against search results
  - hallucinations
  - routing correctness
  - output format
- **Bounded retries** to avoid infinite loops
- **Immediate abort on hallucination**
- Failure-type classification to drive recovery behavior
- Confidence and latency attached to every execution

This implementation shows how safety, reliability, and observability can be layered
on top of a basic agent without changing the core logic.

---

## 🛡️ Verification & Safety Logic

The LangGraph agent verifies every generated answer and classifies failures into
explicit categories:

- `VERIFICATION_NOT_GROUNDED` – answer not supported by search results
- `VERIFICATION_HALLUCINATION` – fabricated or incorrect facts
- `SYNTHESIS_ERROR` – formatting or generation issues
- `DECISION_PARSE_ERROR` – routing or parsing failures

### Safety rules:
- Hallucinations → **immediate abort**
- Other failures → **bounded retries**
- Retries exhausted → safe stop with explanation

---

## 📊 Observability

For every query, the agent tracks:

- Routing decision and reason
- Model used
- Failure type (if any)
- Retry count
- Confidence score
- End-to-end latency (ms)

This makes the agent **debuggable, explainable**.

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

- Demonstrate real-world AI agent design
- Keep execution flow explicit and inspectable
- Show how verification and safety can be added incrementally
- Serve as a portfolio-quality reference for agent architectures

The baseline agent stays intentionally simple, while the LangGraph agent illustrates how production concerns (verification, retries, safety) can be layered on cleanly.

---

## 📝 Notes

- The agent backend is **stateless**
- No user data is persisted
- External dependencies are kept **minimal and explicit**
- Verification logic exists only in the LangGraph agent
- This project is intended for **learning, experimentation, and portfolio use**


---

## 👩‍💻 Author

**Pratiksha Dhavane**  
Data Scientist | Generative AI Practitioner
