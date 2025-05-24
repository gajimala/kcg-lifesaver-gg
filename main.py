import json
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# CORS 설정 (정확한 도메인만 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcg-1099287947809.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 구조요청 저장 파일 경로
REQUESTS_FILE = "public/requests.json"

# 요청 모델
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # ms 단위

# 구조 요청 기록 저장 POST API
@app.post("/request-help")
def request_help(data: HelpRequest):
    try:
        # requests.json 파일이 없으면 빈 리스트로 생성
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        # 기존 요청 읽기
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests = json.load(f)

        now = time.time() * 1000
        # 24시간 이내 요청만 필터링
        recent_requests = [
            r for r in requests if now - r.get("timestamp", 0) < 86400000
        ]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # 다시 저장
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recent_requests, f, ensure_ascii=False, indent=2)

        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 구조 요청 전체 확인 GET API
@app.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# lifesavers.json 반환 API
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 루트 경로에 index.html 직접 바인딩
@app.get("/")
def root():
    return FileResponse("public/index.html")

# public 폴더 전체를 정적 파일로 서빙
app.mount("/", StaticFiles(directory="public", html=True), name="static")
