from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from google.cloud import storage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/lifesavers")
def get_lifesavers():
    client = storage.Client()
    bucket = client.bucket("kcg-lifesaver-json")  # ← 여기를 네 실제 버킷 이름으로 바꿔
    blob = bucket.blob("lifesavers.json")

    data = blob.download_as_text(encoding="utf-8")
    return json.loads(data)
