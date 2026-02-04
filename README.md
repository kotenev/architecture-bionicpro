# BionicPRO Architecture Project

## Overview

BionicPRO is a Russian company that produces and sells bionic prosthetics. This project implements a comprehensive architecture solution for managing user authentication, data collection from prosthetic devices, and generating reports. The system addresses security vulnerabilities discovered after a previous breach and implements enhanced data privacy controls.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Service Architecture](#architecture-components)
- [Deployment Guide](#detailed-deployment-guide)
- [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd architecture-bionicpro

# 2. Configure environment (see detailed instructions below)
cp .env.example .env
# Edit .env and set required values

# 3. Start all services
docker-compose up -d

# 4. Wait for initialization (2-3 minutes)
docker-compose logs -f airflow-etl-trigger

# 5. Access the application
open http://localhost:3000
```

## Environment Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Generate Required Secrets

The system requires three secret keys to be configured in `.env`:

#### 2.1 Generate Airflow Fernet Key

Used to encrypt sensitive data in Airflow (connections, variables).

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to `.env`:
```bash
AIRFLOW_FERNET_KEY=<generated-key>
```

#### 2.2 Generate BFF Encryption Key

Used to encrypt OAuth tokens stored in Redis.

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to `.env`:
```bash
ENCRYPTION_KEY=<generated-key>
```

#### 2.3 Generate JWT Secret Key

Used for signing/verifying JWT tokens in Reports Service.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Or: openssl rand -base64 32
```

Add the output to `.env`:
```bash
JWT_SECRET_KEY=<generated-key>
```

### Step 3: (Optional) Configure Yandex ID

For external identity provider integration:

1. Register application at https://oauth.yandex.ru/
2. Set Callback URL: `http://localhost:8080/realms/reports-realm/broker/yandex/endpoint`
3. Add credentials to `.env`:

```bash
YANDEX_CLIENT_ID=<your-client-id>
YANDEX_CLIENT_SECRET=<your-client-secret>
```

### Complete .env Example

```bash
# Required
AIRFLOW_FERNET_KEY=Wv1Qp3R5t7Y9uBdEfGhJkLmNoP2sUwXz4a6C8i0qR1s=
ENCRYPTION_KEY=kL3mN5pQ7rS9tV1xZ3bD5fH7jL9nP1sU3wY5a7c9e1g=
JWT_SECRET_KEY=your-secure-jwt-secret-key-here-32chars

# Optional
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
```

### Security Notes

- **Never commit `.env` to version control** (already in `.gitignore`)
- For production, use secrets management (HashiCorp Vault, AWS Secrets Manager, etc.)
- Rotate keys periodically in production environments
- Each key must be unique - do not reuse the same key for different purposes

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Python 3.8+ (only for generating keys)

## Running the Application

### Full Stack Deployment

```bash
# Start all services
docker-compose up -d

# Monitor initialization
docker-compose logs -f airflow-etl-trigger

# Verify all services are running
docker-compose ps
```

### Verify Services Health

```bash
# Keycloak
curl -s http://localhost:8080/health/ready | jq .

# Airflow
curl -s http://localhost:8081/health | jq .

# Reports Service
curl -s http://localhost:8001/health/live | jq .

# ClickHouse
curl -s "http://localhost:8123/?query=SELECT%201"

# Debezium CDC
curl -s http://localhost:8083/connectors | jq .
```

### Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | LDAP users (see below) |
| Keycloak Admin | http://localhost:8080/admin | admin / admin |
| Airflow UI | http://localhost:8081 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| Kafka UI | http://localhost:8084 | - |
| Reports API Docs | http://localhost:8001/docs | - |

### Test Users (LDAP)

All passwords: `password123`

| Username | Role | Description |
|----------|------|-------------|
| ivan.petrov | prothetic_user | Has prosthesis reports |
| john.mueller | prothetic_user | Has prosthesis reports |
| maria.sidorova | user | Regular user |
| anna.schmidt | user | Regular user |
| alexey.kozlov | administrator | Admin access |

### Stopping Services

```bash
# Stop all services (preserves data)
docker-compose down

# Stop and remove all data (clean start)
./scripts/clean.sh
```

### Regenerating Demo Data

```bash
# Regenerate reports for all test users (7 days of data)
docker-compose exec clickhouse clickhouse-client \
  --queries-file /docker-entrypoint-initdb.d/03_regenerate_demo_data.sql

# Trigger ETL to refresh
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl
```

## Architecture Components

- **Authentication Layer**: Keycloak with OAuth 2.0 and PKCE
- **Backend Services**: Flask-based authentication service
- **Database Layer**: PostgreSQL for operational data, ClickHouse for analytics
- **ETL Pipeline**: Apache Airflow for data processing
- **Frontend**: React/TypeScript application

## Data Pipeline

The system implements an ETL process that:
1. Extracts customer data from CRM PostgreSQL
2. Extracts telemetry data from Telemetry PostgreSQL
3. Transforms and joins the datasets
4. Loads the results to ClickHouse for reporting

---

## Detailed Deployment Guide

This section describes deployment of all implemented features from Sprint 9 tasks.

### Task 1: Security Architecture (Задание 1)

Implementation of enhanced security with unified access management and BFF pattern.

#### Implemented Features

- **LDAP User Federation**: Centralized user management via OpenLDAP
- **BFF Pattern**: Backend-for-Frontend with server-side token storage
- **OAuth2 PKCE**: Secure authorization code flow with S256 challenge
- **Identity Brokering**: Support for external IdPs (Yandex ID)
- **MFA/TOTP**: Mandatory two-factor authentication

#### Deployment Steps

1. **Start core security services**:
   ```bash
   docker-compose up -d ldap keycloak keycloak-db redis bionicpro-auth bionicpro-db
   ```

2. **Wait for Keycloak to initialize** (approx. 60 seconds):
   ```bash
   # Check Keycloak health
   curl -s http://localhost:8080/health/ready
   ```

3. **Verify LDAP connection**:
   ```bash
   # Test LDAP bind
   ldapsearch -x -H ldap://localhost:389 -D "cn=admin,dc=bionicpro,dc=com" -w admin -b "ou=People,dc=bionicpro,dc=com"
   ```

4. **Access Keycloak Admin Console**:
   - URL: http://localhost:8080/admin
   - Credentials: admin / admin
   - Realm: `reports-realm`

5. **(Optional) Configure Yandex ID**:
   ```bash
   # Set environment variables before docker-compose up
   export YANDEX_CLIENT_ID=your-client-id
   export YANDEX_CLIENT_SECRET=your-client-secret
   ```

#### Test Users (LDAP)

| Username | Password | Role | Branch |
|----------|----------|------|--------|
| ivan.petrov | password123 | prothetic_user | Russia |
| maria.sidorova | password123 | user | Russia |
| alexey.kozlov | password123 | administrator | Russia |
| john.mueller | password123 | prothetic_user | Europe |
| anna.schmidt | password123 | user | Europe |

#### Security Architecture Diagram

See: `diagrams/(TO-BE) BionicPRO_C4_container_Security_Architecture_Task1.puml`

---

### Task 2: Reports Service & ETL (Задание 2)

Implementation of ETL pipeline and Reports API for prosthesis usage data.

#### Implemented Features

- **Apache Airflow**: ETL orchestration with scheduled DAGs
- **ClickHouse OLAP**: Analytical database with partitioned data mart
- **Reports Service**: FastAPI-based REST API for reports
- **JWT Authentication**: Secure access with Keycloak token validation

#### Deployment Steps

1. **Start data infrastructure**:
   ```bash
   docker-compose up -d crm_db telemetry_db clickhouse
   ```

2. **Wait for databases to initialize**:
   ```bash
   # Verify CRM DB
   docker-compose exec crm_db psql -U crm_user -d crm_db -c "SELECT COUNT(*) FROM crm.customers;"

   # Verify Telemetry DB
   docker-compose exec telemetry_db psql -U telemetry_user -d telemetry_db -c "SELECT COUNT(*) FROM telemetry.raw_telemetry;"

   # Verify ClickHouse
   curl "http://localhost:8123/?query=SELECT%201"
   ```

3. **Start Airflow**:
   ```bash
   docker-compose up -d airflow-init airflow-webserver airflow-scheduler airflow-connections airflow-etl-trigger
   ```

   **Note**: The `airflow-etl-trigger` service automatically runs the initial ETL after Airflow is ready, populating ClickHouse with demo reports. This ensures users can immediately see reports after login.

4. **Access Airflow UI**:
   - URL: http://localhost:8081
   - Credentials: admin / admin
   - DAG `bionicpro_reports_etl` is auto-enabled and triggered on startup

5. **Start Reports Service**:
   ```bash
   docker-compose up -d reports-service
   ```

6. **Verify Reports API**:
   ```bash
   # Health check
   curl http://localhost:8001/health

   # Get reports (requires JWT token from authenticated session)
   # Login via frontend at http://localhost:3000 to get a session
   ```

#### ETL Schedule

The `bionicpro_reports_etl` DAG runs every 15 minutes and performs:
1. Extract CRM data (customers, prostheses, models)
2. Extract telemetry data (hourly aggregates from last 7 days)
3. Transform and join datasets by chip_id
4. Load to ClickHouse `reports.user_prosthesis_stats`

**Initial Load**: On first startup, the ETL is triggered automatically by the `airflow-etl-trigger` service, which loads demo data for test users (ivan.petrov, john.mueller, etc.)

#### Reports API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/reports | List user's reports |
| GET | /api/reports/summary | User summary statistics |
| GET | /api/reports/{date} | Daily report with hourly breakdown |
| GET | /health | Service health check |

#### Architecture Diagram

See: `diagrams/(TO-BE) BionicPRO_C4_container_Reports_and_ETL_Architecture_Task2.puml`

---

### Task 3: S3/CDN Architecture (Задание 3)

Implementation of report caching with S3 storage and CDN delivery.

#### Implemented Features

- **MinIO**: S3-compatible object storage for reports
- **Nginx CDN**: Reverse proxy with static file caching
- **Cache Invalidation**: TTL-based and ETL-triggered cache refresh
- **CDN URLs**: Direct links to cached reports

#### Deployment Steps

1. **Start S3/CDN infrastructure**:
   ```bash
   docker-compose up -d minio nginx-cdn
   ```

2. **Wait for MinIO to initialize**:
   ```bash
   # Check MinIO health
   curl -s http://localhost:9002/minio/health/live
   ```

3. **Access MinIO Console**:
   - URL: http://localhost:9001
   - Credentials: minioadmin / minioadmin123
   - Bucket: `reports-bucket` (auto-created)

4. **Verify CDN proxy**:
   ```bash
   curl -I http://localhost:8002/health
   ```

5. **Test CDN flow**:
   ```bash
   # Get CDN URL for reports list
   curl -H "Authorization: Bearer <token>" http://localhost:8001/api/reports/cdn/list

   # Response includes cdn_url to fetch report directly
   curl http://localhost:8002/reports/{user_id}/list/reports.json
   ```

#### S3 Storage Structure

```
reports-bucket/
├── {user_id}/
│   ├── list/
│   │   └── reports.json       # Available reports list
│   ├── summary/
│   │   └── summary.json       # User summary stats
│   └── daily/
│       └── {YYYY-MM-DD}/
│           └── report.json    # Daily detailed report
```

#### CDN Cache Configuration

- **Cache TTL**: 5 minutes (configurable in nginx.conf)
- **Cache Size**: 1GB max
- **Invalidation**: Automatic after ETL completion

#### CDN API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/reports/cdn/list | Get CDN URL for reports list |
| GET | /api/reports/cdn/summary | Get CDN URL for user summary |
| GET | /api/reports/cdn/{date} | Get CDN URL for daily report |
| POST | /api/reports/invalidate | Invalidate cache (admin) |

#### Architecture Diagram

See: `diagrams/(TO-BE) BionicPRO_C4_container_S3_CDN_Architecture_Task3.puml`

---

### Task 4: CDC Architecture (Задание 4)

Implementation of Change Data Capture for OLTP/OLAP workload separation.

#### Implemented Features

- **Debezium**: PostgreSQL CDC connector for CRM database
- **Kafka**: Message broker for CDC event streaming
- **ClickHouse KafkaEngine**: Direct ingestion from Kafka topics
- **MaterializedViews**: Automatic data transformation
- **CDC ETL DAG**: Modified pipeline reading from ClickHouse (not CRM)

#### Deployment Steps

1. **Start Kafka infrastructure**:
   ```bash
   docker-compose up -d zookeeper kafka kafka-ui
   ```

2. **Wait for Kafka to be ready**:
   ```bash
   # Check Kafka broker
   docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
   ```

3. **Start Debezium Connect**:
   ```bash
   docker-compose up -d debezium debezium-init
   ```

4. **Verify Debezium connector registration**:
   ```bash
   # List connectors
   curl http://localhost:8083/connectors

   # Check CRM connector status
   curl http://localhost:8083/connectors/crm-connector/status
   ```

5. **Access Kafka UI**:
   - URL: http://localhost:8084
   - Topics: `crm.crm.customers`, `crm.crm.prostheses`, `crm.crm.prosthesis_models`

6. **Verify ClickHouse CDC tables**:
   ```bash
   # Check CDC data in ClickHouse
   curl "http://localhost:8123/" -d "SELECT * FROM reports.crm_customers LIMIT 5"
   curl "http://localhost:8123/" -d "SELECT * FROM reports.cdc_customer_data LIMIT 5"
   ```

7. **Enable CDC ETL DAG**:
   - In Airflow UI, enable `bionicpro_reports_cdc_etl`
   - This DAG reads CRM data from ClickHouse instead of PostgreSQL

#### CDC Data Flow

```
CRM PostgreSQL (wal_level=logical)
         │
         ▼
    Debezium Connector
         │
         ▼
    Kafka Topics (crm.crm.*)
         │
         ▼
    ClickHouse KafkaEngine Tables
         │
         ▼
    MaterializedViews
         │
         ▼
    CDC Target Tables (ReplacingMergeTree)
         │
         ▼
    cdc_customer_data (Mart)
```

#### Kafka Topics

| Topic | Description |
|-------|-------------|
| crm.crm.customers | Customer changes |
| crm.crm.prostheses | Prosthesis changes |
| crm.crm.prosthesis_models | Model catalog changes |

#### ClickHouse CDC Tables

| Table | Type | Description |
|-------|------|-------------|
| kafka_crm_customers | Kafka Engine | Reads from Kafka |
| crm_customers | ReplacingMergeTree | Deduplicated customer data |
| mv_kafka_customers | MaterializedView | Auto-insert trigger |
| cdc_customer_data | View | Joined mart for reports |

#### Debezium Admin API

```bash
# List connectors
curl http://localhost:8083/connectors

# Connector status
curl http://localhost:8083/connectors/crm-connector/status

# Pause connector
curl -X PUT http://localhost:8083/connectors/crm-connector/pause

# Resume connector
curl -X PUT http://localhost:8083/connectors/crm-connector/resume
```

#### CDC Health Check

```bash
curl http://localhost:8001/health/cdc
```

Response:
```json
{
  "status": "healthy",
  "cdc_tables": {
    "crm_customers": {"rows": 5},
    "crm_prostheses": {"rows": 5},
    "crm_prosthesis_models": {"rows": 5}
  }
}
```

#### Architecture Diagram

See: `diagrams/(TO-BE) BionicPRO_C4_container_CDC_Architecture_Task4.puml`

---

## Full Stack Deployment

For complete setup instructions, see [Environment Configuration](#environment-configuration) and [Running the Application](#running-the-application) sections above.

### Quick Reference Commands

```bash
# Full system start
docker-compose up -d

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f reports-service

# Check service status
docker-compose ps

# Restart a service
docker-compose restart reports-service

# Scale down unused services (e.g., disable CDC)
docker-compose stop debezium kafka zookeeper kafka-ui
```

## Service Ports Summary

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| Frontend | 3000 | React SPA | http://localhost:3000 |
| BFF Auth | 8000 | Token management | http://localhost:8000/health |
| Reports Service | 8001 | Reports REST API | http://localhost:8001/health/live |
| Nginx CDN | 8002 | S3 caching proxy | http://localhost:8002/health |
| Keycloak | 8080 | Identity provider | http://localhost:8080/health/ready |
| Airflow | 8081 | ETL orchestration | http://localhost:8081/health |
| Debezium | 8083 | CDC connector | http://localhost:8083/connectors |
| Kafka UI | 8084 | Kafka monitoring | http://localhost:8084 |
| ClickHouse HTTP | 8123 | OLAP database | http://localhost:8123/?query=SELECT%201 |
| MinIO Console | 9001 | S3 storage UI | http://localhost:9001 |
| MinIO S3 API | 9002 | S3 API endpoint | http://localhost:9002/minio/health/live |
| Kafka | 9092 | Message broker | - |
| ClickHouse Native | 9000 | ClickHouse TCP | - |
| LDAP | 389 | Directory service | - |

### Database Ports (for debugging)

| Database | Port | Connection String |
|----------|------|-------------------|
| Keycloak DB | 5433 | `postgresql://keycloak_user:keycloak_password@localhost:5433/keycloak_db` |
| BionicPRO DB | 5434 | `postgresql://bionicpro_user:bionicpro_password@localhost:5434/bionicpro_db` |
| CRM DB | 5435 | `postgresql://crm_user:crm_password@localhost:5435/crm_db` |
| Telemetry DB | 5436 | `postgresql://telemetry_user:telemetry_password@localhost:5436/telemetry_db` |

## Troubleshooting

### Environment Variables Not Set

**Symptom**: Services fail to start or show encryption errors.

```bash
# Verify .env file exists and has values
cat .env

# Check if variables are loaded (should show your values)
docker-compose config | grep -E "AIRFLOW_FERNET_KEY|ENCRYPTION_KEY|JWT_SECRET_KEY"
```

**Fix**: Ensure all required variables are set in `.env` file (see [Environment Configuration](#environment-configuration)).

### Keycloak Not Starting

```bash
# Check logs
docker-compose logs keycloak

# Common issues:
# 1. Database not ready - wait for keycloak_db
docker-compose up -d keycloak_db
sleep 30
docker-compose up -d keycloak

# 2. Port 8080 already in use
lsof -i :8080
# Kill conflicting process or change port in docker-compose.yaml
```

### Authentication Errors

**Symptom**: "Invalid token" or "Token validation failed" errors.

```bash
# 1. Verify Keycloak is running
curl -s http://localhost:8080/health/ready

# 2. Check BFF can reach Keycloak
docker-compose logs bionicpro-auth | grep -i error

# 3. Verify realm configuration
curl -s http://localhost:8080/realms/reports-realm/.well-known/openid-configuration | jq .

# 4. Clear Redis session cache
docker-compose exec redis redis-cli FLUSHALL
```

### Debezium Connector Not Registering

```bash
# Check Debezium logs
docker-compose logs debezium

# Re-run initialization
docker-compose restart debezium-init

# Manual registration
curl -X POST -H "Content-Type: application/json" \
  --data @debezium/crm-connector.json \
  http://localhost:8083/connectors

# Check connector status
curl -s http://localhost:8083/connectors/crm-connector/status | jq .
```

### ClickHouse CDC Tables Empty

```bash
# 1. Check Kafka topics have data
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --from-beginning --max-messages 1

# 2. Verify KafkaEngine is consuming
curl "http://localhost:8123/" -d "SELECT * FROM system.kafka_consumers"

# 3. Check CDC tables
curl "http://localhost:8123/" -d "SELECT count() FROM reports.crm_customers"
```

### Airflow DAG Not Running

```bash
# Check DAG status
docker-compose exec airflow-webserver airflow dags list

# Check if DAG is paused
docker-compose exec airflow-webserver airflow dags unpause bionicpro_reports_etl

# Trigger manually
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl

# Check task logs
docker-compose logs airflow-scheduler
docker-compose exec airflow-webserver airflow tasks list bionicpro_reports_etl
```

### No Reports Displayed in Frontend

```bash
# 1. Check ClickHouse has data
curl "http://localhost:8123/" -d "SELECT count() FROM reports.user_prosthesis_stats"

# 2. If empty, regenerate demo data
docker-compose exec clickhouse clickhouse-client \
  --queries-file /docker-entrypoint-initdb.d/03_regenerate_demo_data.sql

# 3. Trigger ETL
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl

# 4. Check Reports Service logs
docker-compose logs reports-service | tail -50
```

### Container Memory Issues

```bash
# Check memory usage
docker stats --no-stream

# If containers are OOM killed, increase Docker memory limit
# Docker Desktop: Preferences > Resources > Memory (set to 8GB+)

# Or reduce memory by stopping unused services
docker-compose stop kafka-ui  # Optional monitoring service
```

### Clean Restart (Reset All Data)

```bash
# Stop all containers and remove data volumes
./scripts/clean.sh

# Or manually:
docker-compose down -v
rm -rf ./postgres-*-data ./clickhouse-data ./minio-data ./redis-data ./ldap-*
docker-compose up -d
```

### Viewing Detailed Logs

```bash
# All services
docker-compose logs -f

# Specific service with timestamps
docker-compose logs -f --timestamps reports-service

# Last 100 lines
docker-compose logs --tail=100 airflow-scheduler

# Save logs to file
docker-compose logs > logs.txt 2>&1
```

---

## Documentation (MkDocs)

Полная документация доступна в формате MkDocs Knowledge Base.

### Запуск локально

```bash
# Установка зависимостей
pip install -r docs/requirements.txt

# Запуск dev-сервера
mkdocs serve

# Открыть в браузере
open http://localhost:8000
```

### Сборка статического сайта

```bash
# Сборка в каталог site/
mkdocs build

# Сборка и деплой на GitHub Pages
mkdocs gh-deploy
```

### Структура документации

```
docs/
├── index.md                    # Главная страница
├── architecture/
│   ├── overview.md             # Обзор архитектуры
│   ├── security.md             # Task 1: Security
│   ├── reports-etl.md          # Task 2: Reports & ETL
│   ├── s3-cdn.md               # Task 3: S3/CDN
│   ├── cdc.md                  # Task 4: CDC
│   └── data-model.md           # Модель данных
├── deployment/
│   ├── quickstart.md           # Быстрый старт
│   ├── environment.md          # Настройка окружения
│   ├── services.md             # Справочник сервисов
│   └── troubleshooting.md      # Решение проблем
├── api/
│   ├── reports.md              # Reports API
│   ├── auth.md                 # Auth API (BFF)
│   └── cdc-health.md           # CDC Health API
└── diagrams/
    └── c4-diagrams.md          # C4 диаграммы
```

### Содержание документации

| Раздел | Описание |
|--------|----------|
| **Architecture** | Детальное описание архитектуры всех компонентов |
| **Deployment** | Инструкции по развёртыванию и настройке |
| **API Reference** | Документация REST API endpoints |
| **Diagrams** | C4 архитектурные диаграммы |