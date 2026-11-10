# consumer.py
import json
from collections import defaultdict
from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-agg",
    "auto.offset.reset": "earliest",
})
c.subscribe(["orders"])

totals = defaultdict(int)
try:
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"오류: {msg.error()}")
            continue
        order = json.loads(msg.value().decode("utf-8"))
        totals[order["customer"]] += order["amount"]
        print(f"[p{msg.partition()}:{msg.offset()}] {order} | 누적 {dict(totals)}")
except KeyboardInterrupt:
    pass
finally:
    c.close()              # 그룹에서 정상 탈퇴 + 오프셋 정리
