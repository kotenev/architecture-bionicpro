# 2. CDC вместо ETL для CRM данных

Date: 2024-01-15

## Status

Accepted

## Context

ETL pipeline каждые 15 минут создаёт значительную нагрузку на CRM базу данных (тяжёлые SELECT запросы).

## Decision

Использовать Change Data Capture (CDC) через Debezium:
- Debezium читает WAL PostgreSQL
- События публикуются в Kafka
- ClickHouse потребляет через KafkaEngine

## Consequences

**Положительные:**
- Минимальная нагрузка на OLTP базу
- Данные в OLAP обновляются за секунды (< 1s latency)
- Независимость отчётов от доступности CRM

**Отрицательные:**
- Дополнительные компоненты (Kafka, Debezium)
- Сложность отладки CDC pipeline
