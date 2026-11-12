# kb_idem.py — 한 번 더 돌려 개수를 잽니다
from kb import ingest, client, COLLECTION

before = client.count(COLLECTION).count
ingest()
after = client.count(COLLECTION).count
print(f"{before} → {after}")
assert before == after, "멱등하지 않습니다 — id 생성 방식을 확인하세요"
print("멱등 확인")
