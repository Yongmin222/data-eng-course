# kb_bad.py — 일부러 깨뜨려 봅니다(실습용 별도 컬렉션)
import uuid
from qdrant_client.models import VectorParams, Distance, PointStruct
from kb import client, emb, splitter
from minio_env import BUCKET, read_text

TMP = "idempotency_test"
if client.collection_exists(TMP):
    client.delete_collection(TMP)
client.create_collection(
    collection_name=TMP,
    vectors_config=VectorParams(size=len(emb.embed_query("차원")), distance=Distance.COSINE),
)

def ingest_bad():
    chunks = splitter.split_text(read_text(BUCKET, "notes/notes.txt"))
    vectors = emb.embed_documents(chunks)
    client.upsert(collection_name=TMP, points=[
        PointStruct(id=str(uuid.uuid4()), vector=v, payload={"text": c})   # 매번 새 id
        for c, v in zip(chunks, vectors)
    ])

ingest_bad(); print(client.count(TMP))
ingest_bad(); print(client.count(TMP))   # 두 배가 됩니다
client.delete_collection(TMP)
