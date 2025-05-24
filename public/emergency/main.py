import json
import os
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# ✅ 구조 요청 기록 저장 위치 (정확한 경로 반영)
REQUESTS_FILE = "public/emergency/public/requests.json"

# ✅ 구조 요청 요청 데이터 모델 정의
class HelpRequest(BaseModel):
    lat: float        # 위도
    lng: float        # 경도
    timestamp: float  # 요청 시각 (밀리초 기준)

# ✅ 구조 요청 저장 API (최근 24시간 이내 요청만 유지)
@app.post("/request-help")
def request_help(data: HelpRequest):
    try:
        # 파일이 없다면 빈 배열로 초기화
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        # 기존 요청 불러오기
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests = json.load(f)

        now = time.time() * 1000  # 현재 시간(ms)
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]

        # 새로운 요청 추가
        recent_requests.append(data.dict())

        # 파일에 저장
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recent_requests, f, ensure_ascii=False, indent=2)

        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ 구조 요청 전체 반환 API
@app.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ lifesavers.json 반환 API
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/emergency/public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ✅ 정적 파일 서빙 (lifesaver-map HTML 포함)
app.mount("/", StaticFiles(directory="public/emergency/public", html=True), name="static")
