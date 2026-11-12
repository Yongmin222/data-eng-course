# retrievers.py — 키워드(BM25) 순위와 의미(벡터) 순위를 같은 모양(str id 목록)으로
from kb_corpus import client, COLLECTION, bm25, ids
from rag_env import get_emb

emb = get_emb()   # 7-4 와 같은 임베딩 모델이어야 합니다

def bm25_rank(query, top_k=5):
    scores = bm25.get_scores(query.split())
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [ids[i] for i in order[:top_k] if scores[i] > 0]   # 0점은 못 찾은 것

def vector_rank(query, top_k=5):
    hits = client.query_points(
        collection_name=COLLECTION,
        query=emb.embed_query(query),
        limit=top_k,
    ).points
    return [str(h.id) for h in hits]

if __name__ == "__main__":
    q = "작업 순서를 관리하는 도구는?"
    print("BM25  :", bm25_rank(q))
    print("Vector:", vector_rank(q))
