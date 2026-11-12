# compare3.py — 질문 셋 × 검색 셋
from kb_corpus import short
from retrievers import bm25_rank, vector_rank
from hybrid import hybrid_ids

def compare(query):
    print(f"\n=== {query} ===")
    for name, fn in [("BM25 ", bm25_rank), ("벡터 ", vector_rank), ("하이브리드", hybrid_ids)]:
        print(f"  {name}:", [short(i) for i in fn(query, 2)] or "없음")

compare("ERR-4021")
compare("Kafka 파티션")
compare("일정을 정해 두고 도는 작업")
