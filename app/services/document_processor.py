from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.models.document import Document
from app.services.chunking import chunk_text
from app.services.vector_store import embed_and_store, delete_document_chunks
from sqlalchemy import select

async def process_document_async(document_id: int):
    """
    Fetch document from DB, chunk its text, embed, and store in Chroma.
    This function runs in the background and handles its own DB session.
    """
    # Create a new session (the original session from the request is already closed)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc or not doc.extracted_text:
            return

        # Chunk
        chunks = chunk_text(doc.extracted_text)
        if not chunks:
            return

        # Replace old chunks (idempotent)
        await embed_and_store(document_id, chunks)