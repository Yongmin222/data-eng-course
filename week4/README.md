# 4주차 산출물 — MinIO · Iceberg · Trino 레이크하우스

MinIO(오브젝트 스토리지) 위에 Iceberg 테이블을 만들고, Spark로 적재한 테이블을 Trino로 조회하는 레이크하우스입니다. 두 엔진이 같은 Iceberg REST 카탈로그를 바라보도록 구성했고, 같은 테이블을 양쪽에서 읽고 쓰는 것을 직접 확인했습니다. 구조는 [lakehouse_architecture.md](lakehouse_architecture.md)에 다이어그램과 함께 정리했습니다.

## 구성

| 서비스 | 이미지 | 역할 | 접속 |
|---|---|---|---|
| minio | pgsty/minio | S3 호환 오브젝트 스토리지 (`raw`, `warehouse` 버킷) | S3 API `9000`, 콘솔 `9001` |
| mc | pgsty/mc | 버킷 확인·파일 업로드용 CLI | `docker compose exec mc ...` |
| rest | tabulario/iceberg-rest | Iceberg REST 카탈로그 (SQLite 파일을 볼륨에 저장) | `8181` |
| spark-iceberg | tabulario/spark-iceberg | 정제·MERGE 적재 | `8888` |
| trino | trinodb/trino | SQL 조회 엔진 | `8080` |

폴더 구조:

```
week4/
├── docker-compose.yml           # MinIO · mc · REST 카탈로그 · Spark · Trino
├── catalog/
│   └── iceberg.properties       # Trino가 REST 카탈로그에 붙는 설정
├── scripts/
│   ├── etl_orders.py            # 랜딩 존(raw) → 정제 → MERGE 적재
│   ├── etl_bad.py               # 중복을 안 줄이면 MERGE가 실패하는 것을 보는 실험용
│   └── lakehouse_queries.sql    # Trino 쿼리 스크립트
├── data/                        # 연습용 주문 CSV
├── s3_demo.py                   # S3 API 연습
├── lakehouse_architecture.md    # 아키텍처 다이어그램과 설명
└── README.md
```

## 처리 흐름

1. 주문 CSV를 `raw` 버킷(랜딩 존)에 올립니다.
2. `etl_orders.py`가 s3a로 읽어 정제합니다. (형 변환 → `order_id IS NOT NULL AND amount >= 0` 불량 제거 → `order_id`별 최신 1행만 남기기)
3. `MERGE INTO demo.lakehouse.orders`로 적재합니다. 키가 있으면 갱신, 없으면 삽입합니다.
4. Trino에서 `iceberg.lakehouse.orders`로 같은 테이블을 조회합니다. (Spark의 카탈로그 이름은 `demo`, Trino는 `iceberg`이지만 실체는 같습니다)

## 실행 방법

사전 준비: Docker가 켜져 있어야 하고, 9000·9001·8181·8888·8080 포트가 비어 있어야 합니다.

```bash
cd ~/lakehouse
docker compose up -d
until docker compose exec trino trino --execute "SELECT 1" > /dev/null 2>&1; do sleep 2; done; echo "Trino 준비 완료"
```

Spark ETL (랜딩 존 CSV → Iceberg 테이블):

```bash
docker compose exec -T spark-iceberg spark-submit \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
  --conf spark.hadoop.fs.s3a.access.key=minioadmin \
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  /home/iceberg/scripts/etl_orders.py
```

Trino 쿼리 스크립트:

```bash
docker compose exec -T trino trino < scripts/lakehouse_queries.sql
```

접속 정보(`minioadmin`)는 MinIO 기본값을 그대로 쓴 수업용 로컬 값이며 실제 서비스 계정이 아닙니다. 실무에서는 환경변수(`.env`)로 분리하고 Git에 올리지 않습니다.

## 결과

`lakehouse_queries.sql` 실행 결과 일부입니다.

채널별 매출 비중:

| channel | revenue | pct |
|---|---|---|
| app | 118000.0 | 61.5 |
| web | 74000.0 | 38.5 |

고객별 합계:

| customer | orders | total |
|---|---|---|
| choi | 1 | 61000.0 |
| jung | 2 | 51000.0 |
| lee | 1 | 35000.0 |
| ok | 1 | 18000.0 |
| kim | 1 | 15000.0 |
| park | 1 | 12000.0 |

집계 테이블 `daily_sales`:

| order_date | order_cnt | revenue |
|---|---|---|
| 2026-08-01 | 1 | 15000.0 |
| 2026-08-02 | 2 | 47000.0 |
| 2026-08-03 | 3 | 103000.0 |

## 확인한 것

| 확인 항목 | 결과 |
|---|---|
| 두 엔진이 같은 테이블을 보는가 | Trino · Spark 모두 `orders` 7행 |
| Trino가 쓰고 Spark가 읽기 | Trino로 `order_id` 8을 INSERT → Spark 조회에서 보임 |
| Spark가 바꾸고 Trino가 읽기 | Spark로 `memo` 컬럼 추가·UPDATE → Trino `DESCRIBE`와 조회에 반영 |
| 커밋 이력이 하나로 쌓이는가 | `orders$snapshots` 11개 (append 4 · overwrite 6 · delete 1). Spark · Trino 모두 11 |
| 데이터 파일 | `orders$files` 4개 (Spark가 쓴 파일 1개 + Trino가 쓴 파일 3개) |

## 겪은 문제와 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| `docker compose up -d`가 `Bind for 0.0.0.0:9000 failed: port is already allocated` | 5주차 컨테이너가 같은 포트(9000)를 쓰며 떠 있었음 | 다른 스택은 `docker compose stop`으로 멈추고 올림 (`down -v`는 볼륨이 지워지므로 쓰지 않음) |
| Trino `count(*)`가 멈추고 `mc ls`가 `lookup minio ... no such host` | 포트 오류로 실패한 뒤 `down` 없이 `up -d`만 다시 실행해 네트워크가 꼬임 | `docker compose down`(볼륨 유지) 후 `up -d` |
| `etl_orders.py` 재실행이 `UNRESOLVED_COLUMN ... memo` 오류로 실패 | 4-5에서 테이블에 `memo` 컬럼을 추가했는데, 원천 CSV에는 `memo`가 없어서 `UPDATE SET *`가 컬럼을 맞추지 못함 | 아직 수정하지 않음. 실패한 MERGE는 커밋되지 않아 테이블은 7행 그대로. 아래 개선점 참고 |

## 남은 개선점

- 테이블에 컬럼이 늘어나면 `etl_orders.py`가 깨집니다. → 원천에 없는 컬럼은 `NULL`로 채워 맞추거나, 컬럼을 명시한 `MERGE`로 바꿀 예정입니다.
- `daily_sales`는 Trino `CTAS`로 한 번 만든 뒤 갱신되지 않습니다. `orders`에는 8/4 주문(`order_id` 8)이 있지만 `daily_sales`에는 8/4 행이 없습니다. → 적재 후 `daily_sales`를 다시 만들거나 `MERGE`로 갱신하는 단계를 추가할 예정입니다.
- 랜딩 존 전체를 매번 다시 읽습니다. → 날짜별 경로(`dt=...`)로 새 파일만 읽도록 바꿀 예정입니다.
- 접속 정보(`minioadmin`)가 `docker-compose.yml`과 `catalog/iceberg.properties`에 직접 적혀 있습니다. → `.env`로 분리할 예정입니다.
