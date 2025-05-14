from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()

# ✅ 먼저 /lifesavers 라우터를 선언
@app.get("/lifesavers")
def get_lifesavers():
    try:
        with open("public/lifesavers.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

# ✅ 그 다음에 정적 파일 마운트
app.mount("/", StaticFiles(directory="public", html=True), name="static")
