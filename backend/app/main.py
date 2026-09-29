from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, payments  # <-- ADDED payments HERE
from app.core.dependencies import engine

# CRITICAL FIX: We must import User and Organisation here 
# so SQLAlchemy knows they exist before it tries to create the tables.
from app.models.user import Base, User, Organisation

app = FastAPI(title="PayShield API")

# CORS setup for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This block automatically creates your database tables when the server starts
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Use '/api/auth' as the single source of truth for the prefix
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# <-- ADDED THIS BLOCK TO REGISTER PAYMENTS -->
# (Note: The prefix "/api/payments" is already defined inside payments.py, 
# so we don't need to declare it again here)
app.include_router(payments.router)

@app.get("/health")
async def health():
    return {"status": "ok"}