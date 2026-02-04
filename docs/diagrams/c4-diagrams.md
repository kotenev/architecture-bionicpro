# C4 Architecture Diagrams

## Обзор

Архитектура BionicPRO документирована с использованием нотации C4 (Context, Container, Component, Code).

Все диаграммы находятся в каталоге `/diagrams/` и созданы в формате PlantUML.

## Диаграммы

### Task 1: Security Architecture

**Файл**: `(TO-BE) BionicPRO_C4_container_Security_Architecture_Task1.puml`

Описывает архитектуру безопасности:

- BFF Pattern (Backend-for-Frontend)
- OAuth2 PKCE Flow
- Keycloak как Identity Broker
- LDAP User Federation
- Identity Brokering с внешними IdP

```
┌────────────────────────────────────────────────────────────┐
│                    EXTERNAL USERS                           │
│  Пользователь протеза, Покупатель, Оператор, ML-инженер    │
└────────────────────────────────────────────────────────────┘
                              │
┌────────────────────────────────────────────────────────────┐
│                   EXTERNAL IDPs                             │
│         LDAP Russia, LDAP Europe, Яндекс ID                │
└────────────────────────────────────────────────────────────┘
                              │
┌────────────────────────────────────────────────────────────┐
│                   BIONICPRO SECURITY                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ Mobile App  │  │  Keycloak   │  │  bionicpro-auth │    │
│  │   / Web     │──│   (IdP)     │──│     (BFF)       │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
│                                           │                │
│                                    ┌──────┴──────┐        │
│                                    │   Redis     │        │
│                                    │  (Sessions) │        │
│                                    └─────────────┘        │
└────────────────────────────────────────────────────────────┘
```

**Ключевые решения**:

- Токены не передаются на клиент
- HTTP-only, Secure cookies
- Автоматическое обновление токенов
- MFA/TOTP обязателен

---

### Task 2: Reports & ETL Architecture

**Файл**: `(TO-BE) BionicPRO_C4_container_Reports_and_ETL_Architecture_Task2.puml`

Описывает ETL pipeline и Reports Service:

- Apache Airflow как оркестратор
- ClickHouse как OLAP хранилище
- FastAPI Reports Service
- Витрина user_prosthesis_stats

```
┌─────────────────────────────────────────────────────────────┐
│                      ETL PIPELINE                            │
│                                                              │
│   ┌──────────┐     ┌──────────────┐     ┌─────────────┐    │
│   │ CRM DB   │────▶│   Airflow    │────▶│ ClickHouse  │    │
│   │(PostgreSQL)    │   (ETL)      │     │  (OLAP)     │    │
│   └──────────┘     └──────────────┘     └─────────────┘    │
│                           │                    ▲            │
│   ┌──────────┐           │                    │            │
│   │Telemetry │───────────┘                    │            │
│   │   DB     │                                │            │
│   └──────────┘                                │            │
│                                               │            │
│                                    ┌──────────┴───────┐    │
│                                    │ Reports Service  │    │
│                                    │   (FastAPI)      │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**ETL Schedule**: каждые 15 минут

**Data Flow**:
1. Extract: CRM (клиенты, протезы) + Telemetry (агрегаты)
2. Transform: JOIN по chip_id, расчёт метрик
3. Load: ClickHouse `reports.user_prosthesis_stats`

---

### Task 3: S3/CDN Caching Architecture

**Файл**: `(TO-BE) BionicPRO_C4_container_S3_CDN_Architecture_Task3.puml`

Описывает многоуровневое кэширование:

- MinIO как S3 хранилище
- Nginx как CDN proxy
- Redis для метаданных
- Cache invalidation flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHING ARCHITECTURE                      │
│                                                              │
│   ┌──────────┐                                              │
│   │  User    │                                              │
│   └────┬─────┘                                              │
│        │                                                     │
│        ▼                                                     │
│   ┌──────────┐     ┌──────────────┐     ┌─────────────┐    │
│   │ Frontend │────▶│   Reports    │────▶│ ClickHouse  │    │
│   └──────────┘     │   Service    │     └─────────────┘    │
│        │           └──────┬───────┘                         │
│        │                  │                                  │
│        │                  ▼                                  │
│        │           ┌──────────────┐                         │
│        │           │   MinIO S3   │                         │
│        │           └──────┬───────┘                         │
│        │                  │                                  │
│        ▼                  ▼                                  │
│   ┌──────────────────────────────┐                         │
│   │         Nginx CDN            │                         │
│   │    (proxy_cache 5min)        │                         │
│   └──────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

**Cache Flow**:
1. Reports Service проверяет S3
2. Cache HIT → возвращает CDN URL
3. Cache MISS → генерирует, сохраняет в S3, возвращает CDN URL
4. Frontend получает данные через CDN

---

### Task 4: CDC Architecture

**Файл**: `(TO-BE) BionicPRO_C4_container_CDC_Architecture_Task4.puml`

Описывает Change Data Capture pipeline:

- Debezium PostgreSQL Connector
- Kafka как шина событий
- ClickHouse KafkaEngine
- Hybrid architecture (CDC + ETL)

```
┌─────────────────────────────────────────────────────────────┐
│                      CDC PIPELINE                            │
│                                                              │
│   ┌──────────┐     ┌──────────────┐     ┌─────────────┐    │
│   │  CRM DB  │────▶│  Debezium    │────▶│   Kafka     │    │
│   │(wal=log) │     │ (CDC Connect)│     │  (Topics)   │    │
│   └──────────┘     └──────────────┘     └──────┬──────┘    │
│                                                 │           │
│                                                 ▼           │
│                                         ┌──────────────┐   │
│                                         │  ClickHouse  │   │
│                                         │ (KafkaEngine)│   │
│                                         └──────┬───────┘   │
│                                                │           │
│                                                ▼           │
│                                         ┌──────────────┐   │
│                                         │MaterializedView│  │
│                                         │   + Target   │   │
│                                         └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow**:
1. CRM PostgreSQL → WAL (logical replication)
2. Debezium читает WAL, публикует в Kafka
3. ClickHouse KafkaEngine потребляет события
4. MaterializedView трансформирует в target tables
5. Reports читают из ClickHouse (не из CRM)

---

## Просмотр диаграмм

### PlantUML Online

1. Откройте http://www.plantuml.com/plantuml/uml/
2. Вставьте содержимое `.puml` файла
3. Нажмите "Submit"

### VS Code Extension

1. Установите расширение "PlantUML"
2. Откройте `.puml` файл
3. `Cmd/Ctrl + Shift + P` → "PlantUML: Preview Current Diagram"

### CLI

```bash
# Установка PlantUML
brew install plantuml

# Генерация PNG
plantuml diagrams/*.puml

# Генерация SVG
plantuml -tsvg diagrams/*.puml
```

### Docker

```bash
docker run -v $(pwd)/diagrams:/data plantuml/plantuml *.puml
```

## Генерация в MkDocs

Для автоматического рендеринга в MkDocs можно использовать плагин `plantuml-markdown`:

```yaml
# mkdocs.yml
plugins:
  - plantuml:
      server: http://www.plantuml.com/plantuml
```

## Файловая структура

```
diagrams/
├── (TO-BE) BionicPRO_C4_container_Security_Architecture_Task1.puml
├── (TO-BE) BionicPRO_C4_container_Security_Architecture_Task1.drawio.xml
├── (TO-BE) BionicPRO_C4_container_Reports_and_ETL_Architecture_Task2.puml
├── (TO-BE) BionicPRO_C4_container_S3_CDN_Architecture_Task3.puml
└── (TO-BE) BionicPRO_C4_container_CDC_Architecture_Task4.puml
```

## См. также

- [Architecture Overview](../architecture/overview.md)
- [Security Architecture](../architecture/security.md)
- [Reports & ETL](../architecture/reports-etl.md)
- [S3/CDN Caching](../architecture/s3-cdn.md)
- [CDC Pipeline](../architecture/cdc.md)
