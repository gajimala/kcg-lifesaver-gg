import json
import os
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 앱 생성
app = FastAPI()

# CORS 미들웨어 추가
# - 브라우저에서 다른 도메인 또는 포트로 API 요청 시 차단되는 문제 방지
# - 현재는 모든 도메인(*)에서 요청을 허용하지만, 배포 시에는 필요한 도메인만 허용할 것
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 모든 도메인 허용
    allow_credentials=True,   # 쿠키, 인증정보 허용 여부
    allow_methods=["*"],      # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],      # 모든 헤더 허용
)

# 구조 요청 데이터를 저장할 파일 경로 (리눅스 /tmp 디렉터리 사용)
REQUESTS_FILE = "/tmp/requests.json"

# 구조 요청 데이터 모델 정의
# - 클라이언트에서 받는 JSON 데이터가 이 형식이어야 함
class HelpRequest(BaseModel):
    lat: float          # 위도
    lng: float          # 경도 (lng로 통일)
    timestamp: float    # 요청 시각 (밀리초 단위)

# POST /requests
# - 새로운 구조 요청 데이터를 받아서 저장
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        # 요청 저장 파일이 없으면 빈 배열로 생성
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        # 기존 요청 기록 불러오기
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests = json.load(f)

        now = time.time() * 1000  # 현재 시각 (밀리초 단위)
        
        # 24시간 이내 요청만 필터링하여 보관 (오래된 데이터 자동 삭제)
        recent_requests = [
            r for r in requests if now - r.get("timestamp", 0) < 86400000
        ]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # 다시 파일에 저장 (indent=2 로 읽기 쉽게 저장)
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(recent_requests, f, ensure_ascii=False, indent=2)

        # 성공 응답, 현재 저장된 요청 개수 반환
        return {"status": "ok", "count": len(recent_requests)}

    except Exception as e:
        # 예외 발생 시 에러 메시지 반환
        return {"status": "error", "message": str(e)}

# GET /requests
# - 저장된 구조 요청 전체 목록 반환
@app.get("/requests")
def get_requests():
    try:
        with open(REQUESTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GET /lifesavers
# - lifesavers.json 파일 데이터 반환 (구조함 위치 등 정보)
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 정적 파일 서빙 (HTML, JS, CSS 등)
# - public 폴더 내 정적파일 제공
# - '/' 경로에서 index.html 등 열림
app.mount("/", StaticFiles(directory="public", html=True), name="static")
