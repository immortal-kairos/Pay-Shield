import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.models.user import Base, UserRole
from app.api.auth import router, limiter
from app.core.dependencies import get_db

# Async SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Setup Test App
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# --- THE 7 TESTS ---

@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    payload = {
        "email": "test@company.com",
        "password": "SecurePassword123!",
        "role": "MAKER",
        "org_name": "Test Org"
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@company.com"
    assert data["role"] == "MAKER"
    assert "password_hash" not in data  # Non-negotiable security requirement

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(async_client: AsyncClient):
    payload = {
        "email": "dup@company.com",
        "password": "SecurePassword123!",
        "role": "MAKER",
        "org_name": "Test Org"
    }
    await async_client.post("/api/auth/register", json=payload)
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success_returns_jwt(async_client: AsyncClient):
    # Register first
    await async_client.post("/api/auth/register", json={
        "email": "login@company.com",
        "password": "SecurePassword123!",
        "role": "MAKER",
        "org_name": "Test Org"
    })
    
    # Login
    response = await async_client.post("/api/auth/login", json={
        "email": "login@company.com",
        "password": "SecurePassword123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(async_client: AsyncClient):
    await async_client.post("/api/auth/register", json={
        "email": "wrongpass@company.com",
        "password": "SecurePassword123!",
        "role": "MAKER",
        "org_name": "Test Org"
    })
    
    response = await async_client.post("/api/auth/login", json={
        "email": "wrongpass@company.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_no_token_returns_401(async_client: AsyncClient):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 403  # HTTPBearer returns 403 when not authenticated at all

@pytest.mark.asyncio
async def test_protected_route_valid_token_returns_user(async_client: AsyncClient):
    await async_client.post("/api/auth/register", json={
        "email": "me@company.com",
        "password": "SecurePassword123!",
        "role": "CHECKER",
        "org_name": "Test Org"
    })
    login_res = await async_client.post("/api/auth/login", json={
        "email": "me@company.com",
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]
    
    me_res = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@company.com"
    assert "password_hash" not in me_res.json()

@pytest.mark.asyncio
async def test_maker_cannot_access_checker_only_route(async_client: AsyncClient):
    # 1. Register a MAKER
    await async_client.post("/api/auth/register", json={
        "email": "maker@company.com",
        "password": "SecurePassword123!",
        "role": "MAKER",
        "org_name": "Test Org"
    })
    # 2. Login as MAKER
    login_res = await async_client.post("/api/auth/login", json={
        "email": "maker@company.com",
        "password": "SecurePassword123!"
    })
    token = login_res.json()["access_token"]
    
    # 3. Attempt to access CHECKER route
    stub_res = await async_client.get("/api/auth/stub-checker", headers={"Authorization": f"Bearer {token}"})
    
    # Assert 403 Forbidden
    assert stub_res.status_code == 403
    assert stub_res.json()["detail"] == "Insufficient permissions"