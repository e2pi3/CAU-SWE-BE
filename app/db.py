import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

#DB 연결을 위한 URL 생성
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
               f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

async def get_db(): #DB 연결 함수
    return await asyncpg.connect(DATABASE_URL)