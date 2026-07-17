from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse
from app.services.document_parser import validate_file, extract_text_from_file

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