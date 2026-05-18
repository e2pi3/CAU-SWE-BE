# DB 연결

import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

db_pool: asyncpg.Pool = None


async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20,
        statement_cache_size=0,
        ssl="require"
    )


async def close_db():
    await db_pool.close()


def get_pool():
    return db_pool