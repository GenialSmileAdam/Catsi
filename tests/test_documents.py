# tests/test_documents.py

import io
from fastapi import status
from unittest.mock import patch, AsyncMock

class TestDocumentUpload:

    def test_upload_text_file(self, client, registered_user):
        # Login to get token
        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Simulate a text file
        file_content = b"This is a test document about cats."
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert "extracted_text_preview" in data
        # Check preview
        assert "test document" in data["extracted_text_preview"]

    def test_upload_unsupported_type(self, client, registered_user):
        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_content = b"dummy"
        files = {"file": ("image.png", io.BytesIO(file_content), "image/png")}

        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def test_upload_no_auth(self, client):
        file_content = b"content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        response = client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestDocumentProcess:
    @patch("app.api.v1.endpoints.documents.embed_and_store", new_callable=AsyncMock)
    def test_process_success(self, mock_embed, client, registered_user):
        # First upload a document
        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_content = b"Cats are great pets. They like to sleep."
        files = {"file": ("cats.txt", io.BytesIO(file_content), "text/plain")}
        upload_res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        doc_id = upload_res.json()["id"]

        # Now process the document
        process_res = client.post(f"/api/v1/documents/{doc_id}/chunk_store", headers=headers)
        assert process_res.status_code == 200
        data = process_res.json()
        assert data["document_id"] == doc_id
        assert data["chunk_count"] > 0
        # Ensure embed_and_store was called once
        mock_embed.assert_awaited_once()

    def test_process_not_authenticated(self, client):
        response = client.post("/api/v1/documents/1/chunk_store")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED