import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Google Cloud Storage 라이브러리 임포트
from google.cloud import storage

# 운영체제 환경변수 사용 위해 import
import os

# FastAPI 앱 생성
app = FastAPI()

# CORS 미들웨어 설정
# 모든 도메인에서 API 호출 허용 (개발 시 편리, 운영 시에는 도메인 제한 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 모든 오리진 허용
    allow_credentials=True,   
    allow_methods=["*"],      # 모든 HTTP 메서드 허용
    allow_headers=["*"],      
)

# Google Cloud Storage 버킷 및 객체 이름 설정
BUCKET_NAME = "lifesaver-requests"   # GCS 버킷명 (실제 배포 시 본인 버킷명으로 변경)
REQUESTS_BLOB_NAME = "requests.json"  # 구조 요청 데이터 저장 객체명
LIFESAVERS_BLOB_NAME = "lifesavers.json"  # 구조함 위치 데이터 저장 객체명

# GCS 클라이언트 및 버킷 객체 생성
storage_client = storage.Client()  
bucket = storage_client.bucket(BUCKET_NAME)

# 구조 요청 데이터 모델 정의 (위도, 경도, 타임스탬프)
class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float

# GCS에서 requests.json 파일을 읽는 함수
def read_requests_from_gcs():
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        return []  # 파일 없으면 빈 리스트 반환
    data = blob.download_as_text()  # 텍스트로 다운로드
    return json.loads(data)  # JSON 파싱 후 반환

# GCS에 requests.json 파일을 쓰는 함수
def write_requests_to_gcs(data):
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    # JSON 문자열로 변환하여 UTF-8로 업로드 (indent=2는 보기 편하게 들여쓰기)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2)) 

# POST /requests
# 클라이언트에서 구조 요청 데이터를 받아 GCS에 저장
@app.post("/requests")
def request_help(data: HelpRequest):
    try:
        # 기존 요청 데이터 불러오기
        requests = read_requests_from_gcs()

        # 현재 시간 밀리초 단위
        now = time.time() * 1000

        # 24시간(86400000ms) 이내 요청만 필터링 (오래된 데이터 제거)
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < 86400000]

        # 새 요청 추가
        recent_requests.append(data.dict())

        # GCS에 갱신된 리스트 저장
        write_requests_to_gcs(recent_requests)

        # 성공 시 요청 개수 반환
        return {"status": "ok", "count": len(recent_requests)}
    except Exception as e:
        # 에러 발생 시 메시지 반환
        return {"status": "error", "message": str(e)}

# GET /requests
# 저장된 구조 요청 전체를 GCS에서 읽어 반환
@app.get("/requests")
def get_requests():
    try:
        return read_requests_from_gcs()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GET /lifesavers
# lifesavers.json 데이터를 GCS에서 읽어 반환
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

# 정적 파일 서빙 설정
# / 경로로 들어오는 요청은 로컬 public 폴더에서 html, js, css 등 정적 파일 서빙
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# ★ 중요 ★
# Cloud Run에서는 이 스크립트를 직접 실행할 때 (main으로서)
# 환경변수 PORT를 읽어 해당 포트로 서버 실행
# (Cloud Run이 지정하는 포트 환경변수에 맞춰야 정상 작동)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # PORT 환경변수 없으면 8080 기본값
    uvicorn.run("main:app", host="0.0.0.0", port=port)
