# 1주차 산출물 — Docker Compose 기반 통합 엔지니어링 환경

Postgres, pgAdmin, 파이썬 앱을 `docker-compose.yml` 한 파일로 묶어서, 명령 한 줄로 같은 환경을 다시 만들 수 있게 정리했습니다.

## 구성

| 서비스 | 이미지 / 빌드 | 역할 | 접속 |
|---|---|---|---|
| db | `postgres:16` | 데이터 저장 (볼륨 `pgdata`로 데이터 보존) | `localhost:5432` |
| admin | `dpage/pgadmin4:9.18` | DB 관리용 웹 화면 | http://localhost:8081 |
| app | `./app`의 Dockerfile로 직접 빌드 | DB에 접속해 일하는 파이썬 앱 (일회성 실행) | - |

폴더 구조:

```
week1/
├── docker-compose.yml
├── README.md
└── app/
    ├── Dockerfile          # Compose가 빌드에 사용하는 최종 Dockerfile
    ├── Dockerfile.bad      # (실험) COPY . . 을 먼저 두어 캐시를 못 살리는 나쁜 순서
    ├── Dockerfile.fat      # (실험) python:3.12 전체 이미지를 쓴 큰 이미지
    ├── Dockerfile.multi    # (실험) 멀티스테이지 빌드
    ├── app.py
    └── requirements.txt
```

`Dockerfile.bad`, `Dockerfile.fat`, `Dockerfile.multi`는 이미지 최적화(레이어 캐시, 베이스 이미지 크기, 멀티스테이지)를 비교하려고 만든 실험용 파일이며, Compose 실행에는 쓰이지 않습니다.
비교는 예를 들어 이렇게 합니다.

```bash
docker build -t data-app:0.1 ./app                          # 최종 Dockerfile
docker build -t data-app:bad -f app/Dockerfile.bad ./app    # 나쁜 순서
docker images data-app --format "{{.Tag}}\t{{.Size}}"        # 태그별 이미지 크기 비교
```

## 실행 방법

사전 준비: Docker(Docker Desktop 또는 WSL2의 Docker Engine)가 켜져 있어야 합니다. 5432, 8081 포트를 다른 프로그램이 쓰고 있으면 안 됩니다.

1. 이 폴더로 이동합니다.
   ```bash
   cd ~/data-eng/week1
   ```
2. 문법을 미리 검사합니다. (선택)
   ```bash
   docker compose config
   ```
3. 빌드하고 전체를 시작합니다.
   ```bash
   docker compose up -d --build
   ```
4. 상태를 확인합니다.
   ```bash
   docker compose ps -a
   ```
   `db`, `admin`은 `Up`, `app`은 한 번 실행하고 끝나므로 `Exited (0)`이면 정상입니다.
5. 로그를 확인합니다.
   ```bash
   docker compose logs app
   ```
6. 종료합니다.
   ```bash
   docker compose down        # 컨테이너, 네트워크만 정리 (데이터 유지)
   docker compose down -v     # 볼륨까지 삭제 (데이터도 삭제되니 주의)
   ```

## 접속 정보

실습용 값입니다. 실제 서비스에서는 이런 값을 파일에 적지 않고 `.env`로 분리하고 Git에 올리지 않습니다.

- pgAdmin: http://localhost:8081 — `admin@example.com` / `admin123`
- DB
  - 컨테이너 내부(pgAdmin, app 등)에서: 호스트 `db`, 포트 `5432`
  - 내 컴퓨터에서: 호스트 `localhost`, 포트 `5432`
  - 사용자 `engineer` / 비밀번호 `engineer123` / DB명 `pipeline`

### pgAdmin에서 서버 등록하기

1. 로그인 후 **Add New Server**를 누릅니다.
2. **General** 탭 → Name: 원하는 이름 (예: `pipeline-db`). 비우면 저장이 안 됩니다.
3. **Connection** 탭 → Host `db`, Port `5432`, Maintenance database `pipeline`, Username `engineer`, Password `engineer123`
4. **Save**를 누릅니다.

## 데이터 보존 확인 방법 (볼륨 동작)

컨테이너를 내렸다 올려도 데이터가 남는지 확인하는 순서입니다. 명령은 한 줄씩 실행합니다.

```bash
cd ~/data-eng/week1

# 1) 테스트 표 만들고 데이터 넣기
docker compose exec db psql -U engineer -d pipeline -c "CREATE TABLE IF NOT EXISTS week1 (memo TEXT);"
docker compose exec db psql -U engineer -d pipeline -c "INSERT INTO week1 VALUES ('1주차 완료');"

# 2) 환경 전체를 종료했다가 다시 시작 (down에는 -v가 없으므로 볼륨은 유지됨)
docker compose down
docker compose up -d

# 3) 표와 데이터가 살아 있는지 확인 (DB 준비에 몇 초 걸리니 에러가 나면 잠시 후 재시도)
docker compose exec db psql -U engineer -d pipeline -c '\dt'
docker compose exec db psql -U engineer -d pipeline -c "SELECT * FROM week1;"
```

`week1` 표가 보이고 `1주차 완료`가 조회되면 성공입니다.
반대로 `docker compose down -v`로 볼륨까지 지운 뒤 다시 올리면 표가 사라집니다.

## 이미지 최적화 실험 결과 (직접 측정)

`app/`의 Dockerfile 4종으로 이미지 크기와 빌드 시간을 비교했습니다.

측정 환경: Windows 11 WSL2 (커널 5.15.167.4-microsoft-standard-WSL2), Docker Server 29.8.0. 베이스 이미지는 미리 받아 둔 상태에서 잰 값이라 다운로드 시간은 포함되지 않았고, 각 값은 1회 측정입니다.

| 이미지 | Dockerfile | 크기 (DISK USAGE) | 캐시 없이 빌드 | 코드만 수정 후 재빌드 |
|---|---|---|---|---|
| good | `Dockerfile` (slim, 변하지 않는 것 먼저) | 195MB | 4.25초 | **0.73초** |
| bad | `Dockerfile.bad` (`COPY . .`를 먼저) | 195MB | 2.98초 | 3.15초 |
| fat | `Dockerfile.fat` (`python:3.12` 전체) | **1.62GB** | 3.17초 | - |
| multi | `Dockerfile.multi` (멀티스테이지) | 182MB | 3.83초 | - |

배운 점:

- **레이어 순서**: 코드만 고쳤을 때 good은 `pip install` 단계가 캐시(`CACHED`)로 넘어가 0.73초, bad는 `COPY . .`이 먼저라 `pip install`부터 다시 돌아 3.15초로 약 4.3배 느렸습니다. 이 앱은 패키지가 `requests` 하나뿐이라 차이가 작은 편이고, 패키지가 많아지면 몇 분 차이가 됩니다.
- **베이스 이미지**: 같은 앱이 `python:3.12`에서는 1.62GB, `python:3.12-slim`에서는 195MB로 약 8배 차이가 났습니다. 배포할 때마다 이미지를 전송하므로 크기가 곧 비용입니다.
- **멀티스테이지**: 182MB로 slim 단일 스테이지(195MB)보다 13MB 작아졌습니다. 이 앱은 빌드 도구가 가벼워서 효과가 작고, Go, Java, C++처럼 빌드 도구가 무거운 언어에서 효과가 큽니다.
- **캐시 없이 빌드하는 시간**은 세 개가 3~4초로 비슷하고 순서도 일정하지 않습니다. 패키지가 하나뿐이라 시간 차이가 작고, 1회 측정이라 오차가 섞여 있습니다. 시간 비교는 캐시를 쓰는 재빌드 값이 의미가 큽니다.
- `DISK USAGE`는 디스크에 풀린 크기이고, `CONTENT SIZE`(good 47.7MB, fat 416MB)는 압축된 전송 크기입니다. 비교는 `DISK USAGE`로 했습니다.

재현 방법:

```bash
docker build --no-cache -t data-app:good -f app/Dockerfile ./app
docker build --no-cache -t data-app:bad  -f app/Dockerfile.bad ./app
docker build --no-cache -t data-app:fat  -f app/Dockerfile.fat ./app
docker build --no-cache -t data-app:multi -f app/Dockerfile.multi ./app
docker images data-app
# 캐시 효과: app.py를 한 줄 고친 뒤 캐시를 쓰고 다시 빌드해서 시간을 비교
```

## 확인한 것

- `docker compose config`로 문법을 검사했고, `depends_on`이 `service_started`로, 볼륨과 네트워크 이름이 `week1_pgdata`, `week1_default`로 풀리는 것을 확인했습니다.
- `docker compose exec db psql -U engineer -d pipeline -c "SELECT current_database();"` 결과가 `pipeline`으로 나와, 계정과 DB가 설정대로 만들어졌음을 확인했습니다.
- pgAdmin에서 호스트 이름을 `db`로 지정해 연결했습니다. (서비스 이름이 주소로 통한다는 의미)
- `docker compose down` 후 `up`을 해도 `week1` 표와 `1주차 완료` 데이터가 유지되는 것을 확인했습니다. (볼륨 동작 확인, 위 "데이터 보존 확인 방법" 참고)

## 겪은 문제와 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| 3차시에 만든 `pg` 컨테이너가 5432 포트를 쓸 수 있어 Compose의 `db`와 충돌할 위험이 있었음 | 이전 실습 컨테이너를 정리하지 않고 남겨 둠 (`docker ps -a`로 6일 전 `Exited` 상태로 남아 있는 것을 확인) | `docker stop pg`로 포트를 비우고 진행. 실행 전에 `docker ps -a`로 남은 컨테이너를 먼저 확인하기 |
| pgAdmin에서 서버 등록 시 `'Name' cannot be empty` | Connection 탭만 채우고 General 탭의 Name을 비워 둠 | General 탭에 Name을 적은 뒤 Save |
| pgAdmin Host에 무엇을 넣어야 할지 혼동 | 컨테이너 안에서 `localhost`는 자기 자신을 가리킴 | Host에는 서비스 이름 `db`를 사용. 내 컴퓨터에서 직접 접속할 때만 `localhost:5432` |
| `docker compose config` 출력이 내 파일과 달라 보였음 | `config`는 파일을 그대로 보여 주지 않고 기본값을 채워 풀어 쓴 결과를 보여 줌 | 값(이미지, 환경변수, 포트)은 같고 표기만 달라진 것임을 확인 |
| `app`이 `Exited (0)`인 것이 오류인지 헷갈림 | `app`은 한 번 실행하고 끝나는 일회성 컨테이너 | `Exited (0)`은 정상 종료. `docker compose logs app`으로 출력 확인 |
