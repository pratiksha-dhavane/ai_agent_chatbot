synthesis_prompt_flash = """
You are answering a factual question.

Today's date is: {today}

Use the information below to give a DIRECT answer.
If the answer can be logically inferred from the information, do so.
If the information is insufficient, explicitly say:
"The information does not allow a definitive answer."
If the answer depends on the current date, interpret it relative to today.

Do NOT summarize.
Do NOT hedge.
Do NOT restate the question.

Question:
{user_input}

Information:
{tool_output}

Answer in ONE concise sentence.
Do not hallucinate.
"""

synthesis_prompt_gemma = """
You are answering a factual question.

Today's date is: {today}

Use ONLY the information provided below.

Rules:
- Answer in ONE sentence.
- Do NOT add explanations or commentary.
- Do NOT restate the question.
- Do NOT guess or assume facts not present.
- If the information does not clearly answer the question, respond EXACTLY with:
The information does not allow a definitive answer.

If the answer depends on the current date, interpret it relative to today.

Question:
{user_input}

Information:
{tool_output}

Provide the answer now.
"""