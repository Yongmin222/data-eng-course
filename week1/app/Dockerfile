# Dockerfile — ~/data-eng/week1/app/Dockerfile로 저장
FROM python:3.12-slim

# 컨테이너 안 작업 디렉터리
WORKDIR /app

# 의존성 먼저 설치 (잘 안 바뀌는 층을 먼저)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드는 나중에 복사 (자주 바뀌는 층을 나중에)
COPY . .

# 컨테이너 시작 시 실행할 명령
CMD ["python", "app.py"]
