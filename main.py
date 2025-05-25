import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정: 모든 도메인에서 자유롭게 API 호출 가능하도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 모든 출처 허용
    allow_credentials=True,       # 쿠키 인증도 허용
    allow_methods=["*"],          # 모든 HTTP 메소드 허용(GET, POST 등)
    allow_headers=["*"],          # 모든 헤더 허용
)

# Google Cloud Storage 버킷 및 객체 이름 지정
BUCKET_NAME = "lifesaver-requests"       # 실제 GCS 버킷명
REQUESTS_BLOB_NAME = "requests.json"      # 구조 요청 데이터 파일명
LIFESAVERS_BLOB_NAME = "lifesavers.json"  # 구조함 위치 데이터 파일명

# GCS 클라이언트와 버킷 객체 생성 (서비스 계정 인증 필요)
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# 구조 요청 데이터 모델 정의 (pydantic 사용)
class HelpRequest(BaseModel):
    lat: float        # 위도
    lng: float        # 경도
    timestamp: float  # 요청 발생 시간 (밀리초 단위)

# GCS에서 requests.json 파일 읽는 함수
def read_requests_from_gcs():
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():  # 파일이 없으면 빈 리스트 반환
        return []
    data = blob.download_as_text()  # 파일 내용을 문자열로 다운로드
    return json.loads(data)          # JSON 문자열을 파이썬 리스트로 변환

# GCS에 requests.json 파일 쓰는 함수
def write_requests_to_gcs(data):
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    # JSON 문자열로 변환 후 파일 업로드 (utf-8 기본 인코딩)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

# POST /requests 엔드포인트: 새로운 구조 요청을 저장
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        requests = read_requests_from_gcs()  # 기존 요청 불러오기
        now = time.time() * 1000             # 현재 시간 (밀리초)
        # 24시간(86400000ms) 이내의 요청만 필터링해서 유지
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]
        recent_requests.append(data.dict())  # 새 요청 추가
        write_requests_to_gcs(recent_requests)  # 다시 GCS에 저장
        return {"status": "ok", "count": len(recent_requests)}  # 성공 응답
    except Exception as e:
        return {"status": "error", "message": str(e)}  # 에러 발생 시 메시지 반환

# GET /requests 엔드포인트: 저장된 모든 구조 요청 반환
@app.get("/requests")
def get_requests():
    try:
        return read_requests_from_gcs()  # GCS에서 요청 목록 읽어서 반환
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GET /lifesavers 엔드포인트: lifesavers.json 데이터 반환
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

# 정적 파일 서비스 (public 폴더에 있는 파일을 기본 HTML로 서빙)
app.mount("/", StaticFiles(directory="public", html=True), name="static")
