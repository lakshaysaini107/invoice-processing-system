import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_register_user(async_client, test_user_data):
    """Test user registration"""
    response = await async_client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "user_id" in data
    assert data["message"] == "User registered successfully"

@pytest.mark.asyncio
async def test_login_user(async_client, test_user_data):
    """Test user login"""
    # First register
    await async_client.post("/api/auth/register", json=test_user_data)
    
    # Then login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = await async_client.post("/api/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_current_user(authenticated_client):
    """Test getting current user info"""
    response = await authenticated_client.get("/api/auth/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "email" in data
    assert "full_name" in data

@pytest.mark.asyncio
async def test_upload_invoice(authenticated_client, tmp_path):
    """Test invoice upload"""
    # Create a test file
    test_file = tmp_path / "test_invoice.pdf"
    test_file.write_text("test invoice content")
    
    with open(test_file, "rb") as f:
        files = {"files": (f.name, f, "application/pdf")}
        response = await authenticated_client.post("/api/invoices/upload", files=files)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "invoice_id" in data
    assert data["status"] == "uploaded"

@pytest.mark.asyncio
async def test_list_invoices(authenticated_client):
    """Test listing user invoices"""
    response = await authenticated_client.get("/api/invoices/list")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
