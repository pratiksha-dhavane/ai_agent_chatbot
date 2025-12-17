import json
from datetime import date
import google.generativeai as genai

import os
import sys
sys.path.append(os.path.dirname(__file__))

from ai_agent.decision_prompt import decision_prompt_flash, decision_prompt_gemma
from ai_agent.synthesis_prompt import synthesis_prompt_flash, synthesis_prompt_gemma

from langchain_community.tools import DuckDuckGoSearchRun

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is not set....")

genai.configure(api_key=api_key)

# Intitializing the models
flash_model = genai.GenerativeModel("gemini-2.5-flash")
flash_lite_model = genai.GenerativeModel("gemini-2.5-flash-lite")
gemma_model = genai.GenerativeModel("gemma-3-12b-it")

def decide_model_with_fallback(user_input: str):
    """
    This function gives decision to whether use tool or answer.
    """
    today = date.today().isoformat()

    models = [
        ("flash", flash_model, decision_prompt_flash),
        ("flash_lite", flash_lite_model, decision_prompt_flash),
        ("gemma", gemma_model, decision_prompt_gemma)
    ]

    last_error = None

    for name, model, decision_prompt in models:
        try:
            # build the prompt
            prompt = decision_prompt.format(user_input=user_input,today=today)

            # Call the model
            response = model.generate_content(prompt)

        except Exception as e:
            # Model Failed
            last_error = e
            print(f"[WARN] Decision failed on Model {name} : {e}")

        else:
            # Model succeeded
            return response.text.strip(), name 
        
        finally:
            pass 

    # If the loop is exited, ALL models failed
    raise RuntimeError(f"Decision failed on all models. Last error: {last_error}")

def parse_decision_safe(decision_text: str):
    """
    This function parses the JSON decision from LLM
    """
    cleaned = decision_text.strip().replace("```json", "").replace("```", "").replace("json", "").strip()

    try:
        return json.loads(cleaned)
    except Exception as e:
        # Conservative fallback
        print(e)
        return { "action" : "SEARCH" }

search_tool = DuckDuckGoSearchRun() 

def synthesize_with_fallback(user_input: str, tool_output: str):
    """
    This function returns the answer based on retrived results from tool
    """

    today = date.today().isoformat()

    models = [
        ("flash", flash_model, synthesis_prompt_flash),
        ("flash_lite", flash_lite_model, synthesis_prompt_flash),
        ("gemma", gemma_model, synthesis_prompt_gemma)
    ]

    last_error = None

    for name, model, _prompt in models:
        try:
            # build the prompt
            prompt = _prompt.format( user_input=user_input,
                                     tool_output=tool_output,
                                     today=today )

            # Call the model
            response = model.generate_content(prompt)

        except Exception as e:
            # Model Failed
            last_error = e
            print(f"[WARN] Decision failed on Model {name} : {e}")

        else:
            # Model succeeded
            return response.text.strip()
        
        finally:
            pass 

    # If the loop is exited, ALL models failed
    raise RuntimeError(f"Synthesis failed on all models. Last error: {last_error}")
    
def run_agent(user_input: str):
    """
    This is final function which wrapes all imp functions.
    """
    decision_text, decision_model = decide_model_with_fallback(user_input)
    decision = parse_decision_safe(decision_text)

    print("Decision:", decision)
    print("Decision Model:", decision_model)

    if decision["action"] == "SEARCH": 
        print("Using the tool....") 
        search_result = search_tool.run(user_input) 
        # print(search_result)
        return synthesize_with_fallback(user_input, search_result) 
    
    elif decision["action"] == "ANSWER": 
        return decision["content"] 
    
    else: 
        raise ValueError(f"Unknown action: {decision}")