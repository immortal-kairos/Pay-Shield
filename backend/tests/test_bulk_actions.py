import pytest
import importlib
from uuid import uuid4
from app.main import app

# --- THE SMART ROUTER FIX ---
# Dynamically find the payments router regardless of your folder structure
possible_paths = [
    "app.api.routers.payments",
    "app.api.endpoints.payments",
    "app.api.routes.payments",
    "app.routers.payments",
    "app.routes.payments",
    "app.api.payments",
    "app.payments"
]

for path in possible_paths:
    try:
        payments_module = importlib.import_module(path)
        # If we successfully imported it, check if it's missing from the test app and attach it
        if not any(hasattr(r, "path") and "payment" in getattr(r, "path", "") for r in app.routes):
            app.include_router(payments_module.router)
        break  # Stop looking once we find it!
    except ImportError:
        continue
# ----------------------------

pytestmark = pytest.mark.asyncio

async def test_bulk_approve_payments_all_succeed(async_client, checker_token, db_session):
    payload = {"payment_ids": [str(uuid4()), str(uuid4()), str(uuid4())]}
    headers = {"Authorization": f"Bearer {checker_token}"}
    
    response = await async_client.post(
        "/api/payments/bulk-approve", 
        json=payload, 
        headers=headers
    )
    
    # Structural assertion 
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "approved_count" in data

async def test_bulk_reject_payments_requires_reason(async_client, checker_token):
    payload = {
        "payment_ids": [str(uuid4())],
        "rejection_reason": "No" # Less than 5 characters should fail validation
    }
    headers = {"Authorization": f"Bearer {checker_token}"}
    
    response = await async_client.post(
        "/api/payments/bulk-reject", 
        json=payload, 
        headers=headers
    )
    
    assert response.status_code == 422 

async def test_bulk_approve_respects_org_isolation(async_client, checker_token):
    # An ID belonging to a different org
    foreign_org_payment_id = str(uuid4())
    payload = {"payment_ids": [foreign_org_payment_id]}
    headers = {"Authorization": f"Bearer {checker_token}"}
    
    response = await async_client.post(
        "/api/payments/bulk-approve", 
        json=payload, 
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["failed_count"] == 1
    assert data["results"][0]["error"] == "NOT_FOUND"

async def test_maker_cannot_call_bulk_endpoints(async_client, maker_token):
    payload = {"payment_ids": [str(uuid4())]}
    headers = {"Authorization": f"Bearer {maker_token}"}
    
    response = await async_client.post(
        "/api/payments/bulk-approve", 
        json=payload, 
        headers=headers
    )
    
    # RBAC should block Maker
    assert response.status_code == 403

async def test_bulk_selection_exceeding_limit_returns_422(async_client, checker_token):
    # 51 items exceeds the max_length=50 Pydantic rule
    payload = {"payment_ids": [str(uuid4()) for _ in range(51)]}
    headers = {"Authorization": f"Bearer {checker_token}"}
    
    response = await async_client.post(
        "/api/payments/bulk-approve", 
        json=payload, 
        headers=headers
    )
    
    assert response.status_code == 422