import json
import time
import os  # 환경변수 읽기용 추가
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# -------------------------
# Google Cloud Storage 관련 설정
# -------------------------
# 실제 사용하는 GCS 버킷 이름
BUCKET_NAME = "lifesaver-requests"  

# 버킷 내 JSON 파일 이름
REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

# GCS 클라이언트 생성 및 버킷 객체 얻기
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# -------------------------
# FastAPI 앱 생성 및 설정
# -------------------------
app = FastAPI()

# CORS 설정: 모든 출처 허용 (배포 시 꼭 필요한 출처만 허용 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 데이터 모델 정의
# -------------------------
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float  # 밀리초 단위 타임스탬프

# -------------------------
# GCS에서 요청 데이터 읽기
# -------------------------
def read_requests():
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        return []
    data = blob.download_as_text()
    return json.loads(data)

# -------------------------
# GCS에 요청 데이터 쓰기
# -------------------------
def write_requests(data):
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

# -------------------------
# POST /requests
# 새 요청 저장 (최근 24시간 이내 요청만 유지)
# -------------------------
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        requests = read_requests()
        now = time.time() * 1000
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]
        recent_requests.append(data.dict())
        write_requests(recent_requests)
        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# GET /requests
# 저장된 요청 전체 반환
# -------------------------
@app.get("/requests")
def get_requests():
    try:
        return read_requests()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# GET /lifesavers
# lifesavers.json 반환
# -------------------------
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

# -------------------------
# 디버그용: 버킷 및 파일 존재 확인
# -------------------------
@app.get("/debug-bucket")
def debug_bucket():
    try:
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

# -------------------------
# 정적 파일 서빙 설정
# 'public' 폴더의 index.html 등 제공
# -------------------------
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# -------------------------
# uvicorn 직접 실행 시 환경변수 PORT 사용해 실행
# Google Cloud Run 등에서 환경변수 PORT 제공
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # 기본 8080 포트 사용
    uvicorn.run(app, host="0.0.0.0", port=port)
