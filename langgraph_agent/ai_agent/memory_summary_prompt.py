memory_summary_prompt = """
You are updating a running summary of a conversation.

Current summary:
{existing_summary}

New conversation (Latest First):
{conversation}

IMPORTANT RULES:
- Summarize only what the user is trying to learn or ask in short paragraph.
- Keep summary brief without loosing any previous context. 
- Do NOT include answers.
- Do NOT include explanations.
- Do NOT infer facts.
"""