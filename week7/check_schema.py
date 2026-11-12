# check_schema.py — 정의서가 실제와 맞는지 대조합니다
import yaml
from qdrant_client import QdrantClient
from rag_env import get_emb

spec = yaml.safe_load(open("vector-schema.yaml", encoding="utf-8"))
cfg = QdrantClient(url="http://localhost:6333").get_collection(spec["collection"]).config.params.vectors
real_dim = len(get_emb().embed_query("차원 확인"))

assert spec["embedding"]["dim"] == spec["vector"]["size"], "정의서 안에서 dim 과 size 가 다릅니다"
assert real_dim == spec["embedding"]["dim"], f"모델 차원 불일치: 실제 {real_dim} vs 정의서 {spec['embedding']['dim']}"
assert cfg.size == spec["vector"]["size"], f"size 불일치: 컬렉션 {cfg.size} vs 정의서 {spec['vector']['size']}"
print("정의서와 실제 일치 —", cfg.size, cfg.distance)
