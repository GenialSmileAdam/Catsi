import asyncio
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_ollama import OllamaEmbeddings
from app.core.config import settings
from app.services.query_translation import generate_multi_queries
from langsmith import traceable
# Global client and collection (initialized lazily)
_client = None
_collection = None

def get_chroma_client():
    """Return a persistent ChromaDB client (singleton)."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client

def get_or_create_collection():
    """Get or create the ChromaDB collection for our documents."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
    return _collection


async def embed_and_store(
    document_id: int,
    chunks: list[str],
) -> None:
    """
    Generate embeddings for each chunk using Ollama and store them in ChromaDB.
    The chunks are associated with the document_id for later retrieval/filtering.
    """
    if not chunks:
        return

    # Remove old chunks for this document to prevent duplicates
    await delete_document_chunks(document_id)

    # Use LangChain's OllamaEmbeddings wrapper (it handles the API calls)
    # This is sync, so we call in thread.
    embeddings_model = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    # Generate embeddings (this may be a long-running task)
    embeddings = await embeddings_model.aembed_documents(chunks)

    # Prepare metadata for each chunk
    metadata = [{"document_id": document_id} for _ in chunks]
    ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]

    # Add to Chroma collection (also sync)
    collection = get_or_create_collection()
    await asyncio.to_thread(
        collection.add,
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadata,
    )

async def delete_document_chunks(document_id: int) -> None:
    """Remove all chunks associated with a document from ChromaDB."""
    collection = get_or_create_collection()
    # ChromaDB delete uses a where filter on metadata
    await asyncio.to_thread(
        collection.delete,
        where={"document_id": document_id},
    )

async def search_similar(
    query: str,
    top_k: int = 4,
) ->  list[tuple[str, str]]:
    """
    Given a query string, embed it, retrieve the most similar chunks
    from ChromaDB, and return their text content.
    """
    # 1. Embed the query (same model as documents)
    embeddings_model = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )
    # embed_query returns a single embedding vector
    query_embedding = await embeddings_model.aembed_query(query)

    # 2. Search ChromaDB
    collection = get_or_create_collection()
    results = await asyncio.to_thread(
        collection.query,
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents"],   # we want the chunk text
    )

    # 3. Extract chunk texts (results is a dict, docs are in "documents" key)
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]   # list of strings
    return list(zip(ids, docs))

@traceable()
async def multi_query_retrieval(
    question: str,
    top_k_per_query: int = 4,
    num_queries: int = 3,
) -> list[str]:
    """
    Generate multiple query variants, retrieve for each, deduplicate, and return chunk texts.
    """

    queries = await generate_multi_queries(question, num_queries)
    # Retrieve for each query
    all_chunks: dict[str, str] = {}  # id -> text, for deduplication
    for q in queries:
        results = await search_similar(q, top_k=top_k_per_query)
        for chunk_id, text in results:
            if chunk_id not in all_chunks:
                all_chunks[chunk_id] = text
    # Return only the texts (in no particular order)
    return list(all_chunks.values())