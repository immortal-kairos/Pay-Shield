import asyncio
from uuid import uuid4
from sqlalchemy.future import select
from passlib.context import CryptContext
from app.core.dependencies import get_db
from app.models.user import User

# Standard FastAPI password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_checker():
    print("--- PayShield Local Dev: Direct Checker Injection ---")
    maker_email = input("Enter your existing MAKER email (to copy the organization ID): ").strip()
    
    checker_email = "farhan.checker@example.com"
    checker_password = "Password123!"

    db_gen = get_db()
    db = await anext(db_gen)

    try:
        # 1. Find the Maker to get the correct org_id
        result = await db.execute(select(User).where(User.email == maker_email))
        maker = result.scalars().first()
        
        if not maker:
            print(f"\n❌ ERROR: Could not find MAKER '{maker_email}'.")
            return

        org_id = maker.org_id

        # 2. Check if our test checker already exists
        result = await db.execute(select(User).where(User.email == checker_email))
        existing_checker = result.scalars().first()
        
        if existing_checker:
            print(f"\n⚠️ '{checker_email}' already exists. Updating role, org_id, and resetting password...")
            existing_checker.role = "CHECKER"
            existing_checker.org_id = org_id
            existing_checker.password_hash = pwd_context.hash(checker_password)
        else:
            # 3. Inject the new Checker
            new_checker = User(
                id=uuid4(),
                org_id=org_id,
                email=checker_email,
                password_hash=pwd_context.hash(checker_password),
                role="CHECKER",
                is_active=True
            )
            db.add(new_checker)

        await db.commit()
        print(f"\n✅ SUCCESS! Checker account injected directly into the database.")
        print(f"   Email:    {checker_email}")
        print(f"   Password: {checker_password}")
        print(f"   Org ID:   {org_id}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_checker())