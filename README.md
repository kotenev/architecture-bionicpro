# BionicPRO Architecture Project

## Overview

BionicPRO is a Russian company that produces and sells bionic prosthetics. This project implements a comprehensive architecture solution for managing user authentication, data collection from prosthetic devices, and generating reports. The system addresses security vulnerabilities discovered after a previous breach and implements enhanced data privacy controls.

## Security Configuration

### Environment Variables Setup

Before running the application, you need to set up the environment variables:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to add your actual values:
   ```bash
   # Generate a new Fernet key for Airflow
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Update the `.env` file with your generated key and other credentials.

### Important Security Notes

- The `AIRFLOW__CORE__FERNET_KEY` is used to encrypt sensitive data in Airflow, such as connection passwords.
- Never commit the `.env` file to the repository. It's already included in `.gitignore`.
- For production deployments, use a secrets management system (HashiCorp Vault, AWS Secrets Manager, etc.).

## Running the Application

### Prerequisites
- Docker and Docker Compose
- Python 3.8+

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd architecture-bionicpro
   ```

2. Set up environment variables (see above)

3. Build and start the services:
   ```bash
   docker-compose up -d
   ```

4. **Wait for initial setup** (~2-3 minutes):
   - All services will initialize automatically
   - ETL pipeline will run automatically to populate demo reports
   - Check progress: `docker-compose logs -f airflow-etl-trigger`

5. Access the services:
   - **Frontend**: http://localhost:3000 (Login with test users to see reports)
   - Keycloak Admin: http://localhost:8080 (admin/admin)
   - Airflow UI: http://localhost:8081 (admin/admin)
   - Reports API: http://localhost:8001/health
   - ClickHouse HTTP: http://localhost:8123

6. **Test Users** (for frontend login):
   - Username: `ivan.petrov` | Password: `password123` (has prosthesis reports)
   - Username: `john.mueller` | Password: `password123` (has prosthesis reports)
   - Username: `alexey.kozlov` | Password: `password123` (administrator)

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

To deploy all components at once:

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your values

# 2. Start all services
docker-compose up -d

# 3. Wait for initialization (2-3 minutes)
sleep 180

# 4. Verify all services
docker-compose ps

# 5. Run initial ETL
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl
```

## Service Ports Summary

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React application |
| bionicpro-auth | 8000 | BFF authentication service |
| Reports Service | 8001 | Reports REST API |
| Nginx CDN | 8002 | CDN reverse proxy |
| Keycloak | 8080 | Identity management |
| Airflow | 8081 | ETL orchestration |
| Debezium | 8083 | CDC connector |
| Kafka UI | 8084 | Kafka monitoring |
| ClickHouse HTTP | 8123 | OLAP database |
| MinIO Console | 9001 | S3 storage UI |
| MinIO S3 API | 9002 | S3 API endpoint |
| Kafka | 9092 | Message broker |
| LDAP | 389 | Directory service |

## Troubleshooting

### Keycloak not starting
```bash
# Check logs
docker-compose logs keycloak

# Ensure keycloak-db is running
docker-compose up -d keycloak-db
sleep 30
docker-compose up -d keycloak
```

### Debezium connector not registering
```bash
# Re-run initialization
docker-compose restart debezium-init

# Manual registration
curl -X POST -H "Content-Type: application/json" \
  --data @debezium/crm-connector.json \
  http://localhost:8083/connectors
```

### ClickHouse CDC tables empty
```bash
# Check Kafka topics have data
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --from-beginning --max-messages 1

# Verify KafkaEngine is consuming
curl "http://localhost:8123/" -d "SELECT * FROM system.kafka_consumers"
```

### Airflow DAG not running
```bash
# Check DAG status
docker-compose exec airflow-webserver airflow dags list

# Trigger manually
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl

# Check task logs
docker-compose logs airflow-scheduler
```