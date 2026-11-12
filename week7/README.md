# 7주차 — RAG (청킹 · 임베딩 · Qdrant · 하이브리드 검색)

MinIO에 둔 문서를 잘라 임베딩해 Qdrant에 색인하고, 키워드(BM25)와 의미(벡터) 검색을 RRF로 합쳐 LLM이 근거를 바탕으로 답하게 만든다.

## 1. 구성

| 구성 요소 | 이미지 / 모델 | 역할 |
|---|---|---|
| rag-minio | pgsty/minio | 원본 문서 보관 (`raw-docs` 버킷) |
| qdrant | qdrant/qdrant:v1.20.0 | 벡터 DB |
| ollama | ollama/ollama | 임베딩 `embeddinggemma`(768차원), 답변 `llama3.2` |

## 2. 데이터 흐름

## 3. 벡터 스키마 (`vector-schema.yaml`)

| 항목 | 값 |
|---|---|
| 컬렉션 | `lecture_kb` |
| 벡터 | 768차원, Cosine |
| payload | `text`(조각 본문), `source`(원본 주소), `chunk_index`(문서 안 순번) |
| 청킹 | RecursiveCharacterTextSplitter, chunk_size 300, overlap 30 |
| id 규칙 | `uuid5(source + "#" + chunk_index)` — 같은 입력이면 같은 id (재실행 안전) |

`check_schema.py`로 정의서와 실제 컬렉션이 일치하는지 대조한다.

## 4. 제출 파일

| 파일 | 설명 |
|---|---|
| `vector-schema.yaml` | 벡터 스키마 정의서 |
| `check_schema.py` | 정의서와 실제 컬렉션·모델 차원 대조 |
| `build_kb.py` | MinIO 문서를 읽어 Qdrant에 색인 (몇 번 실행해도 결과 동일) |
| `rag_env.py`, `minio_env.py` | 모델 선택, MinIO 접속 설정 |

## 5. 실습 코드

| 파일 | 하는 일 |
|---|---|
| `kb.py` | 적재·재적재 함수 모음 |
| `kb_corpus.py` | Qdrant 조각을 내려받아 BM25 색인 생성 |
| `retrievers.py` | BM25 순위와 벡터 순위를 같은 모양으로 반환 |
| `hybrid.py` | 두 순위를 RRF로 합산 |
| `rag.py`, `rag_source.py` | 검색 결과를 근거로 LLM이 답변, 출처 표시 |
| `params.py`, `broken.py` | chunk_size·overlap 조합별 조각 수, 문장 끊김 측정 |
| `kb_idem.py`, `kb_bad.py` | 재적재 멱등성 확인, 랜덤 id 대조 실험 |
| `emb_limits.py` | 임베딩이 구분 못 하는 경우 (반대말, 비슷한 식별자) |
| `bm25_josa.py`, `bm25_code.py` | BM25의 조사 문제, 없는 코드에 대한 반응 |
| `compare3.py`, `rrf_k.py` | BM25·벡터·하이브리드 비교, RRF의 k 값 영향 |

## 실행

```bash
python build_kb.py          # 색인 (환경 변수: MINIO_ENDPOINT, QDRANT_URL, CHUNK_SIZE, COLLECTION)
python check_schema.py      # 정의서 대조
python rag.py               # RAG 질의
```

## 6. 확인한 것

`long_notes.txt`(1,247자, 8문단)로 측정했다.

| 실험 | 결과 |
|---|---|
| chunk_size / overlap별 조각 수 | 100/0 → 16, 100/20 → 17, 300/30 → 6, 500/50 → 3, 1000/100 → 2 |
| 문장 중간에서 끝난 조각 | size 100: 7/16 (overlap 20: 8/17), size 300·500: 0 |
| 재적재 | uuid5 id: 10 → 10 (유지) / 랜덤 uuid4 id: 3 → 6 (중복 쌓임) |
| 차원 불일치 | size=10 컬렉션에 768차원 삽입 시 400 (expected 10, got 768) |
| 임베딩의 한계 | 성공/실패 문장 0.741, `A-1001`/`A-1002` 0.862 |
| BM25와 조사 | `Airflow` 2.11, `Airflow는` 1.66, `도구는` 0.00 |
| 없는 코드 `ERR-4012` | BM25 0.00, 벡터는 `ERR-4021` 조각을 0.355로 1등 (있는 코드는 0.411) |
| RRF | 한쪽 1등·다른 쪽 2등이면 동점(0.0325), k=1/60/200에서 1등÷3등 3.33/2.05/2.01배 |
| 하이브리드 효과 | 10조각 데이터에서는 벡터 결과와 동일 (규모가 커져야 차이 예상) |
| 지식베이스 밖 질문 | "모르면 모른다고 답해" 지시에도 소형 모델이 지어냄 |

## 7. 남은 개선점

- `build_kb.py`는 옛 조각을 먼저 지우고 임베딩해서, 임베딩이 실패하면 문서가 색인에서 빠진다. 임베딩 → 삭제 → 저장 순서로 바꿔야 한다.
- 문서가 짧아졌을 때 옛 조각이 정리되는지는 직접 실험하지 못했다.
- BM25가 공백 기준 토큰이라 조사가 붙은 낱말을 놓친다. 형태소 분석기로 교체한다.
- 무관한 질문을 막으려면 검색 점수 기준선으로 LLM 호출 전에 차단해야 한다.
- 근거 표시가 LLM에 넘긴 후보 전체라서, 점수 기준을 넘은 상위 조각만 표시한다.
- 데이터가 10조각뿐이라 하이브리드 효과를 못 봤다. 채용공고 수백 건으로 다시 측정한다.

## 주의

`minio_env.py`의 `minioadmin`은 로컬 실습용 기본 계정이다. 실제 환경에서는 환경 변수로 분리한다.
