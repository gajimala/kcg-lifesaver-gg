from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json

# emergency 서브 라우터 import
from emergency.main import router as emergency_router

app = FastAPI()

# CORS 설정 (정확한 도메인만 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcg-1099287947809.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# lifesavers API
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

# 루트 경로에 index.html 직접 바인딩
@app.get("/")
def root():
    return FileResponse("public/index.html")

# public 폴더 전체를 정적 파일로 서빙
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# emergency API 라우터 포함 (prefix: /emergency)
app.include_router(emergency_router, prefix="/emergency")

# emergency 정적 파일도 함께 서빙 (경로: /emergency/static)
app.mount(
    "/emergency/static",
    StaticFiles(directory="public/emergency/public"),
    name="emergency_static",
)
