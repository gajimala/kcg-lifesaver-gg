import json
import os
import time
from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

app = FastAPI()

REQUESTS_FILE = "/tmp/requests.json"  # 구조요청 저장 파일

# 요청 모델 (lng로 통일)
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # ms 단위

# 구조 요청 기록
@app.post("/requests")
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
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

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

# 기존 lifesaver_count API
@app.get("/lifesaver_count")
def lifesaver_count(
    left: float = Query(...),
    bottom: float = Query(...),
    right: float = Query(...),
    top: float = Query(...)
):
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            lifesavers = json.load(f)

        count = sum(
            1 for item in lifesavers
            if left <= item["lng"] <= right and bottom <= item["lat"] <= top
        )
        return {"count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 줌 레벨에 따라 필터링해서 마커 리스트 또는 count만 반환하는 새 API
@app.get("/lifesavers_filtered")
def lifesavers_filtered(
    left: float = Query(...),
    bottom: float = Query(...),
    right: float = Query(...),
    top: float = Query(...),
    zoom: int = Query(...)
):
    try:
        zoom_threshold = 7  # 필요에 따라 조정 가능

        with open("public/lifesavers.json", encoding="utf-8") as f:
            lifesavers = json.load(f)

        filtered = [
            item for item in lifesavers
            if left <= item["lng"] <= right and bottom <= item["lat"] <= top
        ]

        if zoom < zoom_threshold:
            return {"count": len(filtered), "lifesavers": []}
        else:
            return {"count": len(filtered), "lifesavers": filtered}
    except Exception as e:
        return {"status": "error", "message": str(e)}
