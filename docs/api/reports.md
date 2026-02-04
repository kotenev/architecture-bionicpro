# Reports API

## Обзор

Reports Service предоставляет REST API для получения отчётов о работе протезов.

**Base URL**: `http://localhost:8001`

## Аутентификация

Все endpoints (кроме health) требуют JWT токен в заголовке:

```http
Authorization: Bearer <access_token>
```

Токен автоматически передаётся через BFF при использовании Frontend.

## Endpoints

### Health Check

#### GET /health

Проверка работоспособности сервиса.

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8001
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### GET /health/live

Liveness probe для Kubernetes.

**Response** `200 OK`:
```json
{
  "status": "live"
}
```

#### GET /health/cdc

Проверка CDC pipeline.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "cdc_tables": {
    "crm_customers": {"rows": 5, "last_update": "2024-01-15T10:30:00Z"},
    "crm_prostheses": {"rows": 5},
    "crm_prosthesis_models": {"rows": 5}
  },
  "kafka_lag": {
    "crm.crm.customers": 0
  }
}
```

### Reports

#### GET /api/reports

Список доступных отчётов пользователя.

**Request**:
```http
GET /api/reports HTTP/1.1
Host: localhost:8001
Authorization: Bearer <token>
```

**Response** `200 OK`:
```json
{
  "reports": [
    {"date": "2024-01-15"},
    {"date": "2024-01-14"},
    {"date": "2024-01-13"}
  ],
  "total": 3,
  "user": "ivan.petrov"
}
```

#### GET /api/reports/summary

Сводная статистика пользователя.

**Request**:
```http
GET /api/reports/summary HTTP/1.1
Host: localhost:8001
Authorization: Bearer <token>
```

**Response** `200 OK`:
```json
{
  "user": "ivan.petrov",
  "prosthesis_model": "BionicHand Pro X1",
  "total_days": 30,
  "summary": {
    "total_movements": 45230,
    "avg_response_time_ms": 44.5,
    "avg_battery_level": 75.2,
    "total_errors": 12,
    "avg_daily_usage_hours": 12.5
  }
}
```

#### GET /api/reports/{date}

Детальный отчёт за конкретную дату.

**Parameters**:
- `date` (path) - дата в формате YYYY-MM-DD

**Request**:
```http
GET /api/reports/2024-01-15 HTTP/1.1
Host: localhost:8001
Authorization: Bearer <token>
```

**Response** `200 OK`:
```json
{
  "date": "2024-01-15",
  "user": "ivan.petrov",
  "prosthesis_model": "BionicHand Pro X1",
  "chip_id": "CHIP-001-2024",
  "summary": {
    "total_movements": 1523,
    "avg_response_time_ms": 45.2,
    "avg_battery_level": 78.5,
    "total_errors": 3,
    "uptime_hours": 14
  },
  "hourly_data": [
    {
      "hour": "2024-01-15T08:00:00Z",
      "movements_count": 145,
      "avg_response_time": 42.1,
      "battery_level": 95.0,
      "error_count": 0
    },
    {
      "hour": "2024-01-15T09:00:00Z",
      "movements_count": 189,
      "avg_response_time": 44.3,
      "battery_level": 92.0,
      "error_count": 1
    }
  ]
}
```

**Response** `404 Not Found`:
```json
{
  "detail": "Report not found for date 2024-01-15"
}
```

### CDN Endpoints

#### GET /api/reports/cdn/list

Получить CDN URL для списка отчётов.

**Request**:
```http
GET /api/reports/cdn/list HTTP/1.1
Host: localhost:8001
Authorization: Bearer <token>
```

**Response** `200 OK`:
```json
{
  "cdn_url": "http://localhost:8002/reports/550e8400.../list/reports.json",
  "expires_in": 300
}
```

#### GET /api/reports/cdn/summary

Получить CDN URL для сводки.

**Response** `200 OK`:
```json
{
  "cdn_url": "http://localhost:8002/reports/550e8400.../summary/summary.json"
}
```

#### GET /api/reports/cdn/{date}

Получить CDN URL для отчёта за дату.

**Parameters**:
- `date` (path) - дата в формате YYYY-MM-DD

**Response** `200 OK`:
```json
{
  "cdn_url": "http://localhost:8002/reports/550e8400.../daily/2024-01-15/report.json",
  "date": "2024-01-15"
}
```

### Cache Management

#### POST /api/reports/invalidate

Инвалидация кэша (только для администраторов).

**Request**:
```http
POST /api/reports/invalidate HTTP/1.1
Host: localhost:8001
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** `200 OK`:
```json
{
  "status": "invalidated",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "cleared": {
    "s3_objects": 5,
    "redis_keys": 3
  }
}
```

## Коды ответов

| Code | Описание |
|------|----------|
| 200 | Успешный запрос |
| 401 | Не авторизован (отсутствует или невалидный токен) |
| 403 | Доступ запрещён (нет прав) |
| 404 | Отчёт не найден |
| 500 | Внутренняя ошибка сервера |

## Примеры использования

### cURL

```bash
# Получить токен через BFF (cookie-based)
# Используйте браузер для аутентификации

# Прямой запрос с токеном
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/reports

# Получить отчёт за дату
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/reports/2024-01-15
```

### Python

```python
import requests

BASE_URL = "http://localhost:8001"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Список отчётов
response = requests.get(f"{BASE_URL}/api/reports", headers=headers)
reports = response.json()

# Детальный отчёт
date = reports["reports"][0]["date"]
response = requests.get(f"{BASE_URL}/api/reports/{date}", headers=headers)
report = response.json()
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8001';
const token = 'your-jwt-token';

// Список отчётов
const response = await fetch(`${BASE_URL}/api/reports`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const reports = await response.json();

// Использование CDN URL
const cdnResponse = await fetch(`${BASE_URL}/api/reports/cdn/list`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { cdn_url } = await cdnResponse.json();

// Загрузка отчёта через CDN
const reportData = await fetch(cdn_url).then(r => r.json());
```

## OpenAPI Specification

Полная спецификация доступна по адресу:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- OpenAPI JSON: http://localhost:8001/openapi.json

## См. также

- [Architecture: Reports & ETL](../architecture/reports-etl.md)
- [Architecture: S3/CDN](../architecture/s3-cdn.md)
- [Auth API](auth.md)
