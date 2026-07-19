# tests/test_chat.py

from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from langchain_core.messages import AIMessage

class TestChat:
    @patch("app.api.v1.endpoints.chat.ChatOllama.invoke")
    @patch("app.api.v1.endpoints.chat.search_similar", new_callable=AsyncMock)
    def test_chat_with_rag(self, mock_search, mock_invoke, client, registered_user):
        # Mock retrieval to return some chunks
        mock_search.return_value = ["Cats sleep 16 hours a day."]
        # Mock LLM response
        mock_llm = AIMessage(content="Based on the document, cats sleep a lot.")
        mock_invoke.return_value = mock_llm

        # Login
        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Send chat
        response = client.post("/api/v1/chat/", json={"message": "How long do cats sleep?"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert data["sources"] == ["Cats sleep 16 hours a day."]
        # Ensure the LLM was called
        mock_invoke.assert_called_once()

    @patch("app.api.v1.endpoints.chat.ChatOllama.invoke")
    @patch("app.services.vector_store.search_similar", new_callable=AsyncMock)
    def test_chat_no_documents(self, mock_search, mock_invoke, client, registered_user):
        # No documents retrieved
        mock_search.return_value = []
        mock_llm = AIMessage(content="I don't have any information about that.")
        mock_invoke.return_value = mock_llm

        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/api/v1/chat/", json={"message": "Unknown topic"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "I don't have any information about that."
        # Check that the LLM was still called (but with empty context)
        mock_invoke.assert_called_once()