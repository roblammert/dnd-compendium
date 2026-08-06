import asyncio
from app.db import Base, SessionLocal, engine
from app.services import init_search
from app.sync import sync_open5e

async def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        init_search(db)
        run=await sync_open5e(db)
        print(f"sync #{run.id}: {run.status}; seen={run.records_seen}, created={run.records_created}, updated={run.records_updated}")
if __name__=="__main__": asyncio.run(main())
