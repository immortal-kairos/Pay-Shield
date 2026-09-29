import asyncio
from sqlalchemy.future import select
from app.core.dependencies import get_db
from app.models.user import User

async def update_user_role():
    print("--- PayShield Local Dev: Role Manager ---")
    email = input("Enter your account's email address: ").strip()
    new_role = input("Enter the role you want (e.g., CHECKER or MAKER): ").strip().upper()
    
    # Grab the database session generator you already use in your app
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Find the user using the ORM
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if user:
            user.role = new_role
            await db.commit()
            print(f"\n✅ SUCCESS! The account '{email}' is now a {new_role}.")
            print("⚠️ IMPORTANT: You must log out and log back in on the frontend to get your new token!")
        else:
            print(f"\n❌ ERROR: Could not find a user with the email '{email}'.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(update_user_role())