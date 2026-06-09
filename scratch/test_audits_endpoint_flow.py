import asyncio
import sys
sys.path.append(".")

from api.database import AsyncSessionLocal
from api.models import Form5500Audit
from sqlalchemy import select

async def main():
    db = AsyncSessionLocal()
    clean_ein = "020444227"
    
    stmt = select(Form5500Audit).where(Form5500Audit.ein == clean_ein)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    print(f"Record: {record}")
    if record:
        print(f"Record EIN: {record.ein}")
        print(f"Record total_assets: {record.total_assets} (type: {type(record.total_assets)})")
        print(f"record.total_assets is None: {record.total_assets is None}")
        try:
            print(f"record.total_assets == 0.0: {record.total_assets == 0.0}")
            print(f"float(record.total_assets) == 0.0: {float(record.total_assets) == 0.0}")
        except Exception as e:
            print(f"Error checking == 0.0: {e}")
            
        condition = not record or record.total_assets is None or record.total_assets == 0.0
        print(f"Trigger condition evaluated to: {condition}")
        
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
