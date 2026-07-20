import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

async def generate_multi_queries(question: str, num_queries: int = 3) -> list[str]:
    """
    Ask the LLM to generate alternative phrasings of the same question.
    Returns the original question plus the generated ones.
    """
    system_prompt = (
        "You are a helpful assistant. Your task is to generate alternative versions "
        "of a user's question to improve document retrieval. "
        "Output each question on a new line. Do NOT number them, do NOT say 'Version 1', "
        "just output the questions themselves, one per line."
    )
    user_message = f"User question: {question}\nGenerate {num_queries} alternative questions."

    llm = ChatOllama(
        model=settings.CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.3,  # lower temperature for focused variations
    )
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    raw_text = response.content.strip()

    # Clean each line: remove any leading "Version X:", numbering, etc.
    lines = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove common prefixes like "1.", "Version 1:", "Question 1:", etc.
        import re
        # Remove leading numbers, dots, colons, and word "Version" patterns
        cleaned = re.sub(r'^(?:\d+[.)]\s*|Version\s*\d+:\s*|Question\s*\d+:\s*)', '', line).strip()
        if cleaned:
            lines.append(cleaned)

    # Include the original question
    all_queries = [question] + lines[:num_queries]
    return all_queries