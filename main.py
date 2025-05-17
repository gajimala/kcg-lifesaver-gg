from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.cloud import storage
import json
import os

app = FastAPI()

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (index.html 포함)
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# GCS에서 JSON 불러오기
@app.get("/lifesavers")
def get_lifesavers():
    client = storage.Client()
    bucket = client.bucket("kcg-lifesaver-json")  # 👉 너의 GCS 버킷 이름으로 수정할 것
    blob = bucket.blob("lifesavers.json")         # 👉 GCS에 올린 JSON 파일명

    data = blob.download_as_text(encoding="utf-8")
    return json.loads(data)

# (선택) 루트 수동 지정 시
@app.get("/")
def read_root():
    return FileResponse("public/index.html")
