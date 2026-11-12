# kb_corpus.py — Qdrant(lecture_kb)의 조각을 모두 내려받아 BM25 색인을 만듭니다
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
COLLECTION = "lecture_kb"
def load():
    records, _ = client.scroll(collection_name=COLLECTION, limit=1000, with_payload=True)
    corpus = [r.payload["text"] for r in records]
    ids = [str(r.id) for r in records]           # id 타입을 str로 통일해 둡니다
    bm25 = BM25Okapi([doc.split() for doc in corpus])   # 공백으로 자른 낱말이 토큰
    return records, corpus, ids, bm25
records, corpus, ids, bm25 = load()
text_by_id = {i: t for i, t in zip(ids, corpus)}
def short(doc_id, n=20):
    """id 의 본문 앞부분을 한 줄로 — 결과를 나란히 볼 때 씁니다"""
    return text_by_id[doc_id].replace("\n", " ")[:n]
if __name__ == "__main__":
    print("색인된 문서 수:", len(corpus))
    print("id 예:", ids[0])
