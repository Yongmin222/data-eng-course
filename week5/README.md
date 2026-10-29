# 5주차 산출물 — Spark 배치 데이터 마트 (일별 매출)

Spark Standalone 클러스터에서 주문·상품 데이터를 조인·집계해 `daily_sales_mart`를 만들고, MinIO 위의 Iceberg 테이블로 저장하는 배치입니다. 파티션·셔플 동작을 직접 재서, 그 값을 `실측기록_5-5.md`에 정리했습니다.

## 구성

| 구성 요소 | 이미지 / 도구 | 역할 |
|---|---|---|
| spark-master, spark-worker | Docker Compose (Spark 3.5.3) | 일을 나눠 주는 마스터와 실제로 계산하는 워커 (코어 합계 4) |
| minio | MinIO | S3 호환 저장소 (`s3a://warehouse`) |
| Iceberg | `hadoop` 카탈로그 (`lake`) | 저장소의 파일을 표(테이블)처럼 관리 |
| mart.py | `spark-submit` | 조인 → 집계 → 저장하는 배치 스크립트 |

폴더 구조:

```
week5/
├── docker-compose.yml           # Spark 마스터-워커 + MinIO
├── docker-compose.override.yml  # Spark UI(4040)를 컨테이너 밖으로 여는 덧붙임 설정
├── lake-pyspark.sh              # MinIO·Iceberg 설정을 담아 PySpark 셸을 여는 스크립트
├── first_job.py                 # 클러스터 동작 확인용 첫 잡 (5-2, spark-submit 연습)
├── mart.py                      # 일별 매출 마트 배치 (인자·로그·검증·종료 코드)
├── mart.log                     # 실행 로그 (마트 결과 표 포함)
├── 실측기록_5-5.md               # 파티션·셔플·스큐를 직접 잰 값과 해석
└── README.md
```

## 처리 흐름 (mart.py)

1. 원천 주문·상품 데이터를 읽습니다.
2. `product_id`로 조인하고 `amount`(수량 × 단가)를 만듭니다.
3. 날짜별로 집계합니다. (`daily_amount`, `order_cnt`)
4. `coalesce(1)`로 파티션을 1개로 합친 뒤 Iceberg 테이블 `lake.db.daily_sales_mart`로 교체 저장합니다.

| 단계 | 변환 종류 | 셔플 |
|---|---|---|
| `join` | 넓은 변환 | 있음 |
| `withColumn` | 좁은 변환 | 없음 |
| `groupBy` + `agg` | 넓은 변환 | 있음 |
| `coalesce(1)` | 파티션 합치기 | 없음 |

## 실행 방법

사전 준비: Docker가 켜져 있어야 하고, 클러스터가 떠 있어야 합니다. (`docker compose up -d`)

**PySpark 셸을 열어 둔 상태에서는 spark-submit이 일을 받지 못합니다.** 셸이 코어 4개를 모두 잡고 있기 때문입니다. 셸에서 `exit()`로 나온 뒤 실행합니다.

```bash
cd ~/data-eng/week5
docker compose cp mart.py spark-master:/tmp/mart.py
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2 \
  /tmp/mart.py [날짜] > mart.log 2>&1
echo "종료 코드: $?"
grep "\[mart\]" mart.log
```

- `[날짜]`를 생략하면 전체를, `2026-08-25`처럼 주면 그 날짜만 처리합니다.
- 접속 정보(`admin` / `password123`)는 수업용 로컬 MinIO 값이며 실제 서비스 계정이 아닙니다. 실무에서는 환경변수로 분리하고 Git에 올리지 않습니다.

## 결과

마트 조회 결과 (전체 실행):

| order_date | daily_amount | order_cnt |
|---|---|---|
| 2026-08-24 | 113000 | 2 |
| 2026-08-25 | 1155000 | 2 |
| 2026-08-26 | 46000 | 1 |

로그 (`grep "\[mart\]" mart.log`):

```
[mart] 대상 날짜: 전체
[mart] 원천 5행
[mart] 마트 3행
[mart] 완료
```

## 실측 (본인 환경)

| 항목 | 값 |
|---|---|
| 기본 파티션 수 | 4 (`splits=4`, 코어 수와 같음) |
| AQE 끔 · shuffle.partitions 200 → 8 실행 시간 | 0.89초 → 0.14초 |
| coalesce(1) 전/후 저장 파일 수 | 4 → 1 |
| 스큐 Task 시간 Max / Median | 0.6초 / 75ms (약 8배) |

환경이 작은 로컬 클러스터이고 1회 측정이라 절대값은 참고용이며, 방향이 중요합니다. 측정 방법과 해석은 [실측기록_5-5.md](실측기록_5-5.md)에 있습니다.

## 확인한 것

| 확인 항목 | 결과 |
|---|---|
| 두 번 실행해도 결과 동일 (멱등) | `createOrReplace`가 테이블을 통째로 교체해서 3행 그대로 |
| 없는 날짜(`2099-01-01`)를 주면 | `원천이 비어 있습니다 — 중단`, 종료 코드 **1**, 저장 단계까지 가지 않아 기존 마트는 그대로 |
| 정상 실행 | 종료 코드 **0** |
| 한 번 저장에 파일 1개 | `coalesce(1)` 효과. 다시 돌리면 옛 판 파일이 스냅샷으로 남음 |
| 인자로 일부만 처리 | `2026-08-25`만 돌리면 마트가 1행으로 교체됨 (전체 재실행으로 복구) |

## 겪은 문제와 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| `spark-submit`이 `Initial job has not accepted any resources`만 찍고 멈춤 | 열어 둔 PySpark 셸이 워커 코어를 전부 잡고 있음 | 셸에서 `exit()`로 나온 뒤 다시 실행 |
| `localhost:4040`이 열리지 않음 | 4040은 셸이나 spark-submit이 떠 있는 동안만 열림 | 셸을 띄운 상태에서 접속 |
| `>>>` 창에 여러 줄을 붙여 넣으면 `SyntaxError` | `def`, `for` 블록 뒤에 빈 줄이 없으면 파이썬이 블록이 안 끝난 것으로 읽음 | 한 줄씩 넣거나 `.py` 파일로 만들어 실행 |
| `docker run ...`을 `>>>`에 넣었더니 에러 | `>>>`는 파이썬 전용이고 리눅스 명령은 `$` 프롬프트에서 실행해야 함 | `exit()`로 나와서 bash에서 실행 |

## 남은 개선점

- 접속 정보(비밀번호 포함)가 코드에 직접 적혀 있습니다. → 환경변수로 분리할 예정입니다.
- 원천 데이터가 코드 안의 5행입니다. → Iceberg 원천 테이블(`lake.db.orders`)을 읽도록 바꿀 예정입니다.
- 날짜 인자로 돌리면 마트가 그 날짜 1행으로 교체됩니다. → 날짜별 `MERGE`로 증분 반영할 예정입니다.
- 옛 판 파일이 스냅샷으로 쌓입니다. → `expire_snapshots`로 정리할 예정입니다.
