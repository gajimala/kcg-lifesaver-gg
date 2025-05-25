import json
import time
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

BUCKET_NAME = os.environ.get("BUCKET_NAME", "lifesaver-requests")
REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

def get_bucket():
    storage_client = storage.Client()
    return storage_client.bucket(BUCKET_NAME)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HelpRequest(BaseModel):
    lat: float
    lng: float
    timestamp: float

def read_requests():
    blob = get_bucket().blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        return []
    data = blob.download_as_text()
    return json.loads(data)

def write_requests(data):
    blob = get_bucket().blob(REQUESTS_BLOB_NAME)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2))

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

@app.get("/requests")
def get_requests():
    try:
        return read_requests()
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

# 정적 파일 서비스
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# 엔트리포인트 분리 (Cloud Run에서도 작동하게)
def start():
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    start()
