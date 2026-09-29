from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User, Organisation
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_db

# REMOVED the prefix here because we added it in main.py
router = APIRouter()

@router.post("/register", status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Create a dummy Org if none exists (simplifies testing)
        org = Organisation(name=user_in.org_name)
        db.add(org)
        await db.flush() 

        # 2. Create User
        new_user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            role=user_in.role,
            org_id=org.id
        )
        db.add(new_user)
        await db.commit()
        return {"message": "User created", "email": new_user.email}
    except Exception as e:
        print(f"DATABASE ERROR: {e}") # This shows the error in your terminal
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role if isinstance(user.role, str) else user.role.value,
        "org_id": str(user.org_id)
    }
    return {"access_token": create_access_token(token_payload), "token_type": "bearer"}