import asyncio

from src.db import connect_db

if __name__ == "__main__":
    asyncio.run(connect_db())
    print("✅ Database initialized")
