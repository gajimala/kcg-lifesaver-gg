import json
import time
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# **버킷 이름 꼭 여기에 정확히 적으세요**
BUCKET_NAME = "lifesaver-requests"  # 여기 수정해주세요

REQUESTS_BLOB_NAME = "requests.json"
LIFESAVERS_BLOB_NAME = "lifesavers.json"

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

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
    blob = bucket.blob(REQUESTS_BLOB_NAME)
    if not blob.exists():
        return []
    data = blob.download_as_text()
    return json.loads(data)

def write_requests(data):
    blob = bucket.blob(REQUESTS_BLOB_NAME)
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
        blob = bucket.blob(LIFESAVERS_BLOB_NAME)
        if not blob.exists():
            return {"status": "error", "message": "lifesavers.json not found"}
        data = blob.download_as_text()
        return json.loads(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.mount("/", StaticFiles(directory="public", html=True), name="static")
