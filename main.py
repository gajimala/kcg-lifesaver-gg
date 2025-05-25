import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# -------------------------
# Google Cloud Storage 관련 설정
# -------------------------
# 실제로 사용하는 GCS 버킷 이름을 정확히 입력하세요.
BUCKET_NAME = "lifesaver-requests"  

# 버킷 내에 저장된 JSON 파일 이름
REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

# GCS 클라이언트 생성 및 버킷 객체 얻기
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# -------------------------
# FastAPI 앱 생성 및 설정
# -------------------------
app = FastAPI()

# CORS 설정
# 브라우저에서 다른 도메인 혹은 포트에서 오는 요청을 허용하기 위함
# 배포 시에는 allow_origins를 제한하는 것이 안전
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 모든 도메인에서 요청 허용
    allow_credentials=True,   
    allow_methods=["*"],      
    allow_headers=["*"],      
)

# -------------------------
# 데이터 모델 정의
# -------------------------
# 클라이언트가 보내는 구조 요청 데이터의 JSON 형식을 검증하기 위한 Pydantic 모델
class HelpRequest(BaseModel):
    lat: float           # 위도
    lng: float           # 경도
    timestamp: float     # 요청 시각 (밀리초 단위)

# -------------------------
# Google Cloud Storage에서 요청 데이터를 읽는 함수
# -------------------------
def read_requests():
    """
    GCS 버킷에서 요청 데이터를 읽어 JSON 리스트로 반환
    파일이 없으면 빈 리스트 반환
    """
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        # 파일이 없으면 빈 리스트 반환
        return []
    # 파일 내용을 문자열로 다운로드
    data = blob.download_as_text()
    # JSON 파싱 후 반환
    return json.loads(data)

# -------------------------
# Google Cloud Storage에 요청 데이터를 저장하는 함수
# -------------------------
def write_requests(data):
    """
    데이터 리스트를 JSON 문자열로 변환해 GCS에 업로드
    """
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

# -------------------------
# POST /requests
# 클라이언트가 보낸 구조 요청을 저장
# -------------------------
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        # 기존 요청 읽기
        requests = read_requests()
        now = time.time() * 1000  # 현재 시간 (밀리초)
        
        # 24시간 이내 요청만 필터링 (오래된 요청 삭제)
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # 변경된 요청 리스트를 GCS에 저장
        write_requests(recent_requests)

        # 성공 응답 및 저장된 요청 개수 반환
        return {"status": "ok", "count": len(recent_requests)}

    except Exception as e:
        # 오류 발생 시 에러 메시지 반환
        return {"status": "error", "message": str(e)}

# -------------------------
# GET /requests
# 저장된 모든 구조 요청을 반환
# -------------------------
@app.get("/requests")
def get_requests():
    try:
        # GCS에서 읽어 반환
        return read_requests()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# GET /lifesavers
# lifesavers.json 파일 데이터를 반환
# -------------------------
@app.get("/lifesavers")
def get_lifesavers():
    try:
        # lifesavers.json 파일의 Blob 객체 얻기
        blob = bucket.blob(LIFESAVERS_BLOB_NAME)
        if not blob.exists():
            return {"status": "error", "message": "lifesavers.json not found"}

        # 파일 내용 다운로드 후 JSON 파싱
        data = blob.download_as_text()
        return json.loads(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# /debug-bucket 엔드포인트 (디버깅용)
# 버킷 접근 상태 및 파일 존재 여부 확인용
# -------------------------
@app.get("/debug-bucket")
def debug_bucket():
    try:
        # 요청 파일 존재 여부 확인
        blob_requests = bucket.blob(REQUESTS_BLOB_NAME)
        requests_exists = blob_requests.exists()

        # lifesavers 파일 존재 여부 확인
        blob_lifesavers = bucket.blob(LIFESAVERS_BLOB_NAME)
        lifesavers_exists = blob_lifesavers.exists()

        # 버킷 이름과 파일 존재 여부 반환
        return {
            "bucket_name": BUCKET_NAME,
            "requests_json_exists": requests_exists,
            "lifesavers_json_exists": lifesavers_exists,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------
# 정적 파일 서빙 설정
# public 폴더 내 HTML, JS, CSS 등을 서비스함
# '/' 접속 시 index.html 자동 서빙
# -------------------------
app.mount("/", StaticFiles(directory="public", html=True), name="static")
