from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse
from app.services.document_parser import validate_file, extract_text_from_file
from app.services.chunking import chunk_text
from app.services.vector_store import embed_and_store
from sqlalchemy import select

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document, parse it, and store metadata + text."""
    # 1. Validate file type and size
    file_size = await validate_file(file)

    # 2. Extract text
    extracted_text = await extract_text_from_file(file)


    # 3. Create database entry
    document = Document(
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        extracted_text=extracted_text,
        user_id=current_user.id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 4. Return response with preview
    preview = extracted_text[:500] if extracted_text else None
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        user_id=document.user_id,
        extracted_text_preview=preview,
    )


@router.post("/{document_id}/chunk_store", status_code=status.HTTP_200_OK)
async def chunk_and_store(
        document_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """Chunk the document text, embed it, and store in ChromaDB."""
    # Fetch document, ensure it belongs to the user
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    # Chunk the text
    chunks = chunk_text(document.extracted_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks generated")

    # Embed and store in vector DB
    await embed_and_store(document.id, chunks)

    return {
        "message": f"Document processed successfully. {len(chunks)} chunks created.",
        "document_id": document.id,
        "chunk_count": len(chunks),
    }