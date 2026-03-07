from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

import json
import time
from datetime import date 
import google.generativeai as genai
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
from groq import Groq
import os
import sys
sys.path.append(os.path.dirname(__file__))

from ai_agent.decision_prompt import decision_prompt_flash
from ai_agent.synthesis_prompt import synthesis_prompt_flash
from ai_agent.verify_prompt import verify_prompt
from ai_agent.memory_summary_prompt import memory_summary_prompt

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set....")

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise RuntimeError("groq_api_key is not set....")

genai.configure(api_key=google_api_key)
groq_client = Groq(api_key=groq_api_key)

max_retries = 2

# Initialize the models
flash_model = genai.GenerativeModel("gemini-2.5-flash")
flash_lite_model = genai.GenerativeModel("gemini-2.5-flash-lite")
# gemma_model = genai.GenerativeModel("gemma-3-12b-it")
llama_instant = "llama-3.1-8b-instant"
llama_versatile = "llama-3.3-70b-versatile"
def groq_generate(prompt: str, model: str) -> str:
    response = groq_client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
        )
    return response.choices[0].message.content.strip()

# Failure Modes
FAILURE_TYPES = {
    "DECISION_PARSE_ERROR",
    "SEARCH_ERROR",
    "SYNTHESIS_ERROR",
    "VERIFICATION_NOT_GROUNDED",
    "VERIFICATION_HALLUCINATION",
    "VERIFICATION_LOW_CONFIDENCE",
    "VERIFICATION_ROUTING_ERROR",
    "VERIFICATION_FORMAT_ERROR"
}

class AgentState(TypedDict, total=False):
    """
    AgentState: Defines the structure of data flowing through the graph.
    """       
    user_input : str
    summary: str
    recent_turns: list[dict]    
    decision : dict 
    decision_model : str 
    route_reason : str
    search_result : str 
    final_answer : str
    verification : dict 
    retries : int
    failure_type : str 
    confidence : float 
    latency_ms : float

def decide_node(state: AgentState) -> AgentState:
    """
    Decision Node: Determines whether to use SEARCH tool or ANSWER directly.
    """

    # Extract user input from state
    user_input = state["user_input"]
    summary = state["summary"]
    recent_turns = state["recent_turns"]
    today = date.today().isoformat()

    # Model fallback chain: try flash first, then flash_lite, then gemma
    models = [
        ("flash", flash_model),
        ("flash_lite", flash_lite_model),
        ("llama", groq_generate)
    ]

    last_error = None 

    # try each model in order until one succeeds
    for name, model in models:
        try:
            # Build decision prompt
            prompt = decision_prompt_flash.format(user_input=user_input,today=today,summary=summary,recent_turns=recent_turns)

            # Call the model to get decision
            if name != "llama":
                response = model.generate_content(prompt,)
                decision_text = response.text.strip()

            else:
                decision_text = model(prompt=prompt,model=llama_versatile)

            # Parse the JSON Decision
            cleaned = decision_text.strip().replace("```json", "").replace("```", "").replace("json", "").strip()
            decision = json.loads(cleaned)
            print(f"Decision made by model: {name}")
            print(f"Routing reason: {decision.get('reason', '')  }")
            return {
                **state,
                "decision" : decision,
                "decision_model" : name,
                "route_reason" : decision.get("reason", "")  
            }
        
        except Exception as e:
            last_error = e
            # print(f"[WARN] Decision failed on model {name}: {e}") 
            continue

    # Conservative fallback: default to SEARCH action
    print(f"[ERROR] All decision models failed. Defaulting to SEARCH. Last error: {last_error}")
    return {
        **state,
        "decision": {"action": "SEARCH"},
        "decision_model": "fallback",
        "route_reason": "Decision model failed on all attempts; defaulting to SEARCH",
        "failure_type" : "DECISION_PARSE_ERROR" 
    }

search_tool = DuckDuckGoSearchRun()

def search_node(state: AgentState) -> AgentState:
    """
    Search Node: Performs web search using DuckDuckGo
    """

    # Extract user_input from state
    # user_input = state["user_input"]

    query = state.get("decision", {}).get("query", "")
    if query != "":
        user_input = query
    else:
        user_input = state.get("user_input", "")

    try:
        # Run DuckDuckGo Search
        print("[INFO] Running search tool...")
        search_result = search_tool.run(user_input)

        print(f"[SUCCESS] Search completed. Result length: {len(search_result)} chars")
        return {
            **state,
            "search_result" : search_result
        }
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return {
            **state,
            "search_result" : e,
            "failure_type" : "SEARCH_ERROR"
        }
    
def synthesis_node(state: AgentState) -> AgentState:
    """
    Synthesize Node: Generates final answer from search results.
    """

    user_input = state["user_input"]
    query = state.get("decision", {}).get("query", "")
    tool_output = state["search_result"]
    today = date.today().isoformat()

    models = [
        ("flash_lite", flash_lite_model),
        ("llama", groq_generate)
    ]
    
    last_error = None

    for name, model in models:
        try:
            prompt = synthesis_prompt_flash.format(user_input=user_input,query=query,tool_output=tool_output,today=today)

            if name != "llama":
                response = model.generate_content(prompt)
                final_answer = response.text.strip()
            
            else:
                final_answer = model(prompt=prompt,model=llama_instant)

            print(f"[SUCCESS] Synthesis completed by model: {name}")
            return {
                **state,
                "final_answer" : final_answer
            }

        except Exception as e:
            last_error = e
            print(f"[WARN] Synthesis failed on model {name}: {e}")
            continue
    
    # If we reach here, ALL models failed
    error_msg = f"Synthesis failed on all models. Last error: {last_error}"
    # print(f"[ERROR] {error_msg}")
    return {
        **state,
        "final_answer": error_msg,
        "failure_type" : "SYNTHESIS_ERROR"
    }

def answer_node(state: AgentState) -> AgentState:
    """
    Answer Node: Returns direct answer without search.
    """

    decision = state["decision"]
    answer_content = decision.get("content","No answer provided")

    # Return updated state with final answer
    print(f"[SUCCESS] Direct answer provided (no search needed)")
    return {
        **state, 
        "final_answer": answer_content  
    }  

def should_search(state: AgentState) -> Literal["search", "answer"]:
    """
    Routing Function: Decides which path to take after decision node.
    """
    decision = state.get("decision", {})
    action = decision.get("action", "SEARCH")  # Default to search if missing 

    if action == "SEARCH":
        return "search"
    else:
        return "answer"

def verify(state: AgentState) -> AgentState:
    """
    Checks whether the final answer is safe, grounded, and correctly routed.
    """

    user_input = state["user_input"]
    query = state.get("decision", {}).get("query", "")
    final_answer = state.get("final_answer","")
    search_result = state.get("search_result","")
    summary = state.get("summary","")
    recent_turns = state.get("recent_turns","")
    # decision = state.get("decision", {})

    today = date.today().isoformat()

    search_context = (
        search_result.strip()
        if search_result and search_result.strip()
        else "NO SEARCH WAS USED"
    )

    print(final_answer)
    prompt = verify_prompt.format(today=today,
                                  user_input=user_input,
                                  query=query,
                                  search_result=search_context,
                                  final_answer=final_answer,
                                  summary=summary,
                                  recent_turns=recent_turns)
    print(prompt)
    verify_models = [
        ("flash_lite", flash_lite_model),
        ("llama", groq_generate)
    ]

    try:
        for name, model in verify_models:
            try:

                if name != "llama":
                    response = model.generate_content(prompt)
                    verfiy_text = response.text.strip()
                else:
                    verfiy_text = model(prompt=prompt,model=llama_versatile)

                cleaned = (
                    verfiy_text
                    .replace("```json", "")
                    .replace("```", "")
                    .replace("json", "")
                    .strip()
                )

                verdict = json.loads(cleaned)

                print(f"Verdict: {verdict.get('verdict','')} made by model: {name}")

                if verdict.get("verdict") == "pass":
                    return {
                        **state,
                        "verification" : verdict,
                        "failure_type" : None,
                        "confidence": 0.9 
                    }

                failure_type = None

                if verdict.get("verdict") == "fail":
                    reason = verdict.get("reason","")
                    reasons = [r.strip() for r in reason.split("|")] 

                    if "hallucination" in reasons:
                        failure_type = "VERIFICATION_HALLUCINATION"
                    elif "grounding" in reasons:
                        failure_type = "VERIFICATION_NOT_GROUNDED"
                    elif "routing" in reasons:
                        failure_type = "VERIFICATION_ROUTING_ERROR"
                    elif "format" in reasons:
                        failure_type = "VERIFICATION_FORMAT_ERROR"
                    else:
                        failure_type = "VERIFICATION_NOT_GROUNDED"

                if failure_type == "VERIFICATION_HALLUCINATION":
                    confidence = 0.1
                elif failure_type == "VERIFICATION_NOT_GROUNDED":
                    confidence = 0.4
                else:
                    confidence = 0.3

                print(f"Verification failure type: {failure_type} with confidence {confidence}")  

                return {
                    **state,
                    "verification" : verdict,
                    "failure_type" : failure_type,
                    "confidence" : confidence
                }
            
            except Exception as e:
                # print(f"Verification failed on model: {e}")
                continue
        
    except Exception as e:
        # Conservative default: fail verification
        print(f"[ERROR] Verification failed: {e}")
        return {
            **state,
            "verification": {
                "verdict": "fail",
                "reason": "format"
            },
            "failure_type": "VERIFICATION_FORMAT_ERROR",
            "confidence" : 0.3
        }

def verification_router(state: AgentState) -> Literal["pass","retry","stop","abort"]:
    """
    Routes based on verification result.
    """

    verification = state["verification"]
    retries = state.get("retries", 0)
    failure_type = state.get("failure_type", "")

    # Success path
    if verification.get("verdict") == "pass":
        return "pass"
    
    # Hard stop on halluciations
    if failure_type == "VERIFICATION_HALLUCINATION":
        return "abort"
    
    # Failure path
    if retries < max_retries:
        return "retry"
    
    # Retries exhausted
    return "stop"

def increment_retry(state : AgentState) -> AgentState:
    return {
        **state,
        "retries" : state.get("retries",0) + 1
    }

def abort_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer" : "I can't reliably answer this question based on verified information. Please try rephrasing or check an authoritative source."
    }

# def is_followup(user_input):
#     """
#     Simple function to detect if user question is follow up or not. 
#     """

#     markers = [
#         "it", "this", "that", "they",
#         "what about", "and", "also",
#         "its", "their"
#     ]
#     return any(m in user_input.lower() for m in markers) 

def update_summary(existing_summary, recent_turns):
    """
    This function summarizes last few conversations with user.
    """

    conversation = ""

    for turn in recent_turns:
        for k, v in turn.items():
            conversation += f"{k.capitalize()} : {v}\n"

    prompt = memory_summary_prompt.format(existing_summary=existing_summary,conversation=conversation)

    return groq_generate(prompt=prompt,model=llama_versatile)

# def should_summarize(recent_turns, max_turns):
#     """
#     This function decides whether to summarize the conversation.
#     """
#     return len(recent_turns) >= max_turns # and not is_followup(user_input)

def create_agent_graph():
    """
    Creates and compiles the LangGraph agent workflow.
    """

    # Initialize the graph with our state type
    workflow = StateGraph(AgentState)

    # Adding nodes to the graph
    workflow.add_node("decide", decide_node)
    workflow.add_node("search", search_node)
    workflow.add_node("synthesize", synthesis_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("verify", verify)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_node("abort", abort_node)

    # Setting the entry point
    workflow.set_entry_point("decide")

    # Add conditional edges
    workflow.add_conditional_edges("decide", 
                                   should_search, 
                                   {
                                       "search" : "search",
                                       "answer" : "answer"
                                   })
    
    # Add remaining edges
    workflow.add_edge("search", "synthesize")
    workflow.add_edge("synthesize", "verify")
    workflow.add_edge("answer", "verify")

    # Verification routing
    workflow.add_conditional_edges(
        "verify",
        verification_router,
        {
            "pass" : END,
            "retry" : "increment_retry",
            "stop" : "abort",
            "abort" : "abort"
        }
    )

    workflow.add_edge("increment_retry", "search")
    workflow.add_edge("abort", END)

    # Compile the graph
    return workflow.compile() 

agent_graph = create_agent_graph()

def run_agent(user_input: str, memory: dict) -> str:
    """
    Main function to run the LangGraph agent.
    """

    summary = memory.get("summary", "")
    recent_turns = memory.get("recent_turns", [])

    initial_state = {
        "user_input": user_input,
        "summary": summary,
        "recent_turns": recent_turns,
        "decision": {},
        "decision_model": "",
        "route_reason": None,
        "search_result": None,
        "final_answer": None,
        "verification": {},
        "retries": 0,
        "failure_type": None,
        "confidence": None,
        "latency_ms": None
    }

    start_time = time.time()
    try:
        result = agent_graph.invoke(initial_state)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        result["latency_ms"] = latency_ms

        # Extract results for logging 
        decision = result.get("decision", {})
        decision_model = result.get("decision_model", "Unknown")
        final_answer = result.get("final_answer", "No answer generated")

        print(result) 

        # Log execution summary
        print("\n" + "-"*60)
        print("Execution Summary:")
        print(f"  • Decision: {decision.get('action', 'N/A')}")
        print(f"  • Model Used: {decision_model}")
        print(f"  • Answer Length: {len(final_answer)} characters")
        print("-"*60 + "\n")

        return final_answer
    
    except Exception as e:

        # Handle any errors during execution
        error_msg = f"Agent execution failed: {str(e)}"
        print(error_msg)
        return "No answer provided"