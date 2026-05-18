# 메인 서버

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/") # 서버 진입점
async def root():
    return {"message": "CAU-SWE-BE API"}

# 칵테일 목록 조회 API  ex) /cocktails/search?q=모히토
# 이름, 영어이름, 잔 종류만 반환합니다.
@app.get("/cocktails/search")
async def search_cocktails(q: str):
    db = await get_db()

    query = f"{q}%"
    rows = await db.fetch(
        "SELECT id, name, name_ko, glass_type FROM cocktail WHERE name ILIKE $1 OR name_ko ILIKE $2",
        query, query
    )

    await db.close()

    return [
        {"id": r["id"], "name": r["name"], "name_ko": r["name_ko"], "glass_type": r["glass_type"]}
        for r in rows
    ]