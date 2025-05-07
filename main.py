from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# /lifesavers: lon → lng 변환해서 반환
@app.get("/lifesavers")
def get_lifesavers():
    with open("public/lifesavers.json", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        if "lon" in item:
            item["lng"] = item.pop("lon")
    return data
