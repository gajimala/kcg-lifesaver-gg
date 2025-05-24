from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
import time

app = FastAPI()

# ==========================
# 1. CORS 설정 (도메인 허용)
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcg-1099287947809.us-central1.run.app"],  # 허용 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================
# 2. 구조 요청 기록 저장 파일 경로 지정
# ===================================
REQUESTS_FILE = "public/requests.json"

# ===================
# 3. 요청 데이터 모델 정의
# ===================
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # 밀리초 단위 타임스탬프

# =============================
# 4. 구조 요청 기록 저장 API
# =============================
@app.post("/request-help")
def request_help(data: HelpRequest):
    try:
        # requests.json 파일 없으면 빈 리스트로 생성
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        # 기존 요청 불러오기
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests = json.load(f)

        now = time.time() * 1000  # 현재시간(ms)
        # 24시간 이내 요청만 필터링
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # 갱신된 요청 기록 저장
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recent_requests, f, ensure_ascii=False, indent=2)

        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =============================
# 5. 전체 구조 요청 확인 API
# =============================
@app.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =============================
# 6. lifesavers.json 데이터 API
# =============================
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =============================
# 7. 루트 경로에 index.html 직접 바인딩
# =============================
@app.get("/")
def root():
    return FileResponse("public/index.html")

# =============================
# 8. public 폴더 전체를 정적 파일로 서빙
# =============================
app.mount("/", StaticFiles(directory="public", html=True), name="static")
