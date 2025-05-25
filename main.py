import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Google Cloud Storage 라이브러리 임포트
from google.cloud import storage

# FastAPI 앱 생성
app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=True,   
    allow_methods=["*"],      
    allow_headers=["*"],      
)

# GCS 버킷명과 객체명 지정
BUCKET_NAME = "lifesaver-requests"   # 네가 알려준 실제 버킷 이름
REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

# GCS 클라이언트 및 버킷 객체 생성
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# 구조 요청 데이터 모델 정의
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float

# GCS에서 requests.json 읽기 함수
def read_requests_from_gcs():
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        return []
    data = blob.download_as_text()
    return json.loads(data)

# GCS에 requests.json 쓰기 함수
def write_requests_to_gcs(data):
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

# POST /requests - 새 구조 요청 저장
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        # GCS에서 기존 요청 불러오기
        requests = read_requests_from_gcs()

        now = time.time() * 1000
        
        # 24시간 이내 요청만 필터링
        recent_requests = [
            r for r in requests if now - r.get("timestamp", 0) < 86400000
        ]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # GCS에 저장
        write_requests_to_gcs(recent_requests)

        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GET /requests - 저장된 요청 전체 반환
@app.get("/requests")
def get_requests():
    try:
        return read_requests_from_gcs()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GET /lifesavers - lifesavers.json GCS에서 읽기
@app.get("/lifesavers")
def get_lifesavers():
    try:
        blob = bucket.blob(LIFESAVERS_BLOB_NAME)
        if not blob.exists():
            return {"status": "error", "message": "lifesavers.json not found"}
        data = blob.download_as_text()
        return json.loads(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 정적 파일 서빙 (로컬 public 폴더 그대로)
app.mount("/", StaticFiles(directory="public", html=True), name="static")
