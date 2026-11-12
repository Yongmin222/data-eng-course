# bm25_josa.py — 조사가 붙으면 다른 낱말
from kb_corpus import bm25
for q in ["Airflow", "Airflow는", "도구", "도구는", "파티션", "Kafka 파티션", "작업 순서를 관리하는 도구는?"]:
    s = bm25.get_scores(q.split())
    print(f"{q!r:32} 최고점 {max(s):6.2f}")
