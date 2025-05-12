# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사 (여기 중요!! public 폴더 명시적으로 복사)
COPY . . 
COPY public/ ./public/

# 포트 지정
ENV PORT 8080
EXPOSE 8080

# FastAPI 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
