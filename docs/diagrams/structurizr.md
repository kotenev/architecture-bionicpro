# Structurizr DSL Model

## Описание

Полная архитектурная модель BionicPRO в формате "Architecture as Code" на основе [Structurizr DSL](https://docs.structurizr.com/dsl).

## Файл модели

**Расположение**: `docs/architecture/workspace.dsl`

## Преимущества Structurizr DSL

| Аспект | Описание |
|--------|----------|
| **Version Control** | Архитектура хранится в Git вместе с кодом |
| **Review Process** | Изменения проходят code review |
| **Автогенерация** | Диаграммы генерируются автоматически |
| **Консистентность** | Единый источник правды для всех диаграмм |
| **C4 Model** | Нативная поддержка C4 модели |

## Запуск Structurizr

### Вариант 1: Structurizr Lite (рекомендуется)

```bash
# Запуск в Docker
cd docs/architecture
docker run -it -p 8080:8080 \
  -v $(pwd):/usr/local/structurizr \
  structurizr/lite

# Открыть в браузере
open http://localhost:8080
```

### Вариант 2: Structurizr CLI

```bash
# Установка
brew install structurizr-cli

# Экспорт в PlantUML
structurizr-cli export \
  -workspace workspace.dsl \
  -format plantuml \
  -output ./plantuml

# Экспорт в Mermaid
structurizr-cli export \
  -workspace workspace.dsl \
  -format mermaid \
  -output ./mermaid

# Экспорт в JSON
structurizr-cli export \
  -workspace workspace.dsl \
  -format json \
  -output ./json
```

### Вариант 3: VS Code Extension

1. Установите расширение "Structurizr DSL" by Simon Brown
2. Откройте `workspace.dsl`
3. Используйте Preview (Ctrl+Shift+P → "Structurizr: Preview")

## Структура модели

### Actors (People)

```dsl
prostheticUser = person "Пользователь протеза" "..." "User"
buyer = person "Покупатель" "..." "User"
crmOperator = person "Оператор CRM" "..." "Operator"
mlEngineer = person "ML-инженер" "..." "Engineer"
administrator = person "Администратор" "..." "Admin"
```

### External Systems

```dsl
yandexId = softwareSystem "Яндекс ID" "..." "External"
googleIdp = softwareSystem "Google" "..." "External"
prosthesisDevice = softwareSystem "Бионический протез" "..." "External,IoT"
ldapRussia = softwareSystem "LDAP Россия" "..." "External,Directory"
ldapEurope = softwareSystem "LDAP Европа" "..." "External,Directory"
```

### Containers (Services)

| Container | Технология | Описание |
|-----------|------------|----------|
| `frontend` | React 18, TypeScript | SPA для пользователей |
| `bffAuth` | Python, Flask 3.0 | BFF Auth Service |
| `keycloak` | Keycloak 26.5.2 | Identity Provider |
| `ldap` | OpenLDAP 1.5.0 | Directory Service |
| `redis` | Redis 7 | Session Storage |
| `reportsService` | Python, FastAPI 0.109 | Reports API |
| `airflow` | Airflow 2.8.1 | ETL Orchestrator |
| `crmDb` | PostgreSQL 14 | CRM OLTP |
| `telemetryDb` | PostgreSQL 14 | Telemetry OLTP |
| `clickhouse` | ClickHouse 24.1 | OLAP Analytics |
| `kafka` | Confluent 7.5.0 | Message Broker |
| `zookeeper` | Zookeeper 3.8 | Kafka Coordinator |
| `debezium` | Debezium 2.4 | CDC Connector |
| `minio` | MinIO | S3 Storage |
| `nginxCdn` | Nginx 1.25 | CDN Proxy |

### Components

Модель содержит детализацию компонентов для:

- **BFF Auth Service** (8 компонентов)
- **Reports Service** (7 компонентов)
- **ClickHouse** (8 компонентов)
- **Kafka** (3 компонента)
- **CRM Database** (4 компонента)

## Views (Представления)

### System Context (Level 1)

```dsl
systemContext bionicpro "SystemContext" {
    include *
    autoLayout
}
```

Показывает:
- Акторы (пользователи системы)
- BionicPRO как единую систему
- Внешние системы (Yandex ID, LDAP, IoT)

### Container Diagram (Level 2)

```dsl
container bionicpro "Containers" {
    include *
    autoLayout
}
```

Показывает:
- Все контейнеры (сервисы)
- Связи между контейнерами
- Технологии

### Component Diagrams (Level 3)

```dsl
component bionicpro.bffAuth "BFF_Components" { ... }
component bionicpro.reportsService "Reports_Components" { ... }
component bionicpro.clickhouse "ClickHouse_Components" { ... }
```

### Deployment Diagram

```dsl
deployment bionicpro "Production" "Deployment" {
    include *
    autoLayout
}
```

Показывает:
- Docker Host
- Docker Network
- Контейнеры в Docker

### Dynamic Views (Сценарии)

| View | Описание |
|------|----------|
| `AuthFlow` | OAuth2 PKCE Authentication Flow |
| `CDCFlow` | CDC Data Flow (CRM → ClickHouse) |
| `ReportsFlow` | Reports with CDN Caching |
| `ETLFlow` | ETL Pipeline Flow |

## Пример: Auth Flow

```dsl
dynamic bionicpro "AuthFlow" "OAuth2 PKCE Authentication Flow" {
    prostheticUser -> bionicpro.frontend "1. Click Login"
    bionicpro.frontend -> bionicpro.bffAuth "2. GET /auth/login"
    bionicpro.bffAuth -> bionicpro.redis "3. Store PKCE verifier"
    bionicpro.bffAuth -> bionicpro.frontend "4. Redirect to Keycloak"
    bionicpro.frontend -> bionicpro.keycloak "5. Authorization Request"
    bionicpro.keycloak -> bionicpro.ldap "6. Validate credentials"
    bionicpro.keycloak -> bionicpro.frontend "7. Authorization code"
    bionicpro.frontend -> bionicpro.bffAuth "8. Callback with code"
    bionicpro.bffAuth -> bionicpro.keycloak "9. Exchange code + verifier"
    bionicpro.bffAuth -> bionicpro.redis "10. Store encrypted tokens"
    bionicpro.bffAuth -> bionicpro.frontend "11. Set session cookie"
    autoLayout
}
```

## Стили

```dsl
styles {
    element "Person" {
        background #08427b
        color #ffffff
        shape Person
    }
    element "Database" {
        shape Cylinder
    }
    element "Queue" {
        shape Pipe
    }
    element "Service" {
        shape Hexagon
    }
    element "Identity" {
        background #ff6600
        shape Hexagon
    }
}
```

## Экспорт диаграмм

### В PlantUML

```bash
structurizr-cli export -workspace workspace.dsl -format plantuml -output ./export
```

### В PNG/SVG

```bash
# Через PlantUML
java -jar plantuml.jar export/*.puml

# Через Structurizr Lite (в браузере)
# Menu → Export → PNG/SVG
```

### В Confluence/Notion

1. Экспортируйте в PNG через Structurizr Lite
2. Загрузите изображения в Confluence/Notion
3. Или используйте PlantUML plugin

## Расширение модели

### Добавление нового сервиса

```dsl
bionicpro = softwareSystem "BionicPRO Platform" {
    // Существующие контейнеры...

    // Новый сервис
    newService = container "New Service" "Описание" "Python, FastAPI" "Service" {
        component1 = component "Component1" "..." "..."
        component2 = component "Component2" "..." "..."
    }
}

// Связи
newService -> clickhouse "Запросы" "TCP:9000"
```

### Добавление нового сценария

```dsl
dynamic bionicpro "NewScenario" "Description" {
    actor -> container1 "Step 1"
    container1 -> container2 "Step 2"
    container2 -> container3 "Step 3"
    autoLayout
}
```

## CI/CD интеграция

### GitHub Actions

```yaml
name: Validate Architecture

on:
  push:
    paths:
      - 'docs/architecture/workspace.dsl'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Structurizr DSL
        run: |
          docker run --rm \
            -v $(pwd)/docs/architecture:/usr/local/structurizr \
            structurizr/cli \
            validate -workspace workspace.dsl

      - name: Export to PlantUML
        run: |
          docker run --rm \
            -v $(pwd)/docs/architecture:/usr/local/structurizr \
            structurizr/cli \
            export -workspace workspace.dsl -format plantuml
```

## Связь с другими форматами

| Формат | Файл | Описание |
|--------|------|----------|
| Structurizr DSL | `workspace.dsl` | Architecture as Code |
| ArchiMate | `bionicpro.archimate` | Enterprise Architecture |
| PlantUML | `diagrams/*.puml` | Диаграммы |
| Markdown | `docs/**/*.md` | Документация |

## См. также

- [Architecture Overview](../architecture/overview.md)
- [C4 Diagrams](c4-level1.md)
- [ArchiMate Model](archimate.md)
- [Structurizr Documentation](https://docs.structurizr.com/dsl)
