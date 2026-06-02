from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator
import re
import os
import secrets
import hashlib
from app.db import get_pool
from pwdlib import PasswordHash
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

router = APIRouter()
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY 환경변수가 설정되지 않았습니다.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 엑세스 토큰 만료시간 (분)
REFRESH_TOKEN_EXPIRE_DAYS = 14 # 리프레시 토큰 만료시간 (일)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


# 리프레시 토큰 생성 (opaque random token)
def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


# 토큰 SHA-256 해시 (DB 저장용)
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# JWT 액세스 토큰 생성
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 토큰이 없거나 유효하지 않으면 None 반환 (선택적 인증용)
async def get_optional_user(token: str | None = Depends(oauth2_scheme_optional)) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None


# 토큰을 검증하고 현재 로그인된 사용자의 username 반환 (요청 검증)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=401,
        detail="유효하지 않은 토큰입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


# DB에서 사용자를 조회하고 비밀번호를 검증, 실패 시 None 반환 (로그인 검증)
async def authenticate_user(username: str, password: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, password FROM users WHERE username = $1", username)
    if not row or not password_hash.verify(password, row["password"]):
        return None
    return row


class SignupRequest(BaseModel): # 회원가입 시 적는 필드
    
    username: str # 4~20자, 영문 소문자/숫자/언더스코어 허용, 첫 글자는 영문자만
    
    password: str # 8~32자
    
    nickname: str # 2~12자, 한글/영문/숫자 허용, 공백/특수문자 금지

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-z][a-z0-9_]{3,19}$', v):
            raise ValueError("아이디는 4~20자, 영문 소문자로 시작하며 영문 소문자/숫자/언더스코어만 사용 가능합니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not (8 <= len(v) <= 32):
            raise ValueError("비밀번호는 8~32자여야 합니다.")
        return v

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        if not re.match(r'^[가-힣a-zA-Z0-9]{2,12}$', v):
            raise ValueError("닉네임은 2~12자, 한글/영문/숫자만 사용 가능합니다.")
        return v


class LoginRequest(BaseModel): # 로그인 시 적는 필드
    username: str
    password: str


class RefreshRequest(BaseModel): # 토큰 갱신/로그아웃 시 사용
    refresh_token: str


# 회원가입 API
@router.post("/signup")
async def signup(user: SignupRequest):
    pool = get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", user.username)
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
        hashed_password = password_hash.hash(user.password)
        await conn.execute(
            "INSERT INTO users (username, password, nickname) VALUES ($1, $2, $3)",
            user.username, hashed_password, user.nickname,
        )
    return {"message": "회원가입 성공"}


# 로그인 API
@router.post("/login")
async def login(user: LoginRequest):
    saved_user = await authenticate_user(user.username, user.password)
    if not saved_user:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token()
    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
            saved_user["id"], token_hash, expires_at,
        )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# 액세스 토큰 재발급 API (refresh token rotation)
@router.post("/refresh")
async def refresh(body: RefreshRequest):
    token_hash = hash_token(body.refresh_token)
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT rt.id, rt.expires_at, u.username, u.id AS user_id
            FROM refresh_tokens rt
            JOIN users u ON rt.user_id = u.id
            WHERE rt.token_hash = $1
            """,
            token_hash,
        )
        if not row:
            raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
        if row["expires_at"] < datetime.now(timezone.utc):
            await conn.execute("DELETE FROM refresh_tokens WHERE id = $1", row["id"])
            raise HTTPException(status_code=401, detail="만료된 리프레시 토큰입니다.")

        # rotation: 기존 토큰 삭제 후 새 토큰 발급 (트랜잭션으로 묶어 원자성 보장)
        new_refresh_token = create_refresh_token()
        new_token_hash = hash_token(new_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        async with conn.transaction():
            await conn.execute("DELETE FROM refresh_tokens WHERE id = $1", row["id"])
            await conn.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
                row["user_id"], new_token_hash, new_expires_at,
            )

    access_token = create_access_token({"sub": row["username"]})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


# 로그아웃 API (리프레시 토큰 무효화)
@router.post("/logout")
async def logout(body: RefreshRequest):
    token_hash = hash_token(body.refresh_token)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM refresh_tokens WHERE token_hash = $1", token_hash)
    return {"message": "로그아웃 성공"}


# 자기 정보 확인 API
@router.get("/me")
async def read_me(current_user: str = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, nickname, created_at FROM users WHERE username = $1", current_user
        )
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {
        "id": row["id"],
        "username": row["username"],
        "nickname": row["nickname"],
        "created_at": row["created_at"],
    }
