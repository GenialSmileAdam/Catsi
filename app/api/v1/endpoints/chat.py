
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_ollama import ChatOllama
from app.core.config import settings
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatResponse, ChatRequest
from app.services.reranker import rerank_chunks
from app.services.vector_store import multi_query_retrieval
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    user_message = chat_request.message

    # ---- RAG Step 1:Multi-query Retrieval for retrieving relevant document chunks ----
    candidate_chunks = await multi_query_retrieval(user_message, top_k_per_query=5, num_queries=3)

    #----- RAG step 2: Rerank the chunks-----
    reranked_chunks= await rerank_chunks(user_message, candidate_chunks)

    if not reranked_chunks:
        # No documents? Just answer without context.
        context_text = ""
    else:
        context_text = "\n\n".join([f"---\n{chunk}" for chunk in reranked_chunks])

    # ---- RAG Step 3: Build the prompt ----
    system_prompt = (
        "You are a helpful assistant. Use the following pieces of context to answer the user's question.\n"
        "If the answer is not in the context, say you don't know. Do not make up information.\n\n"
        f"Context:\n{context_text}"
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    # ---- RAG Step 4: Call the LLM ----
    llm = ChatOllama(
        model=settings.CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7,
    )
    try:
        ai_message = await llm.ainvoke(messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    # Return the answer + the sources so you can see what was retrieved
    return ChatResponse(
        response=ai_message.content,
        sources=reranked_chunks,
    )