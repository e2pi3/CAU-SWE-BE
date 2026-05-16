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

@app.get("/cocktails/search") # 칵테일 검색 API  ex) /cocktails/search?q=모히토
async def search_cocktails(q: str):
    db = await get_db()

    query = f"{q}%"
    rows = await db.fetch(
        "SELECT id, name, name_ko, description FROM cocktail WHERE name ILIKE $1 OR name_ko ILIKE $2",
        query, query
    )

    await db.close()

    return [
        {"id": r["id"], "name": r["name"], "name_ko": r["name_ko"], "description": r["description"]}
        for r in rows
    ]