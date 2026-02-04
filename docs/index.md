# BionicPRO Architecture Documentation

BionicPRO — российская компания, производящая и продающая бионические протезы. Данная документация описывает архитектуру enterprise-решения для управления аутентификацией пользователей, сбора данных с протезов и формирования отчётов.

## Обзор системы

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYER                               │
│ LDAP (389) → Keycloak (8080) → BFF Auth (8000) → Redis          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│ Frontend React (3000) ← BFF → Reports Service FastAPI (8001)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                                 │
│ CRM PostgreSQL ─── Debezium CDC ─── Kafka ─── ClickHouse        │
│ Telemetry PostgreSQL ─── Airflow ETL (15min) ─── ClickHouse     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CDN & CACHING                                  │
│ Reports Service → MinIO S3 (9002) → Nginx CDN (8002)            │
└─────────────────────────────────────────────────────────────────┘
```

## Ключевые компоненты

| Задание | Название | Описание |
|---------|----------|----------|
| Task 1 | [Security Architecture](architecture/security.md) | LDAP + Keycloak OAuth2/PKCE + BFF pattern + MFA |
| Task 2 | [Reports & ETL](architecture/reports-etl.md) | Airflow ETL + ClickHouse OLAP + FastAPI Reports Service |
| Task 3 | [S3/CDN Caching](architecture/s3-cdn.md) | MinIO S3 + Nginx CDN для снижения нагрузки на БД |
| Task 4 | [CDC Pipeline](architecture/cdc.md) | Debezium + Kafka + ClickHouse KafkaEngine |

## Быстрый старт

```bash
# 1. Клонирование репозитория
git clone <repository-url>
cd architecture-bionicpro

# 2. Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env и установите значения ключей

# 3. Запуск всех сервисов
docker-compose up -d

# 4. Ожидание инициализации (2-3 минуты)
docker-compose logs -f airflow-etl-trigger

# 5. Доступ к приложению
open http://localhost:3000
```

Подробные инструкции: [Deployment Guide](deployment/quickstart.md)

## Тестовые пользователи

Все пароли: `password123`

| Username | Роль | Описание |
|----------|------|----------|
| ivan.petrov | prothetic_user | Пользователь протеза (РФ) |
| john.mueller | prothetic_user | Пользователь протеза (Европа) |
| maria.sidorova | user | Обычный пользователь |
| alexey.kozlov | administrator | Администратор системы |

## Технологический стек

### Backend
- **Python 3.11**: FastAPI 0.109, Flask 3.0, Apache Airflow 2.8.1
- **Databases**: PostgreSQL 14 (OLTP), ClickHouse 24.1 (OLAP)
- **Messaging**: Apache Kafka 3.6 (Confluent 7.5.0), Debezium CDC

### Frontend
- **React 18** с TypeScript
- **Tailwind CSS** для стилизации

### Infrastructure
- **Keycloak 26.5.2**: Identity Provider с LDAP Federation
- **OpenLDAP 1.5.0**: Directory Service
- **Redis 7**: Session Storage & Caching
- **MinIO**: S3-compatible Object Storage
- **Nginx 1.25**: CDN Proxy с кэшированием

## Навигация по документации

<div class="grid cards" markdown>

-   :material-shield-lock:{ .lg .middle } **Security Architecture**

    ---

    BFF pattern, OAuth2 PKCE, MFA, LDAP Federation

    [:octicons-arrow-right-24: Task 1](architecture/security.md)

-   :material-chart-bar:{ .lg .middle } **Reports & ETL**

    ---

    Airflow DAGs, ClickHouse OLAP, FastAPI

    [:octicons-arrow-right-24: Task 2](architecture/reports-etl.md)

-   :material-cloud:{ .lg .middle } **S3/CDN Caching**

    ---

    MinIO, Nginx CDN, Cache Invalidation

    [:octicons-arrow-right-24: Task 3](architecture/s3-cdn.md)

-   :material-database-sync:{ .lg .middle } **CDC Pipeline**

    ---

    Debezium, Kafka, KafkaEngine

    [:octicons-arrow-right-24: Task 4](architecture/cdc.md)

</div>
