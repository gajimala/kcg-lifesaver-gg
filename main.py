from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()

# ✅ 정확한 도메인만 허용 (Cloud Run 도메인)
origins = [
    "https://kcghelp-1099287947809.us-central1.run.app"
]

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 절대 ["*"] + credentials=True 금지
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ 정적 파일 서빙 (public/ 아래 HTML, JS 등)
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# ✅ lifesavers.json 서빙 라우터
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"error": str(e)}  # 🚨 에러 원인 확인용
