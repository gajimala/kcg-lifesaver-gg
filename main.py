from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcghelp-1099287947809.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ ✅ 정적 파일을 먼저 마운트 (순서 중요)
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# ✅ lifesavers 라우트는 반드시 그 뒤에 정의해야 작동 보장됨
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}
