from fastapi import UploadFile, HTTPException, status
import os

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed MIME types
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.text",
    "text/csv",
}


async def validate_file(file: UploadFile) -> int:
    """Validate file type and size."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported."
        )
    # Read file content to check size (we'll also use this later)
    file_content = await file.read()
    file_size =  len(file_content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {MAX_FILE_SIZE // (1024 * 1024)} MB allowed."
        )
    # Reset the file cursor so we can read again later
    await file.seek(0)
    return file_size


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Given an UploadFile, use LangChain's appropriate loader to extract text.
    We need to write the file temporarily because LangChain loaders expect a file path.
    """
    # Save uploaded file to a temporary location
    suffix = os.path.splitext(file.filename or "temp")[1]
    temp_path = f"/tmp/catsi_upload_{os.getpid()}{suffix}"

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Select loader based on content type
        content_type = file.content_type or ""

        if content_type == "application/pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(temp_path)
        elif content_type == "text/plain":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(temp_path, encoding="utf-8")
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(temp_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            from langchain_community.document_loaders import UnstructuredExcelLoader
            loader = UnstructuredExcelLoader(temp_path, mode="elements")
        elif content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            from langchain_community.document_loaders import UnstructuredPowerPointLoader
            loader = UnstructuredPowerPointLoader(temp_path)
        elif content_type == "application/vnd.oasis.opendocument.text":
            from langchain_community.document_loaders import UnstructuredODTLoader
            loader = UnstructuredODTLoader(temp_path)
        elif content_type == "text/csv":
            from langchain_community.document_loaders.csv_loader import CSVLoader
            loader = CSVLoader(file_path=temp_path)
        else:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {content_type}")

        # Load documents (LangChain returns a list of Document objects)
        docs = loader.load()
        # Combine all pages/sections into one text string
        full_text = "\n".join([doc.page_content for doc in docs])
        return full_text
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)