# kb.py — MinIO 문서를 잘라 임베딩해 Qdrant(lecture_kb)에 넣는 부품
import os, uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (VectorParams, Distance, PointStruct,
                                  Filter, FieldCondition, MatchValue, FilterSelector)
from minio_env import mc, BUCKET, read_text
from rag_env import get_emb

emb = get_emb()
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))   # 8주차 Airflow 안에서는 http://qdrant:6333
COLLECTION = "lecture_kb"
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)   # 7-2 에서 정한 값

def ensure_collection():
    if not client.collection_exists(COLLECTION):
        dim = len(emb.embed_query("차원 확인"))
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def ingest(prefix=""):
    ensure_collection()
    total = 0
    for obj in mc.list_objects(BUCKET, prefix=prefix, recursive=True):
        if not obj.object_name.endswith(".txt"):
            continue
        text = read_text(BUCKET, obj.object_name)
        source = f"minio://{BUCKET}/{obj.object_name}"
        chunks = splitter.split_text(text)
        vectors = emb.embed_documents(chunks)          # 배치로 한 번에
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{i}")),   # 같은 입력이면 같은 id
                vector=v,
                payload={"text": c, "source": source, "chunk_index": i},
            )
            for i, (c, v) in enumerate(zip(chunks, vectors))
        ]
        client.upsert(collection_name=COLLECTION, points=points)
        print(f"{source} → {len(points)} chunks")
        total += len(points)
    return total

def count_of(source):
    return client.count(
        COLLECTION,
        count_filter=Filter(must=[FieldCondition(key="source", match=MatchValue(value=source))]),
    ).count

def reingest(object_name):
    """해당 문서의 옛 조각을 모두 지우고 다시 넣습니다"""
    source = f"minio://{BUCKET}/{object_name}"
    client.delete(
        collection_name=COLLECTION,
        points_selector=FilterSelector(filter=Filter(must=[
            FieldCondition(key="source", match=MatchValue(value=source))
        ])),
    )
    return ingest(prefix=object_name)
