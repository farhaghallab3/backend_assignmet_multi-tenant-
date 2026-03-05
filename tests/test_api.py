import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    reg_data = {
        "email": "test@example.com",
        "password": "StrongPassword123",
        "full_name": "Test User"
    }
    response = await client.post("/auth/register", json=reg_data)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

    # Login
    login_data = {
        "email": "test@example.com",
        "password": "StrongPassword123"
    }
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    token = response.json()["access_token"]
    return token

@pytest.mark.asyncio
async def test_create_org_and_rbac(client):
    # Register and Login
    reg_data = {"email": "admin@org.com", "password": "pass", "full_name": "Admin"}
    await client.post("/auth/register", json=reg_data)
    login_resp = await client.post("/auth/login", json={"email": "admin@org.com", "password": "pass"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Org
    org_resp = await client.post("/organization", json={"org_name": "Test Org"}, headers=headers)
    assert org_resp.status_code == 200
    org_id = org_resp.json()["org_id"]

    # Add member
    reg_data_2 = {"email": "member@org.com", "password": "pass", "full_name": "Member"}
    await client.post("/auth/register", json=reg_data_2)
    
    add_user_resp = await client.post(
        f"/organization/{org_id}/user", 
        json={"email": "member@org.com", "role": "member"},
        headers=headers
    )
    assert add_user_resp.status_code == 200

    # Test RBAC - Member views items
    login_resp_mem = await client.post("/auth/login", json={"email": "member@org.com", "password": "pass"})
    mem_token = login_resp_mem.json()["access_token"]
    mem_headers = {"Authorization": f"Bearer {mem_token}"}
    
    items_resp = await client.get(f"/organizations/{org_id}/item", headers=mem_headers)
    assert items_resp.status_code == 200
    assert items_resp.json() == [] # Empty but allowed
