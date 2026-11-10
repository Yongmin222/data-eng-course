# cdc_reader.py — 변경 이벤트를 사람이 읽기 좋게
import json
from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "cdc-reader",
    "auto.offset.reset": "earliest",
})
c.subscribe(["shop.shop.orders"])

OP = {"r": "스냅숏", "c": "INSERT", "u": "UPDATE", "d": "DELETE"}
try:
    while True:
        msg = c.poll(1.0)
        if msg is None or msg.error():
            continue
        if msg.value() is None:                # DELETE 뒤에 오는 툼스톤(값 없음)
            print(f"[툼스톤] id={json.loads(msg.key())['payload']['id']} — 값이 없는 메시지")
            continue
        evt = json.loads(msg.value().decode("utf-8"))
        payload = evt.get("payload", evt)      # 스키마 포함 여부에 따라
        op = payload.get("op")
        before, after = payload.get("before"), payload.get("after")
        print(f"[{OP.get(op, op)}] before={before} after={after}")
except KeyboardInterrupt:
    pass
finally:
    c.close()
