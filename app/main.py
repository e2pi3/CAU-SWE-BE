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



# 칵테일 목록 조회 API  ex) /cocktails/search?q=모히토
# 검색창에서 이름으로 검색 시 목록 나열
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


##################################################
# 칵테일 정보 조회 API ex) /cocktails/info?id=11000
# 칵테일 목록에서 칵테일 세부 조회로 넘어갈 때 사용
# id로 조회하여 해당 칵테일 모든 정보 반환

# 설계구조설명
# id를 입력받아서 칵테일 테이블에서 정보불러오기
# 칵테일-재료 중간 테이블에서 재료 id 얻은다음
# 재료 테이블에서 id로 재료 이름 가져와서 
# 전부 JSON으로 응답
@app.get("/cocktails/info")
async def cocktail_info(id: str):
    pass # 구현 예정
##################################################