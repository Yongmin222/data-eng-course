# 3주차 산출물 — 주문 데이터 정제 파이프라인 + 품질 리포트

주문 CSV(1,015행)를 DuckDB로 읽고 Pandas로 정제해 Parquet로 저장하는 파이프라인입니다. 정제 전후의 품질 지표를 리포트로 남겼고, CSV와 Parquet의 크기·속도 차이를 직접 재서 `실측기록_3-3.md`에 정리했습니다.

## 구성

| 파일 | 역할 |
|---|---|
| `clean_orders.py` | 추출(DuckDB) → 정제(Pandas) → 검증 → Parquet 저장. 검증에 실패하면 종료 코드 1로 끝납니다 |
| `orders_clean.parquet` | 정제 결과 (1,000행) |
| `quality_report.py` | 정제 전후 품질 지표를 계산해 CSV로 저장 |
| `quality_report.csv` | 품질 지표 전후 비교 (표 형태 원본) |
| `quality_report.md` | 품질 리포트 (처리 내용과 근거, 고치지 않은 것, 검증) |
| `실측기록_3-3.md` | CSV vs Parquet 크기·속도 측정과 해석 |

## 처리 흐름 (clean_orders.py)

1. DuckDB로 `orders.csv`를 읽습니다.
2. 정제합니다.

| 문제 | 처리 |
|---|---|
| `category` 앞뒤 공백 | `str.strip()` |
| `order_date` 타입 | `to_datetime()` |
| `order_id` 중복 15건 | `drop_duplicates(keep='first')` |
| `price` 결측 30건 | 중복 제거 뒤 중앙값으로 보정 |

3. `amount`(가격 × 수량)를 계산합니다.
4. `validate()`로 검증합니다. (가격·수량 0 이하, 알 수 없는 카테고리, 중복, 결측). 하나라도 있으면 `검증 실패`를 출력하고 종료 코드 1로 끝나며, 저장하지 않습니다.
5. 통과하면 `orders_clean.parquet`로 저장합니다.

## 실행 방법

같은 폴더에 `orders.csv`(3-1 실습에서 생성)가 있어야 합니다.

```bash
cd week3
pip install duckdb pandas pyarrow
python clean_orders.py
python quality_report.py
```

## 결과

품질 지표 전후 비교 (`quality_report.csv`):

| 지표 | before | after |
|---|---|---|
| 행 수 | 1,015 | 1,000 |
| order_id 중복 | 15 | 0 |
| price 결측 | 30 (2.96%) | 0 |
| category 고유값 | 5 | 4 |

CSV와 Parquet 비교 (`실측기록_3-3.md`, 본인 환경 1회 측정):

| 항목 | CSV | Parquet(zstd) | 배율 |
|---|---|---|---|
| 파일 크기 | 40.6 MB | 9.8 MB | 4.1배 |
| 집계 질의 | 0.088초 | 0.003초 | 26.9배 |

압축 방식 비교: zstd 9.8 MB / snappy 15.9 MB / gzip 10.6 MB

## 확인한 것

| 확인 항목 | 결과 |
|---|---|
| 재실행 | 같은 원본으로 두 번 돌려 결과가 동일 (`equals()` True) |
| 교차 검증 | DuckDB로 다시 측정한 값이 Pandas 결과와 일치 |
| 유효성 검사 | 음수 가격·수량, 알 수 없는 카테고리 0건 |
| 검사기 자체 검증 | 일부러 나쁜 값을 넣어 검사기가 잡는 것을 확인 |

## 겪은 문제와 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| "전부 읽기"가 "한 열만 읽기"보다 빠르게 측정됨 | `count(*)`는 열 값이 필요 없어서 DuckDB가 파일에 적힌 행 수만 읽음 | 측정이 기대와 반대로 나오면 측정 방법부터 의심해야 한다는 것을 배움. 비교가 성립하지 않아 열 단위 읽기 비교로 대체 |

## 남은 개선점

- `validate()`에 가격·수량 상한 검사가 없습니다. → 추가할 예정입니다.
- 결측 가격을 전체 중앙값 하나로 채웠습니다. → 카테고리별 중앙값으로 채우는 방법과 비교해 볼 예정입니다.
- 미래 날짜 검사가 최종 파이프라인에 없고, 중복된 두 행의 내용이 다른 경우를 비교하지 않았습니다. → 따로 집계해 남길 행의 기준을 정할 예정입니다.
