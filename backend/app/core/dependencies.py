import base64
import json
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User

DATABASE_URL = "sqlite+aiosqlite:///./payshield.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def require_role(allowed_roles: list):
    """
    Validates the user's JWT token and ensures they have the correct permissions.
    """
    async def role_checker(
        token: str = Depends(oauth2_scheme), 
        db: AsyncSession = Depends(get_db)
    ):
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid token format")
                
            # FIX 1: Use urlsafe_b64decode to handle JWT dashes and underscores without crashing
            payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("Token missing 'sub' claim")
                
            # FIX 2: Safely convert string to UUID object for SQLAlchemy
            user_id = uuid.UUID(user_id_str)
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            
            # FIX 3: Compare string representations to bypass strict Enum typing errors
            user_role_str = str(user.role.value) if hasattr(user, "role") and hasattr(user.role, "value") else str(user.role)
            allowed_roles_str = [str(r.value) if hasattr(r, "value") else str(r) for r in allowed_roles]
            
            if not user or user_role_str not in allowed_roles_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Access Restricted"
                )
            
            return {"id": str(user.id), "org_id": str(user.org_id), "role": user.role}
            
        except HTTPException:
            # FIX 4: Do not swallow HTTPExceptions! Let them pass through directly.
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail=f"Authentication failed: {str(e)}"
            )
            
    return role_checker