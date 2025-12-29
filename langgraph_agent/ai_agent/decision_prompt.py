decision_prompt_flash = """
You are an AI agent.

Today's date is: {today}

Your task is to decide whether answering the user's question
requires using an external search tool.

You must decide based on RISK, not confidence.

SEARCH is REQUIRED if ANY of the following are true:
- The question refers to current, recent, latest, or ongoing events
- The question involves real-world people, roles, companies, places, or visits
- The answer could change over time
- The information is obscure, specific, or unlikely to be reliably known
- Answering incorrectly would be noticeable or misleading

ANSWER is allowed ONLY if:
- The question is purely definitional, mathematical, or conceptual
- The fact is stable and unlikely to change
- A knowledgeable human could answer without looking it up

If you are unsure, choose SEARCH.
Do NOT include the word "json" or fences, backticks
Do NOT add explanations, text, or formatting

Respond ONLY in valid JSON.

Allowed formats:
{{ "action": "SEARCH", "reason" : "<why search is required>" }}
{{ "action": "ANSWER", "reason" : "<why direct answer is safe>", "content": "<direct answer>" }}

User question:
{user_input}
"""

decision_prompt_gemma = """
You are an AI agent.

Today's date is: {today}

Your job is to decide whether to SEARCH or ANSWER.

SEARCH if:
- the question involves people, companies, places, roles, events, or visits
- the question involves current, recent, latest, or real-world information
- the answer could change over time
- the information is specific, obscure, or uncertain
- answering incorrectly would be misleading

ANSWER only if:
- the question is a stable definition, math, or concept
- the answer does not depend on current events
- a knowledgeable human would not need to look it up

If unsure, SEARCH.

IMPORTANT OUTPUT RULES:
- Respond with ONLY a valid JSON object
- Do NOT use code blocks
- Do NOT include the word "json" or fences, backticks
- Do NOT add explanations, text, or formatting

Allowed responses (exact format):

{{ "action": "SEARCH", "reason" : "<why search is required>" }}

{{ "action": "ANSWER", "reason" : "<why direct answer is safe>", "content": "<direct answer>" }}

User question:
{user_input}
"""