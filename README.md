# AI Agent Chatbot

This project implements a production-oriented AI agent that dynamically routes user queries between direct LLM responses and external search tools. It focuses on reliability, explicit control flow, model fallback and short-term memory - key challenges in real-world agentic systems.

---

## 🚀 Key Features

This repository contains an **AI agent chatbot** implemented in two variants:

- **Baseline Agent** - a simple, linear implementation
- **LangGraph Agent** - a graph-based implementation with verification, retries, safety controls, and short-term memory

The LangGraph agent uses **Google Gemini models** with **Groq (Llama)** as a fallback and a **Streamlit-based chat interface**.

The goal of this project is to demonstrate **production-oriented agent design principles** with **explicit control flow**, **defensive handling**, **short-term memory** and **minimal hidden abstractions**.

---

## 🧠 Short-Term Memory (Hybrid Architecture)

The LangGraph agent implements a **hybrid short-term memory system** that combines a sliding window of recent turns with periodic summarization.

### How it works

**Sliding window** - the last 4 conversation turns are always kept in full and passed into every node that needs context.

**Periodic summarization** - every 4 turns, the recent conversation is summarized into a persistent memory profile using Llama 3.3 70b. This summary accumulates facts about the user across the entire session.

**Memory profile, not topic summary** - the summarization prompt is specifically designed to extract and preserve key user facts (name, preferences, what they are building, tools they use) rather than summarizing conversation topics. Facts are updated when the user provides new information and never dropped unless explicitly overwritten.

### Memory flow

Both the **decision node** and the **verification node** receive `summary` and `recent_turns` as context. This means:

- The decision node checks memory before deciding to search, personal facts already known do not trigger a web search
- The verification node uses memory context to correctly pass answers that are grounded in conversation history rather than search results

---

## 🧭 Agent Execution Graph & Architecture

The LangGraph-based agent is implemented as an **explicit control-flow execution graph**. This graph defines how a single user query moves through the system, including decision-making, tool usage, verification, retries and termination.

> The graph does **not** represent a neural network or model internals.
> It represents **deterministic orchestration logic** for a stateful AI agent.

Each query enters the graph, flows through a bounded set of nodes and terminates with either a verified answer or a safe abort.

---

## 🔁 Execution Flow Overview

At a high level, the agent follows this pattern:

1. Accept user input along with memory context (summary + recent turns)
2. Decide how the query should be handled — checking memory first before routing to search
3. Generate an answer (with or without search)
4. Verify the answer against search results, memory context and safety checks
5. Either return, retry with more context or abort safely

There is **no hidden control flow** and **no implicit retries**. Every transition is explicit in the graph.

---

## 🧩 Node-by-Node Architectural Breakdown

### `__start__` - Query Ingress

**Role** - Entry point for every user query

**Responsibilities**
- Accept raw user input
- Load memory context (summary and recent turns) from session state
- Initialize agent state

---

### `decide` - Routing & Risk Assessment

**Role** - Central decision-making node

**Purpose** - Decide how the query should be processed, not responsible for answering it

**Responsibilities**
- Check memory context first, if the answer is already known, answer directly
- Classify query intent and estimate hallucination risk
- Decide whether external search is required
- Rewrite the query into a focused standalone search query if search is needed

**Memory-first rule** - personal facts provided by the user (name, preferences, what they are building) are answered directly from context without triggering a search

**Possible routing outcomes**
- Route directly to `answer`
- Route to `search`

**Model fallback chain** - flash → flash_lite → llama-3.3-70b-versatile

---

### `answer` - Direct LLM Generation

**When executed** - Query is low-risk or answerable from memory context

**Responsibilities** - Generate a candidate answer from memory or stable knowledge

**What it does NOT do** - No verification, no safety judgment, no retries

---

### `verify` - Validation & Safety Gate

**Role** - Final authority before any answer is returned to the user

**Context received** - user input, search results, memory summary, recent turns

**Checks performed**

Conversational input check (runs first) - if the user is sharing personal information or asking about something they previously told the agent, the answer is passed immediately without further checks

Grounding check - only applies when search results are present; fails only if the answer directly contradicts or fabricates beyond search results; rephrasing and logical inference are allowed

Hallucination check - fails only if the answer invents specific facts contradicted by or implausible given search results

Routing check - fails only if no search was used but the answer makes a time-sensitive or externally verifiable claim that cannot be answered from memory or stable knowledge

Format check - fails only if the answer is empty, evasive or restates the question without answering

**Default behavior** - when in doubt, pass; only fail on clear and obvious violations

**Possible outcomes**
- `pass` → answer is accepted
- `retry` → recovery attempt required (bounded)
- `abort` → execution terminated immediately on hallucination

**Model fallback chain** — flash_lite → llama-3.3-70b-versatile

---

### `abort` - Immediate Safety Termination

**When triggered** - Hallucination detected

**Behavior** - Stops execution immediately, returns a safe failure response

**Design rule** - Hallucinations are never retried

---

### `retry` → `increment_retry` - Controlled Recovery

**When triggered** - Non-critical verification failures such as weak grounding or insufficient context

**Responsibilities** - Increment retry counter, enforce retry limits, redirect to search

Retries are explicit, bounded and observable. This prevents silent loops and uncontrolled cost escalation.

---

### `search` - External Information Retrieval

**Role** - Fetch real-world or time-sensitive information

**Tool used** - DuckDuckGo Search

**Query source** - uses the rewritten query from the decision node when available, falls back to raw user input

---

### `synthesize` - Answer Synthesis with Context

**Role** - Combine user query and retrieved search results into a grounded answer

**Model fallback chain** - flash_lite → llama-3.1-8b-instant

The output is always sent back to `verify` before being returned to the user.

---

### `__end__` - Execution Termination

**When reached** - Verification passes or execution is aborted

**Responsibilities** - Return final response with metadata (confidence, latency, retry count)

---

## 🤖 Model Architecture

| Task | Primary | Fallback 1 | Fallback 2 |
|------|---------|------------|------------|
| Decision | gemini-2.5-flash | gemini-2.5-flash-lite | llama-3.3-70b-versatile |
| Synthesis | gemini-2.5-flash-lite | llama-3.1-8b-instant | — |
| Verification | gemini-2.5-flash-lite | llama-3.3-70b-versatile | — |
| Summarization | llama-3.3-70b-versatile | — | — |

**Why two different Llama models** — llama-3.1-8b-instant is used for synthesis (speed matters, task is straightforward). llama-3.3-70b-versatile is used for decision, verification and summarization where reasoning quality and fact preservation matter more than raw speed.

---

## 🔒 Architectural Guarantees

- Every answer is explicitly verified
- Hallucinations are never returned
- Retries are bounded and observable
- Tool usage is controlled and intentional
- Memory context is always passed to decision and verification
- Execution flow is fully inspectable

There are no hidden retries, no silent fallbacks and no implicit state.

---

## 📊 Observability

For every query, the agent tracks:

- Routing decision and reason
- Model used for decision
- Search query rewrite (if applicable)
- Failure type (if any)
- Retry count
- Confidence score
- End-to-end latency (ms)

---

## 🖥️ User Interface

The frontend is implemented using **Streamlit** and manages session-level memory state.

**UI responsibilities**
- Render chat history
- Maintain `memory` in session state (summary + recent_turns)
- Append each turn to recent_turns after every response
- Trigger summarization every 4 turns
- Pass memory into `run_agent` on every call

**UI does NOT handle** — decision logic, tool handling, model routing or verification

---

## 🧠 Agent Implementations

### 1️⃣ Baseline Agent

**Purpose** - Demonstrate core agent logic with minimal complexity

- Linear, single-pass execution
- Decision → (optional search) → answer
- No verification, no retries, no memory
- Easy to understand and reason about
- Useful as a learning and comparison baseline

### 2️⃣ LangGraph Agent (Production-Oriented)

**Purpose** - Demonstrate a robust, verifiable, memory-aware agent workflow

Key characteristics:
- Explicit graph-based orchestration using LangGraph
- Hybrid short-term memory - sliding window + periodic summarization
- Memory context passed into decision and verification nodes
- Search query rewriting for focused retrieval
- Separate nodes for decision, search, synthesis and verification
- Verification layer with conversational input detection, grounding, hallucination, routing and format checks
- Bounded retries to avoid infinite loops
- Immediate abort on hallucination
- Failure-type classification with distinct types per failure source
- Confidence and latency attached to every execution
- Multi-provider model fallback - Gemini primary, Groq/Llama fallback

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/pratiksha-dhavane/ai_agent_chatbot.git
cd ai_agent_chatbot
```

### 2. Create and activate a virtual environment
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
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
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

- Demonstrate real-world AI agent design with memory
- Keep execution flow explicit and inspectable
- Show how verification, safety and memory can be added incrementally
- Serve as a portfolio-quality reference for agent architectures

The baseline agent stays intentionally simple, while the LangGraph agent illustrates how production concerns (verification, retries, safety, memory) can be layered on cleanly.

---

## 📝 Notes

- The agent is **stateless within each graph execution** - memory is managed externally in Streamlit session state and passed in at the start of each run
- No user data is persisted beyond the active browser session
- External dependencies are kept minimal and explicit
- Verification logic exists only in the LangGraph agent
- This project is intended for learning, experimentation and portfolio use

---

## 👩‍💻 Author

**Pratiksha Dhavane** 
Data Scientist | Generative AI Practitioner