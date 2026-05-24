# 메인 서버

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import init_db, close_db, get_pool
import time
import logging


@asynccontextmanager 
async def lifespan(app: FastAPI):
    await init_db()

    yield  # 서버 실행 구간

    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

######################
# API 성능 측정 함수
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = (time.perf_counter() - start) * 1000

    logger.info(f"{request.method} {request.url.path} took {duration:.2f}ms")

    #로컬 테스트용
    print(f"INFO: {request.method} {request.url.path} took {duration:.2f}ms")

    return response
#######################



@app.get("/") # 서버 진입점
async def root():
    return {"message": "CAU-SWE-BE API Server On"}



# 통합 검색 API  ex) /search?q=모히토
# 칵테일, 재료 테이블에서 이름으로 검색 (각 최대 10개)
@app.get("/search")
async def search(q: str):
    pool = get_pool()
    query = f"{q.lower()}%"

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            (SELECT id::TEXT, name_ko, category FROM cocktail
            WHERE LOWER(name_ko) LIKE $1 OR LOWER(name) LIKE $1
            LIMIT 10)
            UNION ALL
            (SELECT id::TEXT, name_ko, category FROM ingredient
            WHERE LOWER(name_ko) LIKE $1 OR LOWER(name) LIKE $1
            LIMIT 10)
            """,
            query
        )

    return [
        {"id": r["id"],
         "name_ko": r["name_ko"],
         "category": r["category"]
         }
        for r in rows
    ]



# 칵테일 정보 조회 API ex) /cocktails/info?id=11000
# 칵테일 목록에서 칵테일 세부 조회로 넘어갈 때 사용
# id로 조회하여 해당 칵테일 모든 정보 반환
@app.get("/cocktails/info")
async def cocktail_info(id: str):
    pool = get_pool()
    query = id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                c.id,
                c.name,
                c.name_ko,
                c.recipe,
                c.glass_type,
                c.image_url,
                c.abv,
                c.description,
                i.name_ko AS ingredient,
                ci.amount
            FROM cocktail c
            JOIN cocktail_ingredient ci ON c.id = ci.cocktail_id
            JOIN ingredient i ON ci.ingredient_id = i.id
            WHERE c.id = $1
            """, 
            query
        )

    if not rows:
        return None

    first = rows[0]

    ingredients = [
        {
            "ingredient": r["ingredient"],
            "amount": r["amount"]
        }
        for r in rows
    ]

    return {
        "id": first["id"],
        "name": first["name"],
        "name_ko": first["name_ko"],
        "recipe": first["recipe"],
        "glass_type": first["glass_type"],
        "image_url": first["image_url"],
        "abv": first["abv"],
        "description": first["description"],
        "ingredients": ingredients
    }
