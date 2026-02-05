# ArchiMate Model (Archi)

## Описание

Полная модель архитектуры BionicPRO в формате ArchiMate, созданная для инструмента [Archi](https://www.archimatetool.com/).

## Файл модели

**Расположение**: `docs/architecture/bionicpro.archimate`

## Открытие модели

### Установка Archi

1. Скачайте Archi с https://www.archimatetool.com/download/
2. Установите для вашей ОС (Windows, macOS, Linux)

### Открытие файла

1. Запустите Archi
2. File → Open → выберите `bionicpro.archimate`

## Структура модели

### Слои ArchiMate

| Слой | Описание | Элементы |
|------|----------|----------|
| **Strategy** | Стратегические элементы | - |
| **Business** | Бизнес-акторы, процессы, сервисы | Пользователи, бизнес-процессы |
| **Application** | Приложения, компоненты, сервисы | Сервисы, API, функции |
| **Technology** | Инфраструктура, контейнеры | Docker containers, базы данных |
| **Motivation** | Цели, принципы, требования | Архитектурные решения |
| **Implementation** | Рабочие пакеты, deliverables | Tasks 1-4 |

### Представления (Views)

| # | Название | Описание |
|---|----------|----------|
| 1 | Business Layer | Бизнес-акторы и процессы |
| 2 | Application Layer | Приложения и их взаимодействие |
| 3 | Technology Layer - Deployment | Docker контейнеры |
| 4 | Motivation | Цели, принципы, требования |
| 5 | Implementation - Work Packages | Tasks 1-4 и deliverables |
| 6 | Data Flow - CDC Pipeline | Поток данных CDC |
| 7 | Security Architecture | Архитектура безопасности |

## Элементы модели

### Business Layer

#### Акторы (Business Actors)

| Элемент | Описание |
|---------|----------|
| Пользователь протеза | Владелец бионического протеза |
| Покупатель | Заказывает протезы |
| Оператор CRM | Управляет заказами |
| ML-инженер | Анализирует данные |
| Администратор | Управляет системой |

#### Бизнес-процессы

| Процесс | Описание |
|---------|----------|
| Просмотр отчётов | Пользователь просматривает данные о протезе |
| Аутентификация | Вход в систему |
| Управление заказами | Работа с CRM |
| Сбор телеметрии | Получение данных с протезов |
| Анализ данных | ML анализ телеметрии |

### Application Layer

#### Приложения (Application Components)

| Компонент | Технология | Порт |
|-----------|------------|------|
| Frontend SPA | React 18 | 3000 |
| BFF Auth Service | Flask | 8000 |
| Reports Service | FastAPI | 8001 |
| Keycloak | Keycloak 26.5 | 8080 |
| Apache Airflow | Airflow 2.8 | 8081 |
| Debezium Connect | Kafka Connect | 8083 |
| Nginx CDN | Nginx 1.25 | 8002 |

#### Application Services

| Сервис | Описание |
|--------|----------|
| Auth API | /auth/login, /auth/callback, /auth/logout |
| Reports API | /api/reports, /api/reports/cdn/* |
| OAuth2 OIDC | Authorization Code + PKCE |
| ETL Service | Периодический ETL (15 мин) |
| CDC Service | Real-time Change Data Capture |
| CDN Cache | HTTP кэширование |

#### Application Functions

| Функция | Описание |
|---------|----------|
| PKCE Generation | code_verifier, code_challenge (S256) |
| Token Encryption | Fernet шифрование в Redis |
| Report Generation | JSON из ClickHouse |
| Cache Invalidation | Очистка кэша после ETL |
| Data Transformation | JOIN в ETL |
| CDC Capture | Захват из WAL PostgreSQL |

### Technology Layer

#### Nodes (Docker Containers)

| Container | Port | Описание |
|-----------|------|----------|
| frontend-container | 3000 | React SPA |
| bff-auth-container | 8000 | BFF Auth |
| reports-service-container | 8001 | Reports API |
| keycloak-container | 8080 | Identity Provider |
| clickhouse-container | 8123, 9000 | OLAP Database |
| kafka-container | 9092 | Message Broker |
| debezium-container | 8083 | CDC Connector |
| minio-container | 9001, 9002 | S3 Storage |
| nginx-cdn-container | 8002 | CDN Proxy |
| redis-container | 6379 | Session Store |
| ldap-container | 389 | Directory |
| crm-db-container | 5435 | CRM PostgreSQL |
| telemetry-db-container | 5436 | Telemetry PostgreSQL |

#### System Software

| Software | Version |
|----------|---------|
| Docker Engine | - |
| Docker Compose | - |
| PostgreSQL | 14 |
| ClickHouse | 24.1 |
| Apache Kafka | 3.6 |
| Redis | 7 |
| OpenLDAP | 1.5 |
| MinIO | - |
| Nginx | 1.25 |

### Motivation Layer

#### Goals (Цели)

| Цель | Описание |
|------|----------|
| Безопасная аутентификация | MFA, BFF pattern |
| Отчётность в реальном времени | ETL + CDC |
| Разделение OLTP/OLAP | CDC pipeline |
| Снижение нагрузки на БД | Многоуровневое кэширование |

#### Principles (Принципы)

| Принцип | Описание |
|---------|----------|
| BFF Pattern | Токены на сервере, cookies на клиенте |
| OAuth2 PKCE | S256 challenge для защиты кода |
| CDC over ETL for CRM | Real-time репликация вместо batch |
| Multi-tier Caching | Redis → S3 → Nginx CDN |

#### Requirements (Требования)

| Требование | Описание |
|------------|----------|
| MFA обязательна | Двухфакторная аутентификация |
| Токены не на клиенте | HTTP-only cookies |
| ETL каждые 15 минут | Schedule: */15 * * * * |
| CDC latency < 1s | Real-time репликация |
| Cache TTL 5 min | Время жизни кэша CDN |

### Implementation Layer

#### Work Packages

| Task | Название | Deliverables |
|------|----------|--------------|
| Task 1 | Security Architecture | BFF Auth Service |
| Task 2 | Reports & ETL | Reports Service, ETL DAGs |
| Task 3 | S3/CDN Caching | CDN Configuration |
| Task 4 | CDC Pipeline | CDC Pipeline |

## Связи (Relations)

Модель содержит следующие типы связей:

- **Assignment** - назначение (актор → роль)
- **Triggering** - триггер (актор → процесс)
- **Realization** - реализация (процесс → сервис)
- **Serving** - обслуживание (компонент → актор)
- **Flow** - поток данных
- **Composition** - композиция (узел → подузел)
- **Access** - доступ к данным
- **Influence** - влияние (ограничение → технология)

## Экспорт

### В изображения

1. Откройте нужное View
2. File → Export → Export View As Image
3. Выберите формат (PNG, JPG, SVG, PDF)

### В HTML Report

1. File → Report → HTML Report
2. Выберите папку для сохранения
3. Получите интерактивный HTML отчёт

### В других форматах

Archi поддерживает экспорт в:
- CSV
- XML (Open Exchange Format)
- Jasper Reports

## Редактирование

### Добавление элементов

1. В Palette выберите тип элемента
2. Перетащите на View
3. Задайте имя и свойства

### Добавление связей

1. Выберите инструмент связи (Magic Connector или конкретный тип)
2. Соедините два элемента
3. Archi автоматически подберёт допустимый тип связи

### Создание нового View

1. File → New → View
2. Выберите тип (ArchiMate, Sketch, Canvas)
3. Перетащите элементы из Model Tree

## См. также

- [Architecture Overview](../architecture/overview.md)
- [C4 Diagrams](c4-level1.md)
- [Deployment Diagram](deployment.md)
