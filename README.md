# 🍸 칵테일러 🍹

> 칵테일러 BE repository

---

## 📋 목차

- [기술 스택](#-기술-스택)
- [팀원 역할 분담](#-팀원-역할-분담)
- [시작하기](#-시작하기)
- [폴더 구조](#-폴더-구조)
- [브랜치 전략](#-브랜치-전략)
- [커밋 컨벤션](#-커밋-컨벤션)
- [협업 규칙](#-협업-규칙)

---

## 🛠 기술 스택

| 항목 | 내용 |
|------|------|
| Framework | FastAPI |
| Language | Python 3.14 |
| DB | PostgreSQL |
| ORM | SQLAlchemy |
| 버전관리 | Git / GitHub |

---

## 👥 팀원 역할 분담

각 스프린트 별 역할 배분 예정, 추후 디스코드 참고

> 각자 담당 브랜치에서 작업 후 PR을 통해 `develop` 브랜치에 병합합니다.

---

## 🏁 시작하기

### 사전 요구사항

- Python 3.10 이상
- PostgreSQL 설치 및 실행 중
- Git 설치

### 1. 레포지토리 클론

```bash
git clone https://github.com/e2pi3/CAU-SWE-BE.git
cd CAU-SWE-BE
```

### 2. 가상환경 생성 및 활성화 (최초 1회)

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (macOS/Linux)
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
# .env.example 참고해서 .env 파일 생성
cp .env.example .env
```

`.env` 파일에 본인 DB 정보 입력:

```
DB_PASSWORD=
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

| 주소 | 설명 |
|------|------|
| `http://localhost:8000` | 기본 응답 확인 |
| `http://localhost:8000/docs` | 자동 API 문서 |

### 6. 매번 작업 시작할 때

```bash
# venv 활성화 확인 (터미널 앞에 (venv) 있으면 OK)
venv\Scripts\activate

# develop 최신화
git checkout develop
git pull origin develop

# 내 브랜치로 이동
git checkout feature/my-part
```

---

## 📁 폴더 구조

```
CAU-SWE-BE/
├── app/
│   ├── main.py          # 서버 진입점 (API 추가될수록 분리 예정)
│   └── db.py            # DB 커넥션
├── venv/                # 가상환경 (GitHub에 올라가지 않음)
├── .env                 # DB 접속 정보 (GitHub에 올라가지 않음)
├── .env.example         # .env 양식 (GitHub에 올라감)
├── .gitignore
└── requirements.txt     # 패키지 목록
```

---

## 🌿 브랜치 전략

```
main        ← 최종 배포용 (직접 push 금지)
  └── develop   ← 통합 개발 브랜치 (PR로만 병합)
        ├── feature/user
        ├── feature/auth
        └── feature/models
```

---

## 💬 커밋 컨벤션

```
feat     : 새로운 기능 추가
fix      : 버그 수정
style    : 코드 포맷 변경
refactor : 코드 리팩토링
chore    : 패키지 설치, 설정 변경
docs     : 문서 수정
```

### 커밋 예시

```bash
git commit -m "feat: 유저 조회 API 구현"
git commit -m "fix: 로그인 토큰 오류 수정"
git commit -m "chore: sqlalchemy 패키지 추가"
```

---

## 🤝 협업 규칙

1. **직접 push 금지** `main`, `develop` 브랜치에는 절대 직접 push하지 않습니다.
2. **PR 필수** 작업 완료 후 Pull Request를 올리고 팀원 1명 이상 리뷰 후 병합합니다.
3. **패키지 추가 시** `pip freeze > requirements.txt` 실행 후 꼭 같이 push해주세요.
4. **`.env` 절대 push 금지** DB 비밀번호가 노출됩니다.
5. **작업 시작 전** 항상 `develop` 브랜치를 pull 받아 최신 상태를 유지합니다.

---

## ❓ 문의

문제가 생기면 팀 단톡방에 올려주세요! 😊