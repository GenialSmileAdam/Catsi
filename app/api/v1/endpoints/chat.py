import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatResponse, ChatRequest


router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Simple chat endpoint. Sends the user's message to the Ollama LLM
    and returns the generated reply.
    """
    # Create the LangChain ChatOllama instance for our configured model
    llm = ChatOllama(
        model=settings.CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7,
    )

    # The model expects a list of messages. We'll only send the user message.
    messages = [HumanMessage(content=chat_request.message)]

    try:
        ai_message = await asyncio.to_thread(llm.invoke, messages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM call failed: {str(e)}",
        )

    # Extract the text content from the AI response
    return ChatResponse(response=ai_message.content)