memory_summary_prompt = """
You are maintaining a factual memory profile of the user based on their conversation.

Existing memory:
{existing_summary}

New conversation (Latest First):
{conversation}

RULES:
- Extract and preserve ALL key facts the user has shared about themselves.
- If a fact is updated (e.g. favourite language changed), overwrite the old value with the new one.
- Build on existing memory — do NOT drop facts that were in the previous summary unless they were explicitly updated.
- Write as a concise factual profile, not a conversation summary.
- Do NOT summarize what topics were discussed.
- Do NOT use bullet points.
- Do NOT infer anything not explicitly stated.

Updated memory profile:
"""