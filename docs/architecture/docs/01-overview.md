# Обзор системы BionicPRO

## Назначение

BionicPRO — платформа для управления бионическими протезами:

- Сбор телеметрии с IoT устройств
- Формирование отчётов для пользователей
- Управление заказами через CRM
- Безопасная аутентификация с MFA

## Ключевые возможности

| Задача | Компоненты |
|--------|------------|
| Task 1: Security | LDAP, Keycloak, BFF Auth |
| Task 2: Reports & ETL | Airflow, ClickHouse, FastAPI |
| Task 3: S3/CDN | MinIO, Nginx |
| Task 4: CDC | Debezium, Kafka |

## Архитектурные принципы

1. **OLTP/OLAP разделение** — PostgreSQL для транзакций, ClickHouse для аналитики
2. **BFF Pattern** — серверное хранение токенов
3. **CDC** — real-time репликация данных
4. **Multi-tier Caching** — Redis → S3 → CDN
