import json
import os
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

app = FastAPI()

REQUESTS_FILE = "public/requests.json"  # 구조요청 저장 파일

# 요청 모델 (lng로 통일)
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # ms 단위

# 구조 요청 기록
@app.post("/request-help")
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
@app.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# lifesavers.json 반환
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 정적 파일 서빙 (맨 마지막에 위치해야 함)
app.mount("/", StaticFiles(directory="public", html=True), name="static")
