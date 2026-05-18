# 메인 서버

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import init_db, close_db, get_pool
import time


@asynccontextmanager 
async def lifespan(app: FastAPI):
    await init_db()
    print("DB pool initialized")

    yield  # 서버 실행 구간

    await close_db()
    print("DB pool closed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


######################
# API 성능 측정 함수
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = (time.perf_counter() - start) * 1000

    print(f"{request.url.path} took {duration:.2f}ms")

    return response
#######################



@app.get("/") # 서버 진입점
async def root():
    return {"message": "CAU-SWE-BE API Server On"}



# 칵테일 목록 조회 API  ex) /cocktails/search?q=모히토
# 이름, 영어이름, 잔 종류만 반환합니다.
@app.get("/cocktails/search")
async def search_cocktails(q: str):
    pool = get_pool()
    query = f"{q.lower()}%"

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, name_ko, glass_type
            FROM cocktail
            WHERE LOWER(name) LIKE $1 
                OR LOWER(name_ko) LIKE $1
            LIMIT 10
            """,
            query
        )

    return [
        {"id": r["id"], 
         "name": r["name"], 
         "name_ko": r["name_ko"], 
         "glass_type": r["glass_type"]
         }
        for r in rows
    ]


# 칵테일 정보 조회 API ex) /cocktails/info?id=11000
# 칵테일 목록에서 칵테일 세부 조회로 넘어갈 때 사용
# id로 조회하여 해당 칵테일 모든 정보 반환
@app.get("/cocktails/info")
async def cocktail_info(id: str):
    pass # 구현 예정