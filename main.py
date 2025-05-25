import json
import time
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# 환경변수로 버킷 이름 관리 (로컬 개발 시 기본값 제공)
BUCKET_NAME = os.environ.get("BUCKET_NAME", "lifesaver-requests")
REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

# Cloud Run에서는 앱 시작 시 인증 실패 방지를 위해
# storage.Client()와 bucket 선언을 함수로 분리
def get_bucket():
    storage_client = storage.Client()
    return storage_client.bucket(BUCKET_NAME)

app = FastAPI()

# CORS 허용 설정: 프론트엔드에서 자유롭게 접근 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 구조요청 데이터 포맷 정의
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float

# requests.json 읽기 함수
def read_requests():
    blob = get_bucket().blob(REQUESTS_BLOB_NAME)
    if not blob.exists():  # 파일이 없으면 빈 리스트 반환
        return []
    data = blob.download_as_text()
    return json.loads(data)

# requests.json 쓰기 함수
def write_requests(data):
    blob = get_bucket().blob(REQUESTS_BLOB_NAME)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

# 구조요청 추가 API (POST /requests)
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        requests = read_requests()
        now = time.time() * 1000  # 현재 시간 (밀리초)
        # 최근 24시간 이내 요청만 유지
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]
        recent_requests.append(data.dict())  # 새 요청 추가
        write_requests(recent_requests)
        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 구조요청 목록 조회 API (GET /requests)
@app.get("/requests")
def get_requests():
    try:
        return read_requests()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 인명구조함 목록 조회 API (GET /lifesavers)
@app.get("/lifesavers")
def get_lifesavers():
    try:
        blob = get_bucket().blob(LIFESAVERS_BLOB_NAME)
        if not blob.exists():
            return {"status": "error", "message": "lifesavers.json not found"}
        data = blob.download_as_text()
        return json.loads(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 디버그용 버킷 상태 확인 API (GET /debug-bucket)
@app.get("/debug-bucket")
def debug_bucket():
    try:
        bucket = get_bucket()
        blob_requests = bucket.blob(REQUESTS_BLOB_NAME)
        requests_exists = blob_requests.exists()
        blob_lifesavers = bucket.blob(LIFESAVERS_BLOB_NAME)
        lifesavers_exists = blob_lifesavers.exists()
        return {
            "bucket_name": BUCKET_NAME,
            "requests_json_exists": requests_exists,
            "lifesavers_json_exists": lifesavers_exists,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 정적 파일 (HTML, JS 등) 서비스: public 폴더 기준
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# 로컬 실행 시 사용할 엔트리포인트
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
