# 쇼핑몰 ERD 설계서

> 2주차 · 2-4 ERD 설계 및 정규화/반정규화 전략 산출물
> 도구: MySQL Workbench (EER Diagram) · 원본 모델 `ERD.mwb` · 이미지 `ERD.png`

![ERD](ERD.png)

## 1. 설계 목표

온라인 쇼핑몰에서 **누가(고객) · 언제(주문) · 무엇을(상품) · 몇 개 · 얼마에** 샀는지를 중복 없이 저장하는 것이 목표입니다.
처음에는 주문 정보를 한 표에 모두 넣은 형태를 가정했고, 정규화로 표를 나눈 뒤 꼭 필요한 부분만 반정규화했습니다.

## 2. 엔터티 정의

표 4개로 구성했습니다.

### customers (고객)

| 컬럼 | 타입 | 키 | 설명 |
|---|---|---|---|
| id | INT | PK | 고객 번호 |
| name | VARCHAR(50) | | 고객 이름 |
| tel | VARCHAR(20) | | 연락처 |

### products (상품)

| 컬럼 | 타입 | 키 | 설명 |
|---|---|---|---|
| id | INT | PK | 상품 번호 |
| name | VARCHAR(100) | | 상품명 |
| category | VARCHAR(50) | | 분류 |
| price | INT | | 현재 판매가 |
| stock | INT | | 재고 수량 |

### orders (주문)

| 컬럼 | 타입 | 키 | 설명 |
|---|---|---|---|
| id | INT | PK | 주문 번호 |
| customer_id | INT | FK → customers.id | 주문한 고객 |
| ordered_at | DATETIME | | 주문 일시 |

### order_items (주문 상세)

| 컬럼 | 타입 | 키 | 설명 |
|---|---|---|---|
| order_id | INT | PK, FK → orders.id | 어떤 주문의 상세인지 |
| product_id | INT | PK, FK → products.id | 어떤 상품인지 |
| quantity | INT | | 주문 수량 |
| unit_price | INT | | **주문 당시** 단가 (반정규화, 5번 참고) |

복합 PK `(order_id, product_id)`는 "한 주문 안에서 같은 상품은 한 줄만 존재한다"는 규칙을 DB가 보장하게 합니다.

## 3. 관계

| 관계 | 카디널리티 | 선 종류 | 설명 |
|---|---|---|---|
| customers → orders | 1 : N | 비식별 (점선) | 고객 한 명이 주문을 여러 번 할 수 있습니다. FK `customer_id`는 orders의 일반 컬럼입니다. |
| orders → order_items | 1 : N | 식별 (실선) | 주문 하나에 상품 줄이 여러 개 들어갑니다. FK `order_id`가 order_items의 PK에 포함됩니다. |
| products → order_items | 1 : N | 식별 (실선) | 상품 하나가 여러 주문에 들어갈 수 있습니다. FK `product_id`가 PK에 포함됩니다. |

**N : M 해소.** 주문과 상품은 원래 다대다 관계입니다. (주문 하나에 상품이 여러 개, 상품 하나가 여러 주문에 포함)
다대다는 표 하나로 표현할 수 없으므로 **교차 표 `order_items`** 를 두어 두 개의 1 : N 관계로 풀었습니다.
FK는 항상 N쪽 표에 둡니다.

식별/비식별은 "FK가 자식 표의 PK 안에 들어가는가"로 구분합니다.
order_items는 부모(주문, 상품) 없이는 존재할 수 없으므로 식별 관계(실선)로 그렸고, orders는 자체 PK(`id`)를 따로 가지므로 customers와는 비식별 관계(점선)로 그렸습니다.

## 4. 정규화 근거

| 단계 | 규칙 | 이 설계에서 적용한 방식 |
|---|---|---|
| 1NF | 한 칸에는 값 하나 (원자값) | 한 주문에 여러 상품이 있어도 한 칸에 `마우스, 키보드`처럼 묶지 않고 order_items에 **행으로 분리**했습니다. |
| 2NF | 복합 PK의 일부에만 종속된 컬럼 제거 | 상품명·분류는 `product_id`만 알면 정해지므로 order_items에 두지 않고 products로 분리했습니다. order_items에는 `(주문, 상품)` 둘이 모두 있어야 정해지는 `quantity`만 남겼습니다. |
| 3NF | PK가 아닌 컬럼 사이의 종속 제거 | 고객 이름·연락처는 `customer_id`로 정해지는 값이므로 orders에 두지 않고 customers로 분리했습니다. |

정규화로 막으려는 이상 현상은 다음과 같습니다.

| 이상 | 한 표에 모두 넣었을 때 | 분리한 뒤 |
|---|---|---|
| 수정 이상 | 고객 전화번호가 바뀌면 그 고객의 모든 주문 행을 고쳐야 합니다. | customers의 한 행만 수정하면 됩니다. |
| 삽입 이상 | 주문이 없는 신규 고객·상품은 넣을 곳이 없습니다. | customers, products에 따로 등록할 수 있습니다. |
| 삭제 이상 | 마지막 주문을 지우면 고객·상품 정보도 함께 사라집니다. | 주문을 지워도 고객·상품은 남습니다. |

## 5. 반정규화 결정

| 항목 | 내용 |
|---|---|
| 대상 | `order_items.unit_price` |
| 정규화 관점 | 가격은 products에 있는데 order_items에도 저장하므로 중복처럼 보입니다. |
| 그래도 두는 이유 | `products.price`는 **현재** 판매가라서 바뀔 수 있습니다. 주문 당시 가격을 따로 저장하지 않으면, 가격이 오른 뒤 과거 주문 금액까지 바뀌어 매출 집계가 틀어집니다. |
| 성격 | 중복이 아니라 **주문 시점 가격의 스냅샷(기록)** 입니다. |
| 비용 | 컬럼이 1개 늘어납니다. 대신 과거 주문 금액을 JOIN 없이 `quantity * unit_price`로 계산할 수 있습니다. |

반정규화하지 않은 항목은 주문 총액(`orders.total_price`)입니다. 상세 줄의 합으로 언제든 계산할 수 있고, 따로 저장하면 상세 내역과 값이 어긋날 위험이 생기기 때문입니다.

## 6. DDL

설계를 실제 표로 옮긴 SQL입니다. 기존 `shop` DB의 `products`와 충돌하지 않도록 별도 DB에서 실행합니다.
생성 순서는 **부모 표 → 자식 표**여야 합니다. (FK가 참조할 표가 먼저 존재해야 하기 때문입니다.)

**Workbench 모델(`ERD.mwb`)과 다른 점.** 모델의 스키마 이름은 `mydb`이고, FK 이름은 Workbench가 자동으로 붙인 `fk_orders_customers1` 같은 이름이며, `id`에는 AUTO_INCREMENT가 없습니다.
아래 DDL은 이 모델을 바탕으로 다음 세 가지를 다듬은 것입니다.

| 다듬은 점 | 이유 |
|---|---|
| 스키마 이름을 `shop_erd`로 지정 | 기존 `shop` DB의 표와 충돌하는 것을 방지 |
| FK 이름을 의미 있게 지정 (`fk_orders_customer` 등) | 오류 메시지와 `information_schema`에서 알아보기 쉬움 |
| `id`에 AUTO_INCREMENT, 필수 컬럼에 NOT NULL 추가 | 번호를 DB가 자동으로 부여하고, 빈 값이 들어오는 것을 방지 |

```sql
CREATE DATABASE IF NOT EXISTS shop_erd DEFAULT CHARACTER SET utf8mb4;
USE shop_erd;

-- 1) 부모 표
CREATE TABLE customers (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  tel  VARCHAR(20)
);

CREATE TABLE products (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(100) NOT NULL,
  category VARCHAR(50),
  price    INT NOT NULL,
  stock    INT NOT NULL DEFAULT 0
);

-- 2) customers를 참조하는 표
CREATE TABLE orders (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  ordered_at  DATETIME NOT NULL,
  CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- 3) orders, products를 참조하는 교차 표 (복합 PK)
CREATE TABLE order_items (
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL,
  unit_price INT NOT NULL,
  PRIMARY KEY (order_id, product_id),
  CONSTRAINT fk_items_order
    FOREIGN KEY (order_id) REFERENCES orders (id),
  CONSTRAINT fk_items_product
    FOREIGN KEY (product_id) REFERENCES products (id)
);
```

### 제약 이름을 붙인 이유

`CONSTRAINT 이름 FOREIGN KEY ...`처럼 이름을 직접 붙이면 오류 메시지와 `information_schema` 조회에서 어떤 제약인지 바로 알 수 있습니다.

### 검증 쿼리

```sql
-- FK 3개가 의도대로 걸렸는지
SELECT table_name, constraint_name, referenced_table_name
FROM information_schema.key_column_usage
WHERE table_schema = 'shop_erd' AND referenced_table_name IS NOT NULL;

-- order_items의 복합 PK 순서 (order_id → product_id)
SELECT index_name, seq_in_index, column_name
FROM information_schema.statistics
WHERE table_schema = 'shop_erd' AND table_name = 'order_items'
  AND index_name = 'PRIMARY'
ORDER BY seq_in_index;
```

기대 결과: FK는 3개(`orders.customer_id`, `order_items.order_id`, `order_items.product_id`)이고, PK 순서는 `order_id(1) → product_id(2)`입니다.

## 7. 설계하면서 배운 점

- 관계선을 그으면 Workbench가 FK 컬럼을 `테이블명_컬럼명` 형태로 자동 생성합니다. 미리 만들어 둔 컬럼과 겹치면 중복되므로, FK 컬럼은 관계선에 맡기고 이름만 다듬는 것이 안전합니다.
- 기존 표가 있는 `shop` 스키마에 그대로 반영하면 충돌할 수 있으므로 별도 스키마를 사용합니다.
