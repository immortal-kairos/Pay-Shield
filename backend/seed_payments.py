import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy import text
from app.core.dependencies import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.models.payment import Payment 

async def seed_payments():
    print("--- PayShield Local Dev: Data Seeder ---")
    email = input("Enter your Checker email (to link the correct org_id): ").strip()
    
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # 0. THE DATABASE RESCUE: Fix the bad enum status we injected previously!
        # This raw SQL command fixes the corrupted row before SQLAlchemy even looks at it.
        await db.execute(text("UPDATE vendors SET status = 'ACTIVE' WHERE status = 'APPROVED'"))
        await db.commit()

        # Find the correct organization and user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            print(f"\n❌ Could not find user: {email}")
            return
            
        org_id = user.org_id
        now = datetime.now(timezone.utc) 
        
        # 1. Fetch the dummy vendor
        vendor_result = await db.execute(select(Vendor).where(Vendor.contact_email == "billing@techflow.example.com"))
        vendor = vendor_result.scalars().first()
        
        if not vendor:
            print("\n❌ Could not find the dummy vendor.")
            return
            
        # 2. Create the 3 Dummy Payments
        dummy_payments = [
            Payment(
                id=uuid.uuid4(),
                org_id=org_id,
                vendor_id=vendor.id,
                amount=25000.00,
                currency="INR",
                payment_date=(now + timedelta(days=1)).date(),
                status="PENDING_APPROVAL",
                risk_score=12.0,
                risk_level="LOW",
                reference_note="Standard monthly software billing",
                created_by_user_id=user.id,
                created_at=now
            ),
            Payment(
                id=uuid.uuid4(),
                org_id=org_id,
                vendor_id=vendor.id,
                amount=145000.00,
                currency="INR",
                payment_date=(now + timedelta(days=2)).date(),
                status="PENDING_APPROVAL",
                risk_score=85.0,
                risk_level="HIGH",
                reference_note="Urgent expedited freight - UNVERIFIED VENDOR",
                created_by_user_id=user.id,
                created_at=now
            ),
            Payment(
                id=uuid.uuid4(),
                org_id=org_id,
                vendor_id=vendor.id,
                amount=450.00,
                currency="INR",
                payment_date=(now + timedelta(days=1)).date(),
                status="PENDING_APPROVAL",
                risk_score=5.0,
                risk_level="LOW",
                reference_note="API usage overage fees",
                created_by_user_id=user.id,
                created_at=now,
                ml_available=True,
                ml_risk_score=0.92,
                ml_risk_label="HIGH" 
            )
        ]
        
        db.add_all(dummy_payments)
        await db.commit()
        
        print("\n✅ SUCCESS! 3 Payments have been permanently saved to the ledger.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(seed_payments())