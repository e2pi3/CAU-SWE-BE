from fastapi import FastAPI
from app.db import get_db

app = FastAPI()

@app.get("/") # 진입점
async def root():
    return {"message": "CAU-SWE-BE API"}

@app.get("/users") # DB(임시) 테이블 조회 예시
async def get_users():
    db = await get_db()
    
    rows = await db.fetch("SELECT id, name, age FROM users")

    await db.close()

    return [
        {"id": r["id"], "name": r["name"], "age": r["age"]}
        for r in rows
    ]