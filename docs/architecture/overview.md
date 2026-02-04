# Architecture Overview

## Обзор системы BionicPRO

BionicPRO — платформа для управления бионическими протезами, включающая:

- Сбор телеметрии с протезов в реальном времени
- Формирование отчётов для пользователей
- Управление заказами через CRM
- Безопасную аутентификацию с MFA

## Архитектурные решения

Система построена по принципам:

1. **Разделение OLTP/OLAP нагрузок** — CRM работает с PostgreSQL, отчёты формируются из ClickHouse
2. **BFF Pattern** — токены хранятся на сервере, фронтенд работает только с session cookies
3. **CDC для real-time данных** — изменения в CRM автоматически реплицируются в OLAP
4. **Многоуровневое кэширование** — Redis + S3 + Nginx CDN

## Диаграмма компонентов

```mermaid
graph TB
    subgraph "Users"
        U1[Пользователь протеза]
        U2[Оператор CRM]
        U3[ML-инженер]
    end

    subgraph "Frontend Layer"
        FE[React Frontend<br/>:3000]
    end

    subgraph "Security Layer"
        KC[Keycloak<br/>:8080]
        LDAP[OpenLDAP<br/>:389]
        BFF[BFF Auth<br/>:8000]
        REDIS[(Redis<br/>:6379)]
    end

    subgraph "Application Layer"
        RS[Reports Service<br/>:8001]
        AF[Airflow<br/>:8081]
    end

    subgraph "Data Layer"
        CRM[(CRM DB<br/>PostgreSQL)]
        TEL[(Telemetry DB<br/>PostgreSQL)]
        CH[(ClickHouse<br/>OLAP)]
    end

    subgraph "CDC Pipeline"
        DBZ[Debezium<br/>:8083]
        KFK[Kafka<br/>:9092]
    end

    subgraph "Caching Layer"
        S3[(MinIO S3<br/>:9002)]
        CDN[Nginx CDN<br/>:8002]
    end

    U1 --> FE
    U2 --> CRM
    U3 --> CH

    FE --> BFF
    BFF --> KC
    KC --> LDAP
    BFF --> REDIS
    BFF --> RS

    RS --> CH
    RS --> S3
    CDN --> S3

    AF --> CRM
    AF --> TEL
    AF --> CH

    CRM --> DBZ
    DBZ --> KFK
    KFK --> CH
```

## Слои архитектуры

### 1. Presentation Layer (Frontend)

| Компонент | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Frontend | React 18 + TypeScript | 3000 | SPA для пользователей протезов |
| Nginx CDN | Nginx 1.25 | 8002 | Reverse proxy с кэшированием |

### 2. Security Layer

| Компонент | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Keycloak | Keycloak 26.5.2 | 8080 | Identity Provider, MFA, Identity Brokering |
| OpenLDAP | OpenLDAP 1.5.0 | 389 | Directory Service для User Federation |
| BFF Auth | Python/Flask | 8000 | Backend-for-Frontend, хранение токенов |
| Redis | Redis 7 | 6379 | Session Storage |

### 3. Application Layer

| Компонент | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Reports Service | Python/FastAPI | 8001 | REST API для отчётов |
| Apache Airflow | Airflow 2.8.1 | 8081 | ETL оркестратор |

### 4. Data Layer

| Компонент | Технология | Порт | Описание |
|-----------|------------|------|----------|
| CRM DB | PostgreSQL 14 | 5435 | OLTP база клиентов и заказов |
| Telemetry DB | PostgreSQL 14 | 5436 | OLTP база телеметрии |
| ClickHouse | ClickHouse 24.1 | 8123/9000 | OLAP витрина отчётов |
| MinIO | MinIO S3 | 9002 | Object Storage для отчётов |

### 5. CDC Pipeline

| Компонент | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Debezium | Debezium Connect | 8083 | CDC коннектор для PostgreSQL |
| Kafka | Apache Kafka 3.6 | 9092 | Message Broker |
| Zookeeper | Apache Zookeeper | 2181 | Координатор Kafka |

## Потоки данных

### Поток аутентификации

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BFF as BFF Auth
    participant KC as Keycloak
    participant LDAP as LDAP
    participant R as Redis

    U->>FE: 1. Login click
    FE->>BFF: 2. GET /auth/login
    BFF->>BFF: 3. Generate PKCE (code_verifier, code_challenge)
    BFF->>R: 4. Store code_verifier
    BFF->>FE: 5. Redirect to Keycloak
    FE->>KC: 6. Authorization request + code_challenge
    KC->>LDAP: 7. Authenticate user
    LDAP->>KC: 8. User credentials
    KC->>FE: 9. Authorization code
    FE->>BFF: 10. Callback with code
    BFF->>R: 11. Get code_verifier
    BFF->>KC: 12. Exchange code + code_verifier
    KC->>BFF: 13. Access + Refresh tokens
    BFF->>R: 14. Store encrypted tokens
    BFF->>FE: 15. Set session cookie (HTTP-only)
```

### Поток получения отчётов

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BFF as BFF Auth
    participant RS as Reports Service
    participant CH as ClickHouse
    participant S3 as MinIO S3
    participant CDN as Nginx CDN

    U->>FE: 1. Request reports
    FE->>BFF: 2. GET /api/reports (+ session cookie)
    BFF->>RS: 3. GET /api/reports (+ JWT)
    RS->>S3: 4. HEAD (check cache)
    alt Cache HIT
        S3->>RS: 5a. Report exists
        RS->>BFF: 6a. Return CDN URL
        BFF->>FE: 7a. CDN URL
        FE->>CDN: 8a. GET report
        CDN->>S3: 9a. Proxy (if not cached)
        CDN->>FE: 10a. Report JSON
    else Cache MISS
        RS->>CH: 5b. SELECT from OLAP
        CH->>RS: 6b. Report data
        RS->>S3: 7b. PUT report
        RS->>BFF: 8b. CDN URL
    end
```

### Поток CDC

```mermaid
sequenceDiagram
    participant CRM as CRM PostgreSQL
    participant DBZ as Debezium
    participant KFK as Kafka
    participant CH as ClickHouse

    CRM->>CRM: 1. INSERT/UPDATE/DELETE
    CRM->>DBZ: 2. WAL event (logical replication)
    DBZ->>DBZ: 3. Transform to Debezium format
    DBZ->>KFK: 4. Publish to topic crm.crm.*
    KFK->>CH: 5. KafkaEngine consumes
    CH->>CH: 6. MaterializedView transforms
    CH->>CH: 7. Insert to target table (ReplacingMergeTree)
```

## Принципы безопасности

### Защита токенов (BFF Pattern)

- Access/Refresh токены **никогда** не передаются на фронтенд
- Токены хранятся в Redis в зашифрованном виде (Fernet)
- Фронтенд работает только с HTTP-only, Secure session cookies
- Автоматическая ротация session ID для защиты от session fixation

### Многофакторная аутентификация

- Обязательный TOTP для всех пользователей
- Настройка через Keycloak Admin Console
- Поддержка Google Authenticator, Authy и др.

### Локализация данных

- Персональные данные остаются в локальных БД представительств
- Keycloak синхронизирует только аутентификационные атрибуты
- User Federation с отдельными LDAP серверами для РФ и Европы

## Следующие шаги

- [Security Architecture](security.md) — детальное описание безопасности
- [Reports & ETL](reports-etl.md) — ETL pipeline и Reports Service
- [S3/CDN Caching](s3-cdn.md) — архитектура кэширования
- [CDC Pipeline](cdc.md) — Change Data Capture
