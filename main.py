from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

# 👉 **emergency 라우터 import**
from emergency.main import router as emergency_router  # 🟧 추가된 부분

app = FastAPI()

# ✅ 정확한 도메인만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcg-1099287947809.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ lifesavers API
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

# ✅ 루트 경로에 index.html 직접 바인딩 (💥 핵심)
@app.get("/")
def root():
    return FileResponse("public/index.html")

# ✅ 정적 파일 전체 mount
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# 🟧 **emergency 라우터 추가 (prefix 설정)**
app.include_router(emergency_router, prefix="/emergency")  # 🟧 추가된 부분
