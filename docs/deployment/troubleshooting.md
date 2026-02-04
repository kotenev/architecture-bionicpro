# Troubleshooting

## Общие проблемы

### Переменные окружения не установлены

**Симптом**: Сервисы не запускаются, ошибки шифрования.

```bash
# Проверить наличие .env
ls -la .env

# Проверить загрузку переменных
docker-compose config | grep -E "AIRFLOW_FERNET_KEY|ENCRYPTION_KEY|JWT_SECRET_KEY"
```

**Решение**: Создайте `.env` файл согласно [Environment Setup](environment.md).

### Контейнеры не запускаются

**Симптом**: `docker-compose ps` показывает статус "Restarting" или "Exit".

```bash
# Посмотреть логи
docker-compose logs <service-name>

# Проверить использование ресурсов
docker stats --no-stream
```

**Решение**: Увеличьте память Docker (минимум 8GB).

## Keycloak

### Keycloak не запускается

```bash
# Проверить логи
docker-compose logs keycloak

# Типичные проблемы:
# 1. База данных не готова
docker-compose up -d keycloak_db
sleep 30
docker-compose up -d keycloak

# 2. Порт 8080 занят
lsof -i :8080
```

### Ошибка импорта realm

```bash
# Пересоздать Keycloak
docker-compose stop keycloak
docker-compose rm keycloak
rm -rf ./postgres-keycloak-data
docker-compose up -d keycloak_db keycloak
```

## Аутентификация

### Invalid token

**Симптом**: Ошибка 401 "Invalid token" или "Token validation failed".

```bash
# 1. Проверить Keycloak
curl -s http://localhost:8080/health/ready

# 2. Проверить BFF логи
docker-compose logs bionicpro-auth | grep -i error

# 3. Проверить realm
curl -s http://localhost:8080/realms/reports-realm/.well-known/openid-configuration | jq .

# 4. Очистить сессии
docker-compose exec redis redis-cli FLUSHALL
```

### LDAP authentication failed

```bash
# Проверить LDAP
ldapsearch -x -H ldap://localhost:389 \
  -D "cn=admin,dc=bionicpro,dc=com" \
  -w admin \
  -b "ou=People,dc=bionicpro,dc=com"

# Проверить User Federation в Keycloak
# http://localhost:8080/admin → reports-realm → User Federation → ldap
```

## CDC Pipeline

### Debezium не подключается

```bash
# Проверить логи Debezium
docker-compose logs debezium

# Проверить WAL level в PostgreSQL
docker-compose exec crm_db psql -U crm_user -d crm_db -c "SHOW wal_level;"
# Должно быть 'logical'

# Проверить replication slot
docker-compose exec crm_db psql -U crm_user -d crm_db \
  -c "SELECT * FROM pg_replication_slots;"
```

### Connector не регистрируется

```bash
# Перезапустить init
docker-compose restart debezium-init

# Ручная регистрация
curl -X POST -H "Content-Type: application/json" \
  --data @debezium/crm-connector.json \
  http://localhost:8083/connectors

# Проверить статус
curl -s http://localhost:8083/connectors/crm-connector/status | jq .
```

### Данные не появляются в ClickHouse

```bash
# 1. Проверить Kafka топики
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crm.crm.customers \
  --from-beginning --max-messages 1

# 2. Проверить KafkaEngine
curl "http://localhost:8123/" -d "SELECT * FROM system.kafka_consumers"

# 3. Проверить CDC таблицы
curl "http://localhost:8123/" -d "SELECT count() FROM reports.crm_customers"
```

## Airflow & ETL

### DAG не запускается

```bash
# Проверить статус DAG
docker-compose exec airflow-webserver airflow dags list

# Включить DAG
docker-compose exec airflow-webserver airflow dags unpause bionicpro_reports_etl

# Ручной запуск
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl

# Проверить логи
docker-compose logs airflow-scheduler
```

### Ошибки подключения к базам

```bash
# Проверить connections
docker-compose exec airflow-webserver airflow connections list

# Пересоздать connections
docker-compose restart airflow-connections
```

## Reports Service

### Нет отчётов во Frontend

```bash
# 1. Проверить данные в ClickHouse
curl "http://localhost:8123/" -d "SELECT count() FROM reports.user_prosthesis_stats"

# 2. Если пусто - регенерировать демо данные
docker-compose exec clickhouse clickhouse-client \
  --queries-file /docker-entrypoint-initdb.d/03_regenerate_demo_data.sql

# 3. Запустить ETL
docker-compose exec airflow-webserver airflow dags trigger bionicpro_reports_etl

# 4. Проверить логи Reports Service
docker-compose logs reports-service | tail -50
```

### S3/CDN не работает

```bash
# Проверить MinIO
curl -s http://localhost:9002/minio/health/live

# Проверить bucket
docker-compose exec minio mc ls local/reports-bucket

# Проверить CDN
curl -I http://localhost:8002/health
```

## Проблемы с памятью

### Out of Memory (OOM)

```bash
# Проверить память
docker stats --no-stream

# Увеличить память Docker Desktop:
# Preferences → Resources → Memory → 8GB+

# Или отключить необязательные сервисы
docker-compose stop kafka-ui
```

## Полная очистка

Если ничего не помогает — сброс к начальному состоянию:

```bash
# Остановить и удалить всё
./scripts/clean.sh

# Или вручную:
docker-compose down -v
rm -rf ./postgres-*-data ./clickhouse-data ./minio-data ./redis-data ./ldap-*

# Запустить заново
docker-compose up -d
```

## Сбор информации для отладки

```bash
# Сохранить все логи
docker-compose logs > logs.txt 2>&1

# Статус всех сервисов
docker-compose ps > status.txt

# Версии
docker version >> status.txt
docker-compose version >> status.txt

# Конфигурация
docker-compose config > config.txt 2>&1
```

## Полезные команды

```bash
# Войти в контейнер
docker-compose exec <service> /bin/bash

# Перезапустить все
docker-compose restart

# Пересобрать образы
docker-compose build --no-cache

# Удалить неиспользуемые образы
docker image prune -a
```

## См. также

- [Quick Start](quickstart.md)
- [Service Reference](services.md)
- [Environment Setup](environment.md)
