from pydantic import BaseModel, Field
from datetime import datetime

class DocumentResponse(BaseModel):
    """Response model for a single document upload."""
    id: int
    filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime
    user_id: int

    model_config = {"from_attributes": True}

class DocumentUploadResponse(DocumentResponse):
    """Extended response that also includes a preview of extracted text."""
    extracted_text_preview: str | None = Field(
        None,
        description="First 500 characters of extracted text"
    )