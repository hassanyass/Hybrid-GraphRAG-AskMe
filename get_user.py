import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())

from backend.app.database.session import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id FROM users LIMIT 1"))
        val = res.scalar()
        print(f"USER_ID={val}")
        
        res = await conn.execute(text("SELECT id FROM workspaces LIMIT 1"))
        val = res.scalar()
        print(f"WORKSPACE_ID={val}")

if __name__ == '__main__':
    asyncio.run(main())
