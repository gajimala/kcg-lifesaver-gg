from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
import time

router = APIRouter()

# 구조 요청 저장 경로
REQUESTS_FILE = "public/emergency/public/requests.json"

# 요청 모델
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # ms 단위

# 🔥 /emergency/ 접속 시 index.html 반환 (핵심!)
@router.get("/")
def emergency_root():
    return FileResponse("public/emergency/public/index.html")

# 구조 요청 기록 저장
@router.post("/request-help")
def request_help(data: HelpRequest):
    try:
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests = json.load(f)

        now = time.time() * 1000
        recent_requests = [
            r for r in requests if now - r.get("timestamp", 0) < 86400000
        ]

        recent_requests.append(data.dict())

        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recent_requests, f, ensure_ascii=False, indent=2)

        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 구조 요청 전체 확인
@router.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}
