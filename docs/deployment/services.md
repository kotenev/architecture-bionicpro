# Service Reference

## Обзор сервисов

### Application Services

| Service | Port | Technology | Описание |
|---------|------|------------|----------|
| frontend | 3000 | React 18 | SPA для пользователей |
| bionicpro-auth | 8000 | Flask | BFF для аутентификации |
| reports-service | 8001 | FastAPI | REST API для отчётов |

### Security Services

| Service | Port | Technology | Описание |
|---------|------|------------|----------|
| keycloak | 8080 | Keycloak 26.5.2 | Identity Provider |
| ldap | 389 | OpenLDAP 1.5.0 | Directory Service |
| redis | 6379 | Redis 7 | Session Storage |

### Data Services

| Service | Port | Technology | Описание |
|---------|------|------------|----------|
| crm_db | 5435 | PostgreSQL 14 | CRM база данных |
| telemetry_db | 5436 | PostgreSQL 14 | База телеметрии |
| clickhouse | 8123/9000 | ClickHouse 24.1 | OLAP база данных |

### CDC Pipeline

| Service | Port | Technology | Описание |
|---------|------|------------|----------|
| kafka | 9092 | Kafka 3.6 | Message Broker |
| zookeeper | 2181 | Zookeeper | Kafka координатор |
| debezium | 8083 | Debezium | CDC коннектор |
| kafka-ui | 8084 | Kafka UI | Мониторинг Kafka |

### ETL & Caching

| Service | Port | Technology | Описание |
|---------|------|------------|----------|
| airflow-webserver | 8081 | Airflow 2.8.1 | ETL UI |
| airflow-scheduler | - | Airflow 2.8.1 | ETL планировщик |
| minio | 9001/9002 | MinIO | S3 хранилище |
| nginx-cdn | 8002 | Nginx 1.25 | CDN proxy |

## Health Checks

### Все сервисы

```bash
# Frontend
curl -s http://localhost:3000 | head -1

# BFF Auth
curl -s http://localhost:8000/health

# Reports Service
curl -s http://localhost:8001/health/live

# Keycloak
curl -s http://localhost:8080/health/ready

# Airflow
curl -s http://localhost:8081/health

# ClickHouse
curl -s "http://localhost:8123/?query=SELECT%201"

# Debezium
curl -s http://localhost:8083/connectors

# MinIO
curl -s http://localhost:9002/minio/health/live

# Nginx CDN
curl -s http://localhost:8002/health
```

### Автоматизированная проверка

```bash
#!/bin/bash
# scripts/healthcheck.sh

services=(
    "http://localhost:3000|Frontend"
    "http://localhost:8000/health|BFF Auth"
    "http://localhost:8001/health/live|Reports Service"
    "http://localhost:8080/health/ready|Keycloak"
    "http://localhost:8123/?query=SELECT%201|ClickHouse"
)

for service in "${services[@]}"; do
    url="${service%%|*}"
    name="${service##*|}"
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✓ $name"
    else
        echo "✗ $name"
    fi
done
```

## Управление сервисами

### Запуск

```bash
# Все сервисы
docker-compose up -d

# Конкретный сервис
docker-compose up -d reports-service

# Группа сервисов (Security)
docker-compose up -d ldap keycloak keycloak-db redis bionicpro-auth
```

### Остановка

```bash
# Все сервисы
docker-compose down

# Конкретный сервис
docker-compose stop reports-service

# С удалением volumes
docker-compose down -v
```

### Перезапуск

```bash
# Конкретный сервис
docker-compose restart reports-service

# Пересборка и перезапуск
docker-compose up -d --build reports-service
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f reports-service

# Последние 100 строк
docker-compose logs --tail=100 airflow-scheduler

# С timestamps
docker-compose logs -f --timestamps reports-service
```

## Конфигурация сервисов

### Frontend

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  environment:
    REACT_APP_AUTH_URL: http://localhost:8000
```

### BFF Auth

```yaml
bionicpro-auth:
  build: ./bionicpro-auth
  ports:
    - "8000:8000"
  environment:
    KEYCLOAK_URL: http://keycloak:8080
    KEYCLOAK_PUBLIC_URL: http://localhost:8080
    KEYCLOAK_REALM: reports-realm
    CLIENT_ID: bionicpro-auth
    REDIS_HOST: redis
    ENCRYPTION_KEY: ${ENCRYPTION_KEY}
```

### Reports Service

```yaml
reports-service:
  build: ./reports-service
  ports:
    - "8001:8001"
  environment:
    CLICKHOUSE_HOST: clickhouse
    CLICKHOUSE_PORT: 9000
    CLICKHOUSE_DATABASE: reports
    REDIS_HOST: redis
    S3_ENDPOINT_URL: http://minio:9000
    CDN_BASE_URL: http://localhost:8002
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092
```

### Keycloak

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:26.5.2
  ports:
    - "8080:8080"
  environment:
    KEYCLOAK_ADMIN: admin
    KEYCLOAK_ADMIN_PASSWORD: admin
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://keycloak_db:5432/keycloak_db
  command:
    - start-dev
    - --import-realm
```

### ClickHouse

```yaml
clickhouse:
  image: clickhouse/clickhouse-server:24.1
  ports:
    - "8123:8123"  # HTTP
    - "9000:9000"  # Native
  environment:
    CLICKHOUSE_DB: reports
    CLICKHOUSE_USER: default
```

### Kafka

```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

## Database Connections

### PostgreSQL

| Database | Host | Port | User | Password | DB |
|----------|------|------|------|----------|-----|
| Keycloak | localhost | 5433 | keycloak_user | keycloak_password | keycloak_db |
| BionicPRO | localhost | 5434 | bionicpro_user | bionicpro_password | bionicpro_db |
| CRM | localhost | 5435 | crm_user | crm_password | crm_db |
| Telemetry | localhost | 5436 | telemetry_user | telemetry_password | telemetry_db |
| Airflow | - | - | airflow | airflow | airflow |

### Connection Strings

```bash
# CRM DB
postgresql://crm_user:crm_password@localhost:5435/crm_db

# Telemetry DB
postgresql://telemetry_user:telemetry_password@localhost:5436/telemetry_db

# ClickHouse HTTP
http://localhost:8123?database=reports

# ClickHouse Native
clickhouse://default@localhost:9000/reports
```

## Volumes

### Persistent Data

| Volume | Path | Описание |
|--------|------|----------|
| postgres-keycloak-data | ./postgres-keycloak-data | Keycloak DB |
| postgres-bionicpro-data | ./postgres-bionicpro-data | BionicPRO DB |
| postgres-crm-data | ./postgres-crm-data | CRM DB |
| postgres-telemetry-data | ./postgres-telemetry-data | Telemetry DB |
| postgres-airflow-data | ./postgres-airflow-data | Airflow DB |
| clickhouse-data | ./clickhouse-data | ClickHouse |
| minio-data | ./minio-data | S3 Storage |
| redis-data | ./redis-data | Redis |
| ldap-data | ./ldap-data | LDAP |

### Очистка volumes

```bash
# Полная очистка
./scripts/clean.sh

# Ручная очистка
docker-compose down -v
rm -rf ./postgres-*-data ./clickhouse-data ./minio-data ./redis-data ./ldap-*
```

## Resource Requirements

### Minimum

| Resource | Value |
|----------|-------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 20 GB |

### Recommended

| Resource | Value |
|----------|-------|
| CPU | 8 cores |
| RAM | 16 GB |
| Disk | 50 GB |

### Per-Service Memory

| Service | Memory |
|---------|--------|
| Keycloak | 512MB - 1GB |
| ClickHouse | 1GB - 4GB |
| Kafka | 512MB - 1GB |
| Airflow (total) | 1GB - 2GB |
| Reports Service | 256MB - 512MB |

## См. также

- [Quick Start](quickstart.md)
- [Environment Setup](environment.md)
- [Troubleshooting](troubleshooting.md)
