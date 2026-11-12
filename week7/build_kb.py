# build_kb.py — 지식베이스 구축 스크립트 (주차 산출물 ②)
"""MinIO의 문서를 읽어 Qdrant에 색인한다. 몇 번 실행해도 결과가 같다."""
import os, sys, uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (VectorParams, Distance, PointStruct,
                                  Filter, FieldCondition, MatchValue, FilterSelector)
from minio_env import mc, read_text      # 7-4 의 접속 정보
from rag_env import get_emb              # 7-1 의 모델 선택(OpenAI 또는 Ollama)

BUCKET = os.getenv("BUCKET", "raw-docs")
COLLECTION = os.getenv("COLLECTION", "lecture_kb")
CHUNK = int(os.getenv("CHUNK_SIZE", "300"))

emb = get_emb()
qc = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))   # 8주차 Airflow 안에서는 http://qdrant:6333
splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK, chunk_overlap=CHUNK // 10)


def ensure_collection(dim):
    if not qc.collection_exists(COLLECTION):
        qc.create_collection(COLLECTION,
                             vectors_config=VectorParams(size=dim, distance=Distance.COSINE))


def ingest_one(key):
    source = f"minio://{BUCKET}/{key}"
    text = read_text(BUCKET, key)

    # 옛 조각을 지우고 다시 넣는다 — 문서가 짧아져도 잔재가 남지 않는다
    qc.delete(COLLECTION, points_selector=FilterSelector(filter=Filter(
        must=[FieldCondition(key="source", match=MatchValue(value=source))])))

    chunks = splitter.split_text(text)
    vectors = emb.embed_documents(chunks)
    qc.upsert(COLLECTION, points=[
        PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{i}")),
                    vector=v, payload={"text": c, "source": source, "chunk_index": i})
        for i, (c, v) in enumerate(zip(chunks, vectors))
    ])
    return len(chunks)


def main():
    ensure_collection(len(emb.embed_query("차원 확인")))
    total = 0
    for obj in mc.list_objects(BUCKET, recursive=True):
        if obj.object_name.endswith(".txt"):
            n = ingest_one(obj.object_name)
            print(f"  {obj.object_name} → {n}")
            total += n
    print(f"적재 {total} 조각 · 총 {qc.count(COLLECTION).count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
