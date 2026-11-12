# emb_limits.py — 반대말 · 식별자
from rag_env import get_emb

emb = get_emb()
def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb)

a = emb.embed_query("이 작업은 성공했습니다")
b = emb.embed_query("이 작업은 실패했습니다")
print("성공 vs 실패:", round(cos(a, b), 3))

c = emb.embed_query("주문번호 A-1001")
d = emb.embed_query("주문번호 A-1002")
print("A-1001 vs A-1002:", round(cos(c, d), 3))
