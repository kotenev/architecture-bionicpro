# Environment Setup

## Переменные окружения

### Обязательные переменные

| Переменная | Описание | Генерация |
|------------|----------|-----------|
| `AIRFLOW_FERNET_KEY` | Шифрование данных в Airflow | Fernet key |
| `ENCRYPTION_KEY` | Шифрование токенов в Redis | Fernet key |
| `JWT_SECRET_KEY` | Подпись JWT токенов | Random string |

### Опциональные переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `YANDEX_CLIENT_ID` | ID приложения Яндекс | - |
| `YANDEX_CLIENT_SECRET` | Секрет приложения Яндекс | - |

## Генерация ключей

### Fernet Key (для AIRFLOW_FERNET_KEY и ENCRYPTION_KEY)

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Результат: 44 символа, base64-encoded, например:
```
Wv1Qp3R5t7Y9uBdEfGhJkLmNoP2sUwXz4a6C8i0qR1s=
```

### JWT Secret Key

```bash
# Вариант 1: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Вариант 2: OpenSSL
openssl rand -base64 32
```

Результат: 43 символа, например:
```
kL3mN5pQ7rS9tV1xZ3bD5fH7jL9nP1sU3wY5a7c9e1g
```

## Файл .env

### Минимальная конфигурация

```bash
# .env

# Airflow Fernet Key
AIRFLOW_FERNET_KEY=Wv1Qp3R5t7Y9uBdEfGhJkLmNoP2sUwXz4a6C8i0qR1s=

# BFF Encryption Key
ENCRYPTION_KEY=kL3mN5pQ7rS9tV1xZ3bD5fH7jL9nP1sU3wY5a7c9e1g=

# JWT Secret Key
JWT_SECRET_KEY=your-secure-jwt-secret-key-here-32chars
```

### Полная конфигурация

```bash
# .env

# ============================================================================
# REQUIRED
# ============================================================================

AIRFLOW_FERNET_KEY=Wv1Qp3R5t7Y9uBdEfGhJkLmNoP2sUwXz4a6C8i0qR1s=
ENCRYPTION_KEY=kL3mN5pQ7rS9tV1xZ3bD5fH7jL9nP1sU3wY5a7c9e1g=
JWT_SECRET_KEY=your-secure-jwt-secret-key-here-32chars

# ============================================================================
# OPTIONAL - Yandex ID Integration
# ============================================================================

# Register at https://oauth.yandex.ru/
# Callback URL: http://localhost:8080/realms/reports-realm/broker/yandex/endpoint
YANDEX_CLIENT_ID=your-yandex-client-id
YANDEX_CLIENT_SECRET=your-yandex-client-secret
```

## Настройка Yandex ID

### Шаг 1: Регистрация приложения

1. Перейдите на https://oauth.yandex.ru/
2. Нажмите "Зарегистрировать новое приложение"
3. Заполните форму:
   - Название: BionicPRO
   - Платформы: Веб-сервисы
   - Callback URL: `http://localhost:8080/realms/reports-realm/broker/yandex/endpoint`

### Шаг 2: Права доступа

Выберите права:
- `login:info` — базовая информация
- `login:email` — email пользователя

### Шаг 3: Получение credentials

После создания приложения:
- ClientID → `YANDEX_CLIENT_ID`
- Client secret → `YANDEX_CLIENT_SECRET`

## Проверка конфигурации

```bash
# Проверить наличие .env файла
ls -la .env

# Проверить загрузку переменных Docker Compose
docker-compose config | grep -E "AIRFLOW_FERNET_KEY|ENCRYPTION_KEY|JWT_SECRET_KEY"
```

## Безопасность

!!! danger "Важно"
    - **Никогда** не коммитьте `.env` в репозиторий
    - Используйте разные ключи для разных сред (dev/staging/prod)
    - Периодически ротируйте ключи в production

### Проверка .gitignore

```bash
# .env должен быть в .gitignore
grep ".env" .gitignore
```

### Production рекомендации

Для production используйте:

- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager

Пример с Docker Secrets:

```yaml
# docker-compose.prod.yaml
services:
  airflow-webserver:
    secrets:
      - airflow_fernet_key
    environment:
      AIRFLOW__CORE__FERNET_KEY_FILE: /run/secrets/airflow_fernet_key

secrets:
  airflow_fernet_key:
    external: true
```

## Переопределение настроек

### Для разработки

```bash
# Включить debug mode
export DEBUG=true
docker-compose up -d
```

### Для тестирования

```bash
# Использовать отдельный .env файл
docker-compose --env-file .env.test up -d
```

## См. также

- [Quick Start](quickstart.md)
- [Service Reference](services.md)
- [Security Architecture](../architecture/security.md)
