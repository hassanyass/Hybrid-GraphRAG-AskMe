import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())
from backend.app.database.session import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, filename, status FROM documents WHERE status = 'COMPLETED' LIMIT 1"))
        row = res.fetchone()
        if row:
            print(f"Doc: {row.id} - {row.filename} - {row.status}")
        else:
            print("No completed docs found")

if __name__ == '__main__':
    asyncio.run(main())
