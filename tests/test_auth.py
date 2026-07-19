
import pytest
from fastapi import status

class TestAuth:

    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "secure1234"
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert "password" not in data
        assert "id" in data

    def test_register_duplicate(self, client, registered_user):
        # Try to register the same username again
        response = client.post("/api/v1/auth/register", json={
            "username": registered_user["username"],
            "email": "another@example.com",
            "password": "pass123456"
        })
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_login_success(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_route_without_token(self, client):
        response = client.get("/api/v1/users/me")  # Assuming we have a /users/me endpoint from Step 2 (we can add it if not)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_route_with_valid_token(self, client, registered_user):
        # First login to get token
        login_res = client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        token = login_res.json()["access_token"]
        # Make authenticated request
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == registered_user["username"]