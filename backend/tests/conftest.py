import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.dependencies import get_db
from app.models.user import Base, User, UserRole, Organisation
from app.core.security import create_access_token

# Use an in-memory SQLite database for lightning-fast testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def async_client(db_session):
    # Override the database dependency to use our test session
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def org_id(db_session):
    org = Organisation(name="Test Org")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org.id

@pytest_asyncio.fixture
async def user_id(db_session, org_id):
    user = User(org_id=org_id, email="maker@test.com", password_hash="hash", role=UserRole.MAKER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id

@pytest_asyncio.fixture
async def checker_user_id(db_session, org_id):
    user = User(org_id=org_id, email="checker@test.com", password_hash="hash", role=UserRole.CHECKER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id

@pytest_asyncio.fixture
async def admin_user_id(db_session, org_id):
    user = User(org_id=org_id, email="admin@test.com", password_hash="hash", role=UserRole.ADMIN)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id

@pytest_asyncio.fixture
def maker_token(user_id, org_id):
    return create_access_token(
        {"sub": str(user_id), "email": "maker@test.com", "role": "MAKER", "org_id": str(org_id)}
    )

@pytest_asyncio.fixture
def checker_token(checker_user_id, org_id):
    return create_access_token(
        {"sub": str(checker_user_id), "email": "checker@test.com", "role": "CHECKER", "org_id": str(org_id)}
    )

@pytest_asyncio.fixture
def admin_token(admin_user_id, org_id):
    return create_access_token(
        {"sub": str(admin_user_id), "email": "admin@test.com", "role": "ADMIN", "org_id": str(org_id)}
    )