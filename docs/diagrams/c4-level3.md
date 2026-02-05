# C4 Level 3: Component Diagrams

## Описание

Component Diagrams показывают внутреннюю структуру ключевых контейнеров системы BionicPRO.

## BFF Auth Service Components

Компоненты сервиса аутентификации (Backend-for-Frontend).

```plantuml
@startuml BFF_Components
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title BFF Auth Service - Components

Container_Boundary(bff, "BFF Auth Service") {
    Component(auth_ctrl, "Auth Controller", "Flask", "/auth/login, /callback, /logout")
    Component(proxy_ctrl, "Proxy Controller", "Flask", "Proxy to backend services")
    Component(pkce_svc, "PKCE Service", "Python", "code_verifier, code_challenge")
    Component(token_svc, "Token Service", "Python", "Exchange, refresh, encrypt")
    Component(session_svc, "Session Service", "Python", "Session management")
    Component(kc_client, "Keycloak Client", "requests", "OAuth2/OIDC client")
    Component(redis_client, "Redis Client", "redis-py", "Session storage")
    Component(encryption, "Encryption", "Fernet", "Token encryption")
}

Container_Ext(keycloak, "Keycloak")
ContainerDb_Ext(redis, "Redis")
Container_Ext(reports, "Reports Service")

Rel(auth_ctrl, pkce_svc, "Uses")
Rel(auth_ctrl, token_svc, "Uses")
Rel(auth_ctrl, session_svc, "Uses")
Rel(proxy_ctrl, session_svc, "Validates")
Rel(proxy_ctrl, token_svc, "Gets token")
Rel(token_svc, kc_client, "Exchange/Refresh")
Rel(token_svc, encryption, "Encrypt/Decrypt")
Rel(token_svc, redis_client, "Store")
Rel(session_svc, redis_client, "CRUD")
Rel(kc_client, keycloak, "HTTP")
Rel(redis_client, redis, "TCP")
Rel(proxy_ctrl, reports, "HTTP + JWT")

SHOW_LEGEND()
@enduml
```

### Компоненты BFF

| Компонент | Ответственность |
|-----------|-----------------|
| **Auth Controller** | Endpoints: /auth/login, /auth/callback, /auth/logout, /auth/me |
| **Proxy Controller** | Проксирование запросов к backend сервисам |
| **PKCE Service** | Генерация code_verifier и code_challenge (S256) |
| **Token Service** | Обмен кода на токены, refresh, шифрование |
| **Session Service** | Создание, валидация, ротация сессий |
| **Keycloak Client** | HTTP клиент для Keycloak API |
| **Redis Client** | Клиент для хранения сессий и токенов |
| **Encryption** | Fernet шифрование токенов |

---

## Reports Service Components

Компоненты сервиса отчётов.

```plantuml
@startuml Reports_Components
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Reports Service - Components

Container_Boundary(reports, "Reports Service") {
    Component(reports_router, "Reports Router", "FastAPI", "/api/reports, /api/reports/{date}")
    Component(cdn_router, "CDN Router", "FastAPI", "/api/reports/cdn/*, /invalidate")
    Component(health_router, "Health Router", "FastAPI", "/health, /health/cdc")
    Component(jwt_handler, "JWT Handler", "Python", "Token validation")
    Component(ch_service, "ClickHouse Service", "clickhouse-connect", "OLAP queries")
    Component(s3_service, "S3 Service", "boto3", "Object storage")
    Component(cache_service, "Cache Service", "redis-py", "Metadata cache")
    Component(report_gen, "Report Generator", "Python", "JSON report generation")
    Component(cdc_monitor, "CDC Monitor", "Python", "CDC health monitoring")
}

ContainerDb_Ext(clickhouse, "ClickHouse")
ContainerDb_Ext(minio, "MinIO S3")
ContainerDb_Ext(redis, "Redis")

Rel(reports_router, jwt_handler, "Auth")
Rel(reports_router, ch_service, "Query")
Rel(cdn_router, s3_service, "S3 ops")
Rel(cdn_router, report_gen, "Generate")
Rel(health_router, cdc_monitor, "Check CDC")
Rel(report_gen, ch_service, "Fetch data")
Rel(report_gen, s3_service, "Store")
Rel(ch_service, clickhouse, "TCP/9000")
Rel(s3_service, minio, "S3 API")
Rel(cache_service, redis, "TCP")

SHOW_LEGEND()
@enduml
```

### Компоненты Reports Service

| Компонент | Ответственность |
|-----------|-----------------|
| **Reports Router** | REST endpoints для отчётов |
| **CDN Router** | CDN URLs и cache invalidation |
| **Health Router** | Health checks, CDC monitoring |
| **JWT Handler** | Валидация JWT токенов |
| **ClickHouse Service** | Запросы к OLAP базе |
| **S3 Service** | Работа с MinIO S3 |
| **Cache Service** | Кэширование метаданных |
| **Report Generator** | Генерация JSON отчётов |
| **CDC Monitor** | Мониторинг CDC pipeline |

---

## ETL Pipeline Components

Компоненты ETL pipeline (Apache Airflow).

```plantuml
@startuml ETL_Components
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title ETL Pipeline - Components

Container_Boundary(airflow, "Apache Airflow") {
    Component(webserver, "Webserver", "Flask", "Web UI")
    Component(scheduler, "Scheduler", "Python", "DAG scheduling")
    Component(executor, "Executor", "Python", "Task execution")
}

Container_Boundary(etl, "ETL Jobs") {
    Component(dag_reports, "bionicpro_reports_etl", "DAG", "Main ETL, */15 * * * *")
    Component(extract_crm, "extract_crm_data", "Task", "Extract from CRM")
    Component(extract_tel, "extract_telemetry", "Task", "Extract telemetry")
    Component(transform, "transform_and_join", "Task", "JOIN, calculate metrics")
    Component(load, "load_to_clickhouse", "Task", "INSERT to OLAP")
    Component(invalidate, "invalidate_cache", "Task", "Clear CDN cache")
}

ContainerDb_Ext(crm_db, "CRM DB")
ContainerDb_Ext(tel_db, "Telemetry DB")
ContainerDb_Ext(clickhouse, "ClickHouse")
Container_Ext(reports_svc, "Reports Service")

Rel(scheduler, executor, "Submit")
Rel(executor, dag_reports, "Execute")
Rel(dag_reports, extract_crm, "Task 1")
Rel(dag_reports, extract_tel, "Task 2")
Rel(extract_crm, transform, "XCom")
Rel(extract_tel, transform, "XCom")
Rel(transform, load, "XCom")
Rel(load, invalidate, "Trigger")
Rel(extract_crm, crm_db, "SQL")
Rel(extract_tel, tel_db, "SQL")
Rel(load, clickhouse, "INSERT")
Rel(invalidate, reports_svc, "POST")

SHOW_LEGEND()
@enduml
```

---

## CDC Pipeline Components

Компоненты CDC pipeline (Debezium → Kafka → ClickHouse).

```plantuml
@startuml CDC_Components
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title CDC Pipeline - Components

Container_Boundary(postgres, "CRM PostgreSQL") {
    Component(wal, "WAL", "PostgreSQL", "wal_level=logical")
    Component(publication, "Publication", "PostgreSQL", "crm_publication")
    Component(slot, "Replication Slot", "PostgreSQL", "debezium_crm_slot")
}

Container_Boundary(debezium, "Debezium Connect") {
    Component(connector, "PostgreSQL Connector", "Java", "CDC connector")
    Component(transforms, "SMT Transforms", "Java", "ExtractNewRecordState")
    Component(converter, "JSON Converter", "Kafka Connect", "Serialization")
}

Container_Boundary(kafka, "Apache Kafka") {
    Component(topic_cust, "crm.crm.customers", "Topic", "Customer events")
    Component(topic_pros, "crm.crm.prostheses", "Topic", "Prostheses events")
    Component(topic_mod, "crm.crm.models", "Topic", "Models events")
}

Container_Boundary(clickhouse, "ClickHouse") {
    Component(kafka_engine, "KafkaEngine Tables", "ClickHouse", "Consume from Kafka")
    Component(mv, "MaterializedViews", "ClickHouse", "Transform & insert")
    Component(target, "Target Tables", "ReplacingMergeTree", "Deduplicated data")
    Component(cdc_view, "cdc_customer_data", "View", "Joined CDC data")
}

Rel(wal, publication, "Contains")
Rel(slot, connector, "Stream")
Rel(connector, transforms, "Events")
Rel(transforms, converter, "Transformed")
Rel(converter, topic_cust, "Publish")
Rel(converter, topic_pros, "Publish")
Rel(converter, topic_mod, "Publish")
Rel(topic_cust, kafka_engine, "Consume")
Rel(topic_pros, kafka_engine, "Consume")
Rel(topic_mod, kafka_engine, "Consume")
Rel(kafka_engine, mv, "Trigger")
Rel(mv, target, "INSERT")
Rel(cdc_view, target, "SELECT FINAL")

SHOW_LEGEND()
@enduml
```

## Исходные файлы

- [c4-level3-bff-component.puml](c4-level3-bff-component.puml)
- [c4-level3-reports-component.puml](c4-level3-reports-component.puml)
- [c4-level3-etl-component.puml](c4-level3-etl-component.puml)
- [c4-level3-cdc-component.puml](c4-level3-cdc-component.puml)
