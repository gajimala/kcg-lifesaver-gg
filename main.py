from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 허용 (필수 아님. 확장성 고려해 포함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# public 폴더 전체를 정적 서빙
app.mount("/", StaticFiles(directory="public", html=True), name="static")
