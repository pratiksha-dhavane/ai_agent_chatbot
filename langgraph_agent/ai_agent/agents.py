from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

import json
import time
from datetime import date 
import google.generativeai as genai
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(__file__))

from ai_agent.decision_prompt import decision_prompt_flash, decision_prompt_gemma
from ai_agent.synthesis_prompt import synthesis_prompt_flash, synthesis_prompt_gemma
from ai_agent.verify_prompt import verify_prompt

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set....")

genai.configure(api_key=api_key)

max_retries = 2

# Initialize the models
flash_model = genai.GenerativeModel("gemini-2.5-flash")
flash_lite_model = genai.GenerativeModel("gemini-2.5-flash-lite")
gemma_model = genai.GenerativeModel("gemma-3-12b-it")

# Failure Modes
FAILURE_TYPES = {
    "DECISION_PARSE_ERROR",
    "SEARCH_ERROR",
    "SYNTHESIS_ERROR",
    "VERIFICATION_NOT_GROUNDED",
    "VERIFICATION_HALLUCINATION",
    "VERIFICATION_LOW_CONFIDENCE"
}

class AgentState(TypedDict):
    """
    AgentState: Defines the structure of data flowing through the graph.
    """       
    user_input : str
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
    today = date.today().isoformat()

    # Model fallback chain: try flash first, then flash_lite, then gemma
    models = [
        ("flash", flash_model, decision_prompt_flash),
        ("flash_lite", flash_lite_model, decision_prompt_flash),
        ("gemma", gemma_model, decision_prompt_gemma)
    ]

    last_error = None 

    # try each model in order until one succeeds
    for name, model, decision_prompt in models:
        try:
            # Build decision prompt
            prompt = decision_prompt.format(user_input=user_input,today=today)

            # Call the model to get decision
            response = model.generate_content(prompt)
            decision_text = response.text.strip()

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
            print(f"[WARN] Decision failed on model {name}: {e}") 
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
    user_input = state["user_input"]

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
    tool_output = state["search_result"]
    today = date.today().isoformat()

    models = [
        ("flash", flash_model, synthesis_prompt_flash),
        ("flash_lite", flash_lite_model, synthesis_prompt_flash),
        ("gemma", gemma_model, synthesis_prompt_gemma)
    ]
    
    last_error = None

    for name, model, systhesis_prompt in models:
        try:
            prompt = systhesis_prompt.format(user_input=user_input,tool_output=tool_output,today=today)

            response = model.generate_content(prompt)
            final_answer = response.text.strip()

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
    print(f"[ERROR] {error_msg}")
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
    final_answer = state.get("final_answer","")
    search_result = state.get("search_result","")
    decision = state.get("decision", {})

    today = date.today().isoformat()

    search_context = (
        search_result.strip()
        if search_result and search_result.strip()
        else "NO SEARCH WAS USED"
    )

    prompt = verify_prompt.format(today=today,user_input=user_input,search_result=search_context,final_answer=final_answer)

    verify_models = [
        ("flash_lite", flash_lite_model),
        ("gemma", gemma_model)
    ]

    try:
        for name, model in verify_models:
            try:
                response = model.generate_content(prompt)
                verfiy_text = response.text.strip()

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
                        failure_type = "DECISION_PARSE_ERROR"
                    elif "format" in reasons:
                        failure_type = "SYNTHESIS_ERROR"
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
                print(f"Verification failed on model: {e}")
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
            "failure_type": "SYNTHESIS_ERROR",
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
            "stop" : END,
            "abort" : "abort"
        }
    )

    workflow.add_edge("increment_retry", "search")
    workflow.add_edge("abort", END)

    # Compile the graph
    return workflow.compile() 

agent_graph = create_agent_graph()

def run_agent(user_input: str) -> str:
    """
    Main function to run the LangGraph agent.
    """

    initial_state = {
        "user_input": user_input,
        "decision": {},
        "decision_model": "",
        "route_reason": None,
        "search_result": None,
        "final_answer": None,
        "verification": None,
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