# AI Agent Chatbot (Baseline)

This repository contains a **baseline implementation of an AI agent chatbot**
built using **Google Gemini models** and a **Streamlit-based chat interface**.

The objective of this project is to demonstrate **core agent design principles**
without relying on agent orchestration frameworks or hidden abstractions.


---

## 🚀 What this project does

The chatbot behaves like an AI agent that:

- Accepts user questions through a chat-style UI
- Decides whether a question can be answered directly or requires external search
- Uses DuckDuckGo search for real-world or time-sensitive queries
- Synthesizes a grounded final answer using retrieved information
- Falls back across multiple models when a model is unavailable


---

## 🧠 Agent Capabilities

- **Decision routing** between direct answering and tool usage  
- **External search** using DuckDuckGo  
- **Multi-model fallback** (Gemini Flash, Flash Lite, Gemma)  
- **Defensive parsing** of model outputs  
- **Stateless backend design** (each query is handled independently)


---

## 🖥️ User Interface

The frontend is implemented using **Streamlit** and provides a conversational
chatbot experience.

The UI is intentionally kept **thin and presentation-only**:
- No decision logic
- No tool handling
- No model routing

All intelligence and control flow reside in the backend agent.


---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/pratiksha-dhavane/ai_agent_chatbot.git
cd ai_agent_chatbot
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure environment variables
Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
```

### 4️⃣ Run the application
```bash
streamlit run app.py
```


---

## 🎯 Purpose of this Baseline

This baseline implementation is designed to:

- Focus on **fundamental agent behavior**
- Keep control flow explicit and debuggable
- Avoid framework lock-in
- Serve as a clean foundation for future architectural extensions

The core behavior is intentionally kept stable so that future enhancements
can be layered on top without altering the baseline logic.


---

## 📝 Notes

- The agent backend is **stateless**
- External dependencies are kept **minimal and explicit**
- This project is intended for **learning and experimentation**


---

## 👩‍💻 Author

**Pratiksha Dhavane**  
Data Scientist | Generative AI Practitioner
