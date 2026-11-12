# hybrid.py — 두 순위를 RRF 로 합칩니다
from kb_corpus import text_by_id
from retrievers import bm25_rank, vector_rank

def rrf(rankings, k=60):
    """rankings: 각 검색기의 id 순위 리스트 목록. 1/(k+순위)를 합산합니다."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)

def hybrid_ids(query, top_k=3, k=60):
    return rrf([bm25_rank(query), vector_rank(query)], k=k)[:top_k]

def hybrid_search(query, top_k=3):
    return [text_by_id[i] for i in hybrid_ids(query, top_k)]

if __name__ == "__main__":
    # 이론 시간의 예시로 먼저 검증합니다
    assert rrf([["A", "B", "C"], ["B", "D", "A"]])[0] == "B"
    print("RRF 동작 확인")
