# 메인 서버

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import init_db, close_db, get_pool
from app.auth import router as auth_router
import time
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    yield  # 서버 실행 구간

    await close_db()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)

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
    query = f"{q.lower().replace(' ', '')}%"

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            (SELECT id::TEXT, name_ko, category FROM cocktail
            WHERE REPLACE(LOWER(name_ko), ' ', '') LIKE $1 OR REPLACE(LOWER(name), ' ', '') LIKE $1
            LIMIT 10)
            UNION ALL
            (SELECT id::TEXT, name_ko, category FROM ingredient
            WHERE REPLACE(LOWER(name_ko), ' ', '') LIKE $1 OR REPLACE(LOWER(name), ' ', '') LIKE $1
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
                i.id AS ingredient_id,
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
            "id": r["ingredient_id"],
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



# 재료 정보 조회 API  ex) /ingredients/info?id=1&limit=5&offset=0
# id로 조회하여 재료 정보 및 해당 재료가 들어간 칵테일 목록 반환 (페이지네이션 지원)
@app.get("/ingredients/info")
async def ingredient_info(id: int, limit: int = 5, offset: int = 0):
    pool = get_pool()

    async with pool.acquire() as conn:
        # 재료 기본 정보 조회
        ingredient = await conn.fetchrow(
            """
            SELECT id, name, name_ko, image_url, category
            FROM ingredient
            WHERE id = $1
            """,
            id
        )

        if not ingredient:
            return None

        # 해당 재료가 들어간 칵테일 전체 수 조회
        cocktail_total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM cocktail_ingredient
            WHERE ingredient_id = $1
            """,
            id
        )

        # 해당 재료가 들어간 칵테일 목록 조회 (페이지네이션 적용)
        cocktails = await conn.fetch(
            """
            SELECT c.id::TEXT, c.name_ko, c.image_url
            FROM cocktail c
            JOIN cocktail_ingredient ci ON c.id = ci.cocktail_id
            WHERE ci.ingredient_id = $1
            LIMIT $2 OFFSET $3
            """,
            id, limit, offset
        )

    return {
        "id": ingredient["id"],
        "name": ingredient["name"],
        "name_ko": ingredient["name_ko"],
        "image_url": ingredient["image_url"],
        "category": ingredient["category"],
        "cocktail_total": cocktail_total,
        "cocktails": [
            {
                "id": c["id"],
                "name_ko": c["name_ko"],
                "image_url": c["image_url"]
            }
            for c in cocktails
        ]
    }


# 시간대에 따른 멘트 API
# 홈화면에서 시간대에 따라 표시될 멘트
@app.get("/timement")
async def get_greeting():
    # 한국 시간 기준 시간대 계산 (UTC+9)
    korea_hour = (int(time.time()) // 3600 + 9) % 24

    if 20 <= korea_hour or korea_hour < 4:
        message = "달빛이 드리운 밤, 칵테일 한잔"
    elif 4 <= korea_hour < 12:
        message = "좋은 아침이에요, 오늘도 화이팅!"
    elif 12 <= korea_hour < 18:
        message = "햇살 가득한 오후, 칵테일 한잔"
    else: # 18 <= korea_hour < 20
        message = "노을 빛 아래, 칵테일 한잔"

    return {"message": message}



# 무작위 칵테일 추천 API  ex) /cocktails/random?count=3
# cocktail 테이블에서 count개만큼 랜덤 추출 (기본값: 1)
@app.get("/cocktails/random")
async def cocktail_random(count: int = 1):
    if count < 1:
        raise HTTPException(status_code=400, detail="count는 1 이상이어야 합니다.")

    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id::TEXT, name_ko, category, image_url
            FROM cocktail
            ORDER BY RANDOM()
            LIMIT $1
            """,
            count
        )

    return [
        {
            "id": r["id"],
            "name_ko": r["name_ko"],
            "category": r["category"],
            "image_url": r["image_url"]
        }
        for r in rows
    ]