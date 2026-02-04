# Sequence Diagrams

## Описание

Диаграммы последовательности показывают взаимодействие компонентов системы во времени для ключевых бизнес-процессов.

## Authentication Flow (OAuth2 PKCE)

Процесс аутентификации пользователя с использованием OAuth2 PKCE flow.

```plantuml
@startuml Auth_Flow
!theme plain
title Authentication Flow (OAuth2 PKCE)

actor User
participant "Frontend" as FE
participant "BFF Auth" as BFF
participant "Redis" as Redis
participant "Keycloak" as KC
participant "LDAP" as LDAP

== Login ==
User -> FE: Click Login
FE -> BFF: GET /auth/login
BFF -> BFF: Generate PKCE\n(verifier, challenge)
BFF -> Redis: Store verifier
BFF --> FE: 302 → Keycloak

FE -> KC: Auth Request + challenge
KC -> LDAP: Validate credentials
LDAP --> KC: User found
KC --> FE: 302 + auth code

== Token Exchange ==
FE -> BFF: GET /callback?code=xxx
BFF -> Redis: Get verifier
BFF -> KC: POST /token + verifier
KC --> BFF: access + refresh tokens
BFF -> BFF: Encrypt tokens
BFF -> Redis: Store encrypted tokens
BFF --> FE: Set-Cookie: session_id

== API Request ==
User -> FE: View reports
FE -> BFF: GET /api/reports + Cookie
BFF -> Redis: Get tokens
BFF -> BFF: Decrypt access_token
BFF -> "Reports" as RS: GET + Bearer token
RS --> BFF: Data
BFF --> FE: Response

@enduml
```

---

## CDC Data Flow

Процесс репликации данных из CRM в ClickHouse через CDC pipeline.

```plantuml
@startuml CDC_Flow
!theme plain
title CDC Data Flow (Debezium → Kafka → ClickHouse)

participant "CRM\nPostgreSQL" as CRM
participant "WAL" as WAL
participant "Debezium" as DBZ
participant "Kafka" as KFK
participant "ClickHouse\nKafkaEngine" as KE
participant "MaterializedView" as MV
participant "Target Table" as TT

== INSERT ==
CRM -> WAL: Write INSERT
WAL -> DBZ: Stream event
DBZ -> DBZ: Transform (SMT)
DBZ -> KFK: Publish to topic

KFK -> KE: Consume
KE -> MV: Trigger
MV -> MV: Extract JSON fields\nSet _version, _deleted=0
MV -> TT: INSERT

== UPDATE ==
CRM -> WAL: Write UPDATE
WAL -> DBZ: Stream event
DBZ -> KFK: Publish
KFK -> KE: Consume
KE -> MV: Trigger
MV -> MV: Set new _version
MV -> TT: INSERT (new version)

note right of TT
  ReplacingMergeTree
  keeps latest _version
end note

== DELETE ==
CRM -> WAL: Write DELETE
WAL -> DBZ: Stream event
DBZ -> KFK: Publish (__op = 'd')
KFK -> KE: Consume
KE -> MV: Trigger
MV -> MV: Set _deleted = 1
MV -> TT: INSERT

@enduml
```

---

## Reports Flow with CDN Caching

Процесс получения отчётов с использованием CDN кэширования.

```plantuml
@startuml Reports_Flow
!theme plain
title Reports Flow with CDN Caching

actor User
participant "Frontend" as FE
participant "BFF" as BFF
participant "Reports\nService" as RS
participant "MinIO S3" as S3
participant "Nginx CDN" as CDN
participant "ClickHouse" as CH

User -> FE: View report
FE -> BFF: GET /api/reports/cdn/2024-01-15
BFF -> RS: GET + JWT

RS -> S3: HEAD (check exists)

alt Cache HIT
    S3 --> RS: 200 OK
    RS --> BFF: CDN URL
    BFF --> FE: CDN URL
    FE -> CDN: GET report
    CDN -> CDN: Check cache
    alt CDN HIT
        CDN --> FE: Report (cached)
    else CDN MISS
        CDN -> S3: GET
        S3 --> CDN: Report
        CDN --> FE: Report
    end
else Cache MISS
    S3 --> RS: 404
    RS -> CH: SELECT
    CH --> RS: Data
    RS -> RS: Generate JSON
    RS -> S3: PUT report
    RS --> BFF: CDN URL
    BFF --> FE: CDN URL
    FE -> CDN: GET report
    CDN -> S3: GET
    CDN --> FE: Report
end

FE --> User: Display

@enduml
```

---

## ETL Pipeline Flow

Процесс выполнения ETL pipeline в Apache Airflow.

```plantuml
@startuml ETL_Flow
!theme plain
title ETL Pipeline Flow

participant "Scheduler" as Sched
participant "Executor" as Exec
participant "CRM DB" as CRM
participant "Telemetry DB" as TEL
participant "ClickHouse" as CH
participant "Reports\nService" as RS

Sched -> Exec: Trigger DAG\n(*/15 * * * *)

== Parallel Extract ==
par
    Exec -> CRM: SELECT customers,\nprostheses, models
    CRM --> Exec: CRM DataFrame
and
    Exec -> TEL: SELECT aggregated\ntelemetry
    TEL --> Exec: Telemetry DataFrame
end

== Transform ==
Exec -> Exec: JOIN on chip_id
Exec -> Exec: Calculate metrics:\nerror_rate, etc.

== Load ==
Exec -> CH: INSERT INTO\nuser_prosthesis_stats
CH --> Exec: OK

Exec -> Exec: Get affected user_ids

== Invalidate Cache ==
loop for each user_id
    Exec -> RS: POST /invalidate
    RS --> Exec: OK
end

Exec -> Sched: DAG completed

@enduml
```

## Исходные файлы

- [sequence-auth-flow.puml](sequence-auth-flow.puml)
- [sequence-cdc-flow.puml](sequence-cdc-flow.puml)
- [sequence-reports-flow.puml](sequence-reports-flow.puml)
- [sequence-etl-flow.puml](sequence-etl-flow.puml)
