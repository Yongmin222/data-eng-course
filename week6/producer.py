# producer.py
import json, random, time
from confluent_kafka import Producer

p = Producer({"bootstrap.servers": "localhost:9092"})

def on_delivery(err, msg):
    if err is not None:
        print(f"전송 실패: {err}")
    else:
        print(f"전송 완료 topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")

customers = ["user1", "user2", "user3"]
try:
    for i in range(30):
        order = {
            "order_id": i,
            "customer": random.choice(customers),
            "amount": random.randint(1000, 50000),
        }
        p.produce(
            "orders",
            key=order["customer"],
            value=json.dumps(order, ensure_ascii=False),
            on_delivery=on_delivery,
        )
        p.poll(0)          # 콜백 처리
        time.sleep(1)
finally:
    p.flush()              # 버퍼를 비우고 종료
