import asyncio
from sentence_transformers import CrossEncoder
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

# We'll load the model once, lazily.
_reranker_model = None

def get_reranker_model() -> CrossEncoder:
    """Return the shared CrossEncoder model, loading it if necessary."""
    global _reranker_model
    if _reranker_model is None:
        # This model is a good balance of speed and accuracy.
        _reranker_model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512,  # max tokens for query+chunk
            device="cuda"
        )
    return _reranker_model

@traceable()
async def rerank_chunks(query: str, chunks: list[str], top_k: int = 4) -> list[str]:
    """
    Given a query and a list of chunk texts, use the cross-encoder to
    compute relevance scores, sort chunks by score, and return the top_k.
    """
    logger.info(f"Reranking {len(chunks)} chunks for query: '{query[:80]}...'")
    if not chunks:
        return []

    model = get_reranker_model()
    # Build (query, chunk) pairs for the cross-encoder
    pairs = [(query, chunk) for chunk in chunks]

    # model.predict is synchronous (CPU-bound). We run it in a thread pool.
    scores = await asyncio.to_thread(model.predict, pairs)

    # Combine chunk with its score, sort descending, take top_k
    scored_chunks = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )

    top_chunks = [chunk for chunk, score in scored_chunks[:top_k]]


    logger.debug(f"Scored chunks: {scored_chunks}")
    logger.debug(f"Reranked top scores: {top_chunks}")
    return top_chunks