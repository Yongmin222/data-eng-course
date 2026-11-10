# 6주차 산출물 — 실시간 CDC 파이프라인

## 1. 구성
| 서비스 | 역할 | 포트 |
|---|---|---|
| kafka | 이벤트 중간 저장소 | 9092(외부) · 29092(내부) |
| mysql | 원천 DB | 3306 |
| connect | Debezium 소스 + S3 싱크 | 8083 |
| minio | 적재 대상 (S3 호환) | 9000 · 9001 |

## 2. 데이터 흐름
MySQL(binlog) → Debezium → Kafka(shop.shop.orders) → S3 Sink → MinIO(cdc-raw)

## 3. 토픽 구성
| 토픽 | 용도 |
|---|---|
| orders | 6-3 파이썬 Producer/Consumer 실습용 |
| orders-test | 6-3 실습 중 테스트용 |
| shop.shop.orders | CDC 변경 이벤트 (서버명.DB명.테이블명) |
| shop | 스키마 변경(DDL) 이벤트 |
| schema-changes.shop | Debezium이 테이블 구조 이력을 보관 |
| connect_configs | Connect 커넥터 설정 저장 |
| connect_offsets | 소스 커넥터가 읽은 위치(binlog) 저장 |
| connect_statuses | 커넥터·태스크 상태 저장 |
| __consumer_offsets | 컨슈머 그룹이 어디까지 읽었는지 저장 |

## 4. 제출 파일
- docker-compose.yml
- register-mysql.json (Debezium 소스 커넥터)
- sink-minio.json (S3 싱크 커넥터)

## 5. 실습 코드 (6-3, 6-4)
- producer.py : Kafka로 주문 메시지를 보내는 Producer
- consumer.py : 토픽을 구독해 메시지를 읽는 Consumer
- cdc_reader.py : CDC 변경 이벤트(op, after)를 읽고, DELETE 뒤의 툼스톤(값 없는 메시지)도 구분해 처리

## 6. 확인한 것
- op = r/c/u/d 네 종류를 모두 관찰
- MySQL INSERT → MinIO 파일 생성까지 엔드투엔드 통과
- flush.size 만큼 모여야 파일이 생기는 것을 확인

## 7. 남은 개선점
- flush.size=5 때문에 5건이 안 모이면 파일이 생기지 않고, Sink 컨슈머 그룹에 LAG 1~4가 남는 것을 확인했다. 트래픽이 적을 때 적재가 지연될 수 있으므로 시간 기준 flush(`rotate.schedule.interval.ms`)를 함께 설정하는 개선이 필요하다.
