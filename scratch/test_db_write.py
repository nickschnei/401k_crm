import asyncio
import uuid
import sys

# Add root folder to sys.path
sys.path.append(r"c:\Users\nicks\Documents\401k_crm")

from api.database import AsyncSessionLocal, engine
from api.models import User, Tenant
from utils.security import hash_password

async def test_write():
    print("Testing direct async DB write...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Create Tenant
            tenant_id = str(uuid.uuid4())
            new_tenant = Tenant(
                id=tenant_id,
                company_name="Local Test Firm",
                subscription_tier="free",
                subscription_status="active"
            )
            db.add(new_tenant)
            await db.flush()
            print("Flushed tenant successfully.")
            
            # 2. Create User
            new_user = User(
                id=str(uuid.uuid4()),
                tenant_id=new_tenant.id,
                email="test_async_write@example.com",
                clerk_user_id=f"usr_local_{uuid.uuid4().hex[:12]}",
                hashed_password=hash_password("password123"),
                first_name="Test",
                last_name="User",
                role="admin"
            )
            db.add(new_user)
            await db.commit()
            print("Committed user and tenant successfully!")
            
            # Clean up
            await db.delete(new_user)
            await db.delete(new_tenant)
            await db.commit()
            print("Cleaned up test data.")
            
        except Exception as e:
            print(f"Error during async DB write: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_write())
