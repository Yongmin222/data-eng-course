# crawler_pipeline.py — 수집(fetch) → 정제(parse) → 적재(load)
from __future__ import annotations

import time
from datetime import datetime

import pymysql
import requests
from bs4 import BeautifulSoup

BASE = 'https://quotes.toscrape.com'
HEADERS = {'User-Agent': 'data-eng-class-crawler/1.0 (learning purpose)'}
DELAY_SEC = 1.0  # 크롤링 예절: 요청 간격 1초
FAILED_LOG = 'failed.log'

# 과제 2-1: 접속 정보를 함수 밖 상수로
DB_CONFIG = dict(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='dataeng123',
    database='shop',
    charset='utf8mb4',
)


def fetch(url: str, retries: int = 3) -> str:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 429:
                print(f'  429 too many requests — {attempt}회차, 5초 대기')
                time.sleep(5)
                continue
            res.raise_for_status()
            return res.text
        except requests.RequestException as e:
            last_error = e
            print(f'  요청 실패({attempt}/{retries}): {e}')
            time.sleep(2 * attempt)  # 갈수록 더 오래 쉰다
    raise RuntimeError(f'{url} 수집 실패') from last_error


def parse(html: str) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for q in soup.select('div.quote'):
        rows.append({
            'author': q.select_one('small.author').get_text(strip=True),
            'quote_text': q.select_one('span.text').get_text(strip=True),
            'tags': ','.join(t.get_text(strip=True) for t in q.select('a.tag')),
        })
    next_link = soup.select_one('li.next a')
    next_url = BASE + next_link['href'] if next_link else None
    return rows, next_url


# 과제 2-2: 접속(conn)을 밖에서 받아서 쓴다 (여기서 열고 닫지 않음)
def load(conn, rows: list[dict]) -> int:
    saved = 0
    with conn.cursor() as cur:
        for r in rows:
            # INSERT IGNORE: UNIQUE 충돌(이미 수집한 명언)은 건너뜀
            saved += cur.execute(
                'INSERT IGNORE INTO quotes (author, quote_text, tags, crawled_at) '
                'VALUES (%s, %s, %s, %s)',
                (r['author'], r['quote_text'], r['tags'], datetime.now()),
            )
    conn.commit()
    return saved


# 과제 3: 실패한 URL을 파일에 남긴다
def log_failed(url: str, error) -> None:
    with open(FAILED_LOG, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}\t{url}\t{error}\n')


# 과제 1: max_pages 기본값을 10으로
def run(max_pages: int = 10) -> None:
    conn = pymysql.connect(**DB_CONFIG)  # 접속은 한 번만
    try:
        url = BASE + '/'
        for page in range(1, max_pages + 1):
            try:
                html = fetch(url)
            except RuntimeError as e:
                log_failed(url, e.__cause__)
                print(f'page {page}: 수집 실패 → {FAILED_LOG} 에 기록')
                break
            rows, next_url = parse(html)
            saved = load(conn, rows)
            print(f'page {page}: parsed {len(rows)}, saved {saved}')
            if not next_url:
                break
            url = next_url
            time.sleep(DELAY_SEC)
    finally:
        conn.close()  # 오류가 나도 반드시 닫는다


if __name__ == '__main__':
    run()
