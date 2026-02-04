# Quick Start Guide

## Обзор

Это руководство поможет запустить BionicPRO за несколько минут.

## Требования

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM минимум (16GB рекомендуется)
- 20GB свободного места на диске
- Python 3.8+ (только для генерации ключей)

## Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd architecture-bionicpro
```

## Шаг 2: Настройка переменных окружения

### Создание файла .env

```bash
cp .env.example .env
```

### Генерация ключей

Система требует три секретных ключа:

```bash
# 1. Airflow Fernet Key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. BFF Encryption Key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. JWT Secret Key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Заполнение .env

```bash
# Required
AIRFLOW_FERNET_KEY=<ваш-ключ-1>
ENCRYPTION_KEY=<ваш-ключ-2>
JWT_SECRET_KEY=<ваш-ключ-3>

# Optional (для Yandex ID)
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
```

## Шаг 3: Запуск системы

```bash
# Запуск всех сервисов
docker-compose up -d

# Мониторинг инициализации
docker-compose logs -f airflow-etl-trigger
```

Дождитесь сообщения "ETL completed successfully" (2-3 минуты).

## Шаг 4: Проверка работоспособности

```bash
# Все сервисы должны быть в статусе "Up"
docker-compose ps

# Health checks
curl -s http://localhost:8080/health/ready  # Keycloak
curl -s http://localhost:8001/health/live   # Reports Service
curl -s http://localhost:8123/?query=SELECT%201  # ClickHouse
```

## Шаг 5: Доступ к приложению

### Frontend

Откройте http://localhost:3000 и войдите:

| Username | Password | Роль |
|----------|----------|------|
| ivan.petrov | password123 | Пользователь протеза |
| john.mueller | password123 | Пользователь протеза |
| alexey.kozlov | password123 | Администратор |

### Admin Interfaces

| Сервис | URL | Credentials |
|--------|-----|-------------|
| Keycloak Admin | http://localhost:8080/admin | admin / admin |
| Airflow UI | http://localhost:8081 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| Kafka UI | http://localhost:8084 | - |

## Остановка системы

```bash
# Остановка с сохранением данных
docker-compose down

# Полная очистка (удаление всех данных)
./scripts/clean.sh
```

## Что дальше?

- [Environment Setup](environment.md) — детальная настройка
- [Service Reference](services.md) — описание всех сервисов
- [Architecture Overview](../architecture/overview.md) — архитектура системы
- [Troubleshooting](troubleshooting.md) — решение проблем
