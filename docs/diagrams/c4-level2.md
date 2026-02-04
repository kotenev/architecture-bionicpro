# C4 Level 2: Container Diagram

## Описание

Container Diagram показывает высокоуровневую архитектуру системы BionicPRO и взаимодействие между контейнерами (приложениями, базами данных, сервисами).

## Диаграмма

```plantuml
@startuml BionicPRO_C4_Level2_Container
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title BionicPRO - C4 Level 2: Container Diagram

Person(user, "Пользователь протеза", "Просматривает отчёты")
Person(operator, "Оператор CRM", "Управляет заказами")

System_Ext(prosthesis, "Бионический протез", "ESP32")
System_Ext(ldap, "LDAP Servers", "OpenLDAP")
System_Ext(external_idp, "External IdPs", "Яндекс ID")

System_Boundary(bionicpro, "BionicPRO Platform") {
    Container(frontend, "Frontend SPA", "React 18", "Веб-приложение")
    Container(keycloak, "Keycloak", "Keycloak 26.5", "Identity Provider")
    Container(bff, "BFF Auth", "Flask", "Backend-for-Frontend")
    ContainerDb(redis, "Redis", "Redis 7", "Sessions")
    Container(reports_svc, "Reports Service", "FastAPI", "REST API")
    Container(airflow, "Airflow", "Airflow 2.8", "ETL")
    Container(debezium, "Debezium", "Kafka Connect", "CDC")
    Container(kafka, "Kafka", "Kafka 3.6", "Message Broker")
    ContainerDb(crm_db, "CRM DB", "PostgreSQL", "OLTP")
    ContainerDb(telemetry_db, "Telemetry DB", "PostgreSQL", "OLTP")
    ContainerDb(clickhouse, "ClickHouse", "ClickHouse 24.1", "OLAP")
    ContainerDb(minio, "MinIO S3", "MinIO", "Object Storage")
    Container(nginx_cdn, "Nginx CDN", "Nginx", "CDN Proxy")
}

Rel(user, frontend, "HTTPS")
Rel(frontend, bff, "HTTP + Cookie")
Rel(bff, keycloak, "OAuth2 PKCE")
Rel(bff, redis, "TCP")
Rel(bff, reports_svc, "HTTP + JWT")
Rel(keycloak, ldap, "LDAPS")
Rel(keycloak, external_idp, "OAuth2")
Rel(reports_svc, clickhouse, "TCP")
Rel(reports_svc, minio, "S3 API")
Rel(frontend, nginx_cdn, "HTTPS")
Rel(nginx_cdn, minio, "HTTP")
Rel(airflow, crm_db, "SQL")
Rel(airflow, telemetry_db, "SQL")
Rel(airflow, clickhouse, "TCP")
Rel(crm_db, debezium, "WAL")
Rel(debezium, kafka, "Kafka")
Rel(kafka, clickhouse, "KafkaEngine")
Rel(prosthesis, reports_svc, "HTTPS/4G")

SHOW_LEGEND()
@enduml
```

## Слои архитектуры

### Presentation Layer

| Контейнер | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Frontend SPA | React 18, TypeScript | 3000 | Веб-приложение для пользователей |
| Nginx CDN | Nginx 1.25 | 8002 | CDN proxy с кэшированием |

### Security Layer

| Контейнер | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Keycloak | Keycloak 26.5.2 | 8080 | Identity Provider, MFA |
| BFF Auth | Python/Flask | 8000 | Backend-for-Frontend, PKCE |
| Redis | Redis 7 | 6379 | Session storage |

### Application Layer

| Контейнер | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Reports Service | Python/FastAPI | 8001 | REST API для отчётов |
| Airflow | Apache Airflow 2.8 | 8081 | ETL оркестратор |

### Data Layer

| Контейнер | Технология | Порт | Описание |
|-----------|------------|------|----------|
| CRM DB | PostgreSQL 14 | 5435 | OLTP: клиенты, заказы |
| Telemetry DB | PostgreSQL 14 | 5436 | OLTP: телеметрия |
| ClickHouse | ClickHouse 24.1 | 8123/9000 | OLAP: витрина отчётов |
| MinIO S3 | MinIO | 9001/9002 | Object storage |

### CDC Pipeline

| Контейнер | Технология | Порт | Описание |
|-----------|------------|------|----------|
| Debezium | Debezium Connect | 8083 | CDC коннектор |
| Kafka | Apache Kafka 3.6 | 9092 | Message broker |
| Zookeeper | Apache Zookeeper | 2181 | Координатор |

## Исходный файл

[c4-level2-container.puml](c4-level2-container.puml)
