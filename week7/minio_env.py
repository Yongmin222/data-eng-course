# minio_env.py — 7-4 · 7-5 가 함께 쓰는 MinIO 접속(로컬 컨테이너 rag-minio)
import os
from minio import Minio
mc = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),   # 8주차 Airflow 안에서는 rag-minio:9000
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,          # 로컬 컨테이너는 HTTP이므로 False
)
BUCKET = "raw-docs"
def read_text(bucket, key):
    body = mc.get_object(bucket, key)
    try:
        return body.read().decode("utf-8")
    finally:
        body.close()
        body.release_conn()      # 이걸 빼면 연결이 새어 나갑니다
