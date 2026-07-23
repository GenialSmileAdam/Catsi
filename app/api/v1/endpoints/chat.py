
from fastapi import APIRouter, Depends, HTTPException, status, Request
from langchain_ollama import ChatOllama
from app.core.config import settings
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatResponse, ChatRequest
from app.services.reranker import rerank_chunks
from app.services.vector_store import multi_query_retrieval
from fastapi.responses import StreamingResponse
import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.rate_limiter import limiter, user_limiter
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
@user_limiter.limit("20/minute")
async def chat(
    request:Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"User {current_user.id} asked: '{chat_request.message[:80]}...'")
    user_message = chat_request.message

    # ---- RAG Step 1:Multi-query Retrieval for retrieving relevant document chunks ----
    start = time.time()
    candidate_chunks = await multi_query_retrieval(user_message, top_k_per_query=5, num_queries=3)
    t1 = time.time()

    logger.debug(f"Multi-query retrieval took {t1 - start:.2f}s")

    # Remove duplicate texts (keep order of first occurrence)
    seen = set()
    unique_candidates = []
    for chunk in candidate_chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique_candidates.append(chunk)

    #----- RAG step 2: Rerank the chunks-----
    reranked_chunks= await rerank_chunks(user_message, unique_candidates, top_k = 4)
    t2 = time.time()
    logger.debug(f"Reranking took {t2 - t1:.2f}s")

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

    t3 = time.time()
    logger.debug(f"LLM generation took {t3 - t2:.2f}s")

    # Return the answer + the sources so you can see what was retrieved
    logger.info(f"Returning answer with {len(reranked_chunks)} sources")
    return ChatResponse(
        response=ai_message.content,
        sources=reranked_chunks,
    )



@router.post("/stream")
@limiter.limit("10/minute")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    user_message = chat_request.message
    logger.info(f"User {current_user.id} streaming: '{user_message[:80]}...'")

    # ---- Step 1: Retrieval & reranking (unchanged) ----
    candidate_chunks = await multi_query_retrieval(
        user_message,
        top_k_per_query=5,
        num_queries=3,
    )
    # deduplicate
    seen = set()
    unique = []
    for chunk in candidate_chunks:
        if chunk not in seen:
            seen.add(chunk)
            unique.append(chunk)
    final_chunks = await rerank_chunks(user_message, unique, top_k=4)

    if final_chunks:
        context_text = "\n\n".join([f"---\n{chunk}" for chunk in final_chunks])
    else:
        context_text = ""

    system_prompt = (
        "You are a helpful assistant. Use the following pieces of context to answer the user's question.\n"
        "If the answer is not in the context, say you don't know. Do not make up information.\n\n"
        f"Context:\n{context_text}"
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    # ---- Step 2: LLM streaming ----
    llm = ChatOllama(
        model=settings.CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7,
    )

    # We'll create an async generator that yields SSE chunks
    async def token_generator():
        try:
            logger.debug("LLM streaming started")
            async for chunk in llm.astream(messages):
                # Each chunk is an AIMessageChunk; extract the text delta
                if chunk.content:
                    # Format as SSE: "data: <token>\n\n"
                    # For JSON compatibility, you can also send a JSON object
                    data = json.dumps({"token": chunk.content})
                    yield f"data: {data}\n\n"
            # Send final message with sources
            final_data = json.dumps({"done": True, "sources": final_chunks})
            yield f"data: {final_data}\n\n"
            logger.debug("LLM streaming finished")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},  # disable nginx buffering if behind reverse proxy
    )