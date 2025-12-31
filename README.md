# AI Agent Chatbot

This project implements a production-oriented AI agent that dynamically routes user queries between direct LLM responses and external search tools. It focuses on reliability, explicit control flow, and model fallback which is key challenges in real-world agentic systems.

---

## 🚀 Key Features

This repository contains an **AI agent chatbot** implemented in two variants:

- **Baseline Agent** – a simple, linear implementation  
- **LangGraph Agent** – a graph-based implementation with verification, retries, and safety controls  

Both agents use **Google Gemini models** and a **Streamlit-based chat interface**.  
They share the same prompts, models, and tools, the difference lies in **how execution flow, verification, and recovery are handled**.

The goal of this project is to demonstrate **production-oriented agent design principles** with **explicit control flow**, **defensive handling**, and **minimal hidden abstractions**.

---

## 🧭 Agent Execution Graph & Architecture

The LangGraph-based agent is implemented as an **explicit control-flow execution graph**.  
This graph defines *how a single user query moves through the system*, including decision-making,
tool usage, verification, retries, and termination.

> The graph does **not** represent a neural network or model internals.  
> It represents **deterministic orchestration logic** for a stateless AI agent.

Each query enters the graph, flows through a bounded set of nodes, and terminates with either a verified answer or a safe abort.

---

## 🔁 Execution Flow Overview

At a high level, the agent follows this pattern:

1. Accept user input
2. Decide how the query should be handled
3. Generate an answer (with or without search)
4. Verify the answer
5. Either return, retry with more context, or abort safely

There is **no hidden control flow** and **no implicit retries**. Every transition is explicit in the graph.

---

## 🧩 Node-by-Node Architectural Breakdown

### `__start__` - Query Ingress

**Role**
- Entry point for every user query

**Responsibilities**
- Accept raw user input
- Initialize agent state

**State initialized**
- `user_input`
- `retry_count = 0`
- `search_results = None`
- `candidate_answer = None`

This node performs no logic. It exists to make the execution lifecycle explicit and inspectable.

---

### `decide` - Routing & Risk Assessment

**Role**
- Central decision-making node

**Purpose**
- Decide *how* the query should be processed
- Not responsible for answering the query

**Responsibilities**
- Classify query intent
- Estimate hallucination risk
- Decide whether external search is required

**Possible routing outcomes**
- Route directly to `answer`
- Route to `search` (via retry path)

This node enforces a key design principle:

> Execution flow is determined explicitly by the agent logic, not implicitly by the LLM.

---

### `answer` - Direct LLM Generation

**When executed**
- Query is assessed as low-risk
- No external or time-sensitive information is required

**Responsibilities**
- Call the LLM with the user query
- Generate a candidate answer

**What it does NOT do**
- No verification
- No safety judgment
- No retries

Answer generation and answer validation are intentionally separated to avoid mixing responsibilities.

---

### `verify` - Validation & Safety Gate

**Role**
- Final authority before any answer is returned to the user

**Responsibilities**
- Validate correctness and safety of the generated answer

**Checks performed**
- Grounding against search results (if available)
- Hallucination detection
- Output format validation
- Routing correctness

**Possible outcomes**
- `pass` → answer is accepted
- `retry` → recovery attempt required (bounded)
- `abort` → execution terminated immediately

No answer can reach the user without passing through this node.

---

### `abort` - Immediate Safety Termination

**When triggered**
- Hallucination detected
- Critical safety violation

**Behavior**
- Stops execution immediately
- Returns a safe failure response

**Design rule**
- Hallucinations are **never retried**

This fail-fast behavior is intentional and mirrors real production safety requirements.

---

### `retry` → `increment_retry` - Controlled Recovery

**When triggered**
- Non-critical verification failures
  (e.g. weak grounding, insufficient context)

**Responsibilities**
- Increment retry counter
- Enforce retry limits
- Redirect execution to `search`

Retries are:
- Explicit
- Bounded
- Observable

This prevents silent loops and uncontrolled cost escalation.

---

### `search` - External Information Retrieval

**Role**
- Fetch real-world or time-sensitive information

**Tool used**
- DuckDuckGo Search

**Output**
- Structured search results added to agent state

This node exists only when the agent determines that internal model knowledge is insufficient or risky.

---

### `synthesize` - Answer Synthesis with Context

**Role**
- Combine user query and retrieved search results

**Responsibilities**
- Generate a grounded, context-aware answer
- Use retrieved data as supporting evidence

The output of this node is always sent back to `verify` before being returned to the user.

---

### `__end__` - Execution Termination

**When reached**
- Verification passes
- Or execution is aborted

**Responsibilities**
- Return final response
- Attach metadata (confidence, latency, retry count)

This marks the end of a single, stateless execution cycle.

---

## 🔒 Architectural Guarantees

This graph guarantees that:

- Every answer is explicitly verified
- Hallucinations are never returned
- Retries are bounded and observable
- Tool usage is controlled and intentional
- Execution flow is fully inspectable

There are no hidden retries, no silent fallbacks, and no implicit state.

---

## 🧠 Stateless by Design

The agent is intentionally **stateless**:

- No conversation memory
- No user history persistence
- Each query is processed independently

This simplifies reasoning, debugging, and production deployment.

---

## 🎯 Why a Graph-Based Design?

Using a graph instead of a linear chain enables:

- Clear separation of responsibilities
- Safe branching and recovery paths
- Easier extensibility (new nodes, tools, or checks)
- Production-grade observability

The graph exists to make behavior explicit, not to add complexity.

---

## 🚧 What This Agent Is Not (By Design)

- Not autonomous
- Not self-planning
- Not self-improving
- Not stateful across queries

Those capabilities can be added later, but are intentionally out of scope for this implementation.

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

This implementation shows how safety, reliability, and observability can be layered on top of a basic agent without changing the core logic.

---

## 📊 Observability

For every query, the agent tracks:

- Routing decision and reason
- Model used
- Failure type (if any)
- Retry count
- Confidence score
- End-to-end latency (ms)

This makes every execution debuggable, explainable, and suitable for production diagnostics.

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
