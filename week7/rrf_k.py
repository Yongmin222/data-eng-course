# rrf_k.py — RRF 의 k 를 바꾸면 합친 점수가 어떻게 달라지나
from retrievers import bm25_rank, vector_rank

q = "작업 순서를 관리하는 도구는?"
b, v = bm25_rank(q), vector_rank(q)
for k in [1, 60, 200]:
    scores = {}
    for ranking in [b, v]:
        for rank, d in enumerate(ranking):
            scores[d] = scores.get(d, 0) + 1 / (k + rank + 1)
    top = sorted(scores.values(), reverse=True)[:3]
    print(f"k={k:4} → 상위 세 점수 {[round(x, 4) for x in top]}  1등/3등 = {top[0] / top[2]:.2f}배")
