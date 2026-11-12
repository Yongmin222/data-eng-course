# bm25_code.py — 있는 코드와 없는 코드
from retrievers import bm25, emb, client, COLLECTION
from kb_corpus import short

for code in ["ERR-4021", "ERR-4012"]:
    s = bm25.get_scores(code.split())
    hit = client.query_points(collection_name=COLLECTION, query=emb.embed_query(code), limit=1).points[0]
    print(f"{code}: BM25 최고점 {max(s):.2f} · 벡터 1등 {hit.score:.3f} {short(str(hit.id))}")
