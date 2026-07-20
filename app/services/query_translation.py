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
     f"You are an AI language model assistant.Your task is to generate {num_queries}"
    "different versions of the given user question to retrieve relevant documents from a vector"
    "database.By generating multiple perspectives on the user question, your goal is to help"
    " the user overcome some of the limitations of the distance-based similarity search."
    " Provide these alternative questions separated by newlines."
    )
    user_message = f"Original question: {question}"

    llm = ChatOllama(
        model=settings.CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.3,  # lower temperature for focused variations
    )
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    # The response should be one question per line
    lines = [line.strip() for line in response.content.splitlines() if line.strip()]
    # Include the original question
    all_queries = [question] + lines[:num_queries]
    return all_queries