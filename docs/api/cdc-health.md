# CDC Health API

## Обзор

API для мониторинга состояния CDC pipeline (Debezium → Kafka → ClickHouse).

## Endpoints

### GET /health/cdc

Комплексная проверка CDC pipeline.

**Base URL**: `http://localhost:8001`

**Request**:
```http
GET /health/cdc HTTP/1.1
Host: localhost:8001
```

**Response** `200 OK` (healthy):
```json
{
  "status": "healthy",
  "cdc_tables": {
    "crm_customers": {
      "rows": 5,
      "last_update": "2024-01-15T10:30:00Z"
    },
    "crm_prostheses": {
      "rows": 5,
      "last_update": "2024-01-15T10:30:00Z"
    },
    "crm_prosthesis_models": {
      "rows": 5,
      "last_update": "2024-01-15T10:30:00Z"
    }
  },
  "kafka_lag": {
    "crm.crm.customers": 0,
    "crm.crm.prostheses": 0,
    "crm.crm.prosthesis_models": 0
  },
  "debezium": {
    "status": "RUNNING",
    "connector": "crm-connector",
    "tasks": 1
  }
}
```

**Response** `503 Service Unavailable` (degraded):
```json
{
  "status": "degraded",
  "cdc_tables": {
    "crm_customers": {
      "rows": 5,
      "last_update": "2024-01-15T08:00:00Z"
    }
  },
  "kafka_lag": {
    "crm.crm.customers": 1500
  },
  "debezium": {
    "status": "FAILED",
    "connector": "crm-connector",
    "error": "Connection refused"
  },
  "issues": [
    "High Kafka lag detected (>1000)",
    "Debezium connector not running"
  ]
}
```

## Debezium REST API

### Base URL

`http://localhost:8083`

### List Connectors

```http
GET /connectors HTTP/1.1
Host: localhost:8083
```

**Response**:
```json
["crm-connector"]
```

### Connector Status

```http
GET /connectors/crm-connector/status HTTP/1.1
Host: localhost:8083
```

**Response**:
```json
{
  "name": "crm-connector",
  "connector": {
    "state": "RUNNING",
    "worker_id": "debezium:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "debezium:8083"
    }
  ],
  "type": "source"
}
```

### Pause Connector

```http
PUT /connectors/crm-connector/pause HTTP/1.1
Host: localhost:8083
```

### Resume Connector

```http
PUT /connectors/crm-connector/resume HTTP/1.1
Host: localhost:8083
```

### Restart Connector

```http
POST /connectors/crm-connector/restart HTTP/1.1
Host: localhost:8083
```

### Delete Connector

```http
DELETE /connectors/crm-connector HTTP/1.1
Host: localhost:8083
```

### Create/Update Connector

```http
POST /connectors HTTP/1.1
Host: localhost:8083
Content-Type: application/json

{
  "name": "crm-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "crm_db",
    "database.port": "5432",
    "database.user": "debezium_user",
    "database.password": "debezium_password",
    "database.dbname": "crm_db",
    "database.server.name": "crm",
    "schema.include.list": "crm",
    "table.include.list": "crm.customers,crm.prostheses,crm.prosthesis_models",
    "plugin.name": "pgoutput",
    "topic.prefix": "crm"
  }
}
```

## ClickHouse CDC Queries

### Check CDC Tables

```bash
# Row counts
curl "http://localhost:8123/" -d "
SELECT
    'crm_customers' as table,
    count() as rows
FROM reports.crm_customers FINAL
WHERE _deleted = 0
UNION ALL
SELECT
    'crm_prostheses',
    count()
FROM reports.crm_prostheses FINAL
WHERE _deleted = 0
UNION ALL
SELECT
    'crm_prosthesis_models',
    count()
FROM reports.crm_prosthesis_models FINAL
WHERE _deleted = 0
"
```

### Check Kafka Consumers

```bash
curl "http://localhost:8123/" -d "
SELECT
    database,
    table,
    name as consumer,
    last_poll_time,
    num_messages_read,
    last_commit_time
FROM system.kafka_consumers
"
```

### Check Recent Updates

```bash
curl "http://localhost:8123/" -d "
SELECT
    id,
    name,
    ldap_username,
    updated_at,
    _version
FROM reports.crm_customers FINAL
ORDER BY _version DESC
LIMIT 10
"
```

## Kafka CLI Commands

### List Topics

```bash
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

### Describe Topic

```bash
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic crm.crm.customers
```

### Consumer Lag

```bash
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group clickhouse_customers
```

### Read Messages

```bash
# First message
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --from-beginning \
  --max-messages 1

# Latest messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --max-messages 5
```

## Monitoring Dashboard

### Kafka UI

- URL: http://localhost:8084
- Features:
  - Topic list and messages
  - Consumer groups
  - Connector status

### Health Check Script

```bash
#!/bin/bash
# scripts/check-cdc.sh

echo "=== CDC Health Check ==="

echo -e "\n1. Debezium Connector Status:"
curl -s http://localhost:8083/connectors/crm-connector/status | jq .

echo -e "\n2. Kafka Topics:"
docker-compose exec -T kafka kafka-topics \
  --bootstrap-server localhost:9092 --list 2>/dev/null | grep crm

echo -e "\n3. ClickHouse CDC Tables:"
curl -s "http://localhost:8123/" -d "
SELECT 'customers' as t, count() as c FROM reports.crm_customers FINAL WHERE _deleted=0
UNION ALL SELECT 'prostheses', count() FROM reports.crm_prostheses FINAL WHERE _deleted=0
UNION ALL SELECT 'models', count() FROM reports.crm_prosthesis_models FINAL WHERE _deleted=0
FORMAT Pretty
"

echo -e "\n4. Reports Service CDC Health:"
curl -s http://localhost:8001/health/cdc | jq .
```

## Troubleshooting

### Debezium не запускается

```bash
# Проверить логи
docker-compose logs debezium

# Проверить подключение к PostgreSQL
docker-compose exec debezium curl -s http://localhost:8083/connectors/crm-connector/status
```

### Высокий Kafka lag

```bash
# Проверить consumer groups
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --all-groups

# Перезапустить ClickHouse consumers
# (пересоздать KafkaEngine таблицы)
```

### Данные не появляются

```bash
# 1. Проверить Kafka
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --from-beginning --max-messages 1

# 2. Проверить ClickHouse
curl "http://localhost:8123/" -d "SELECT * FROM system.kafka_consumers"

# 3. Проверить materialized views
curl "http://localhost:8123/" -d "
SELECT
    name,
    total_rows,
    bytes_on_disk
FROM system.tables
WHERE database = 'reports' AND engine LIKE '%View%'
"
```

## См. также

- [Architecture: CDC Pipeline](../architecture/cdc.md)
- [Reports API](reports.md)
- [Troubleshooting](../deployment/troubleshooting.md)
