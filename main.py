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

# 정적 파일 서빙 (public 폴더 아래의 HTML 등)
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# /lifesavers 경로에서 JSON 반환
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"error": str(e)}  # 🔥 에러 원인을 직접 확인

