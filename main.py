from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()

# ✅ 정확한 도메인만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kcghelp-1099287947809.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ lifesavers 먼저 선언
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

# ✅ 마지막에 정적 파일 mount
app.mount("/", StaticFiles(directory="public", html=True), name="static")
import os
print("🔥 index.html exists:", os.path.exists("public/index.html"))

