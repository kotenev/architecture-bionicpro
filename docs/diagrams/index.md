# Architecture Diagrams

## Обзор

Архитектура BionicPRO документирована с использованием нотации C4 Model и дополнительных диаграмм.

## C4 Model Levels

| Level | Название | Описание |
|-------|----------|----------|
| **Level 1** | [Context](c4-level1.md) | Система в контексте пользователей и внешних систем |
| **Level 2** | [Container](c4-level2.md) | Контейнеры (приложения, базы данных, сервисы) |
| **Level 3** | [Component](c4-level3.md) | Компоненты внутри контейнеров |
| **Level 4** | [Code](c4-level4.md) | Диаграммы классов и структура кода |

## Дополнительные диаграммы

| Тип | Описание |
|-----|----------|
| [Sequence Diagrams](sequences.md) | Диаграммы последовательности для ключевых потоков |
| [Deployment Diagram](deployment.md) | Диаграмма развёртывания (Docker containers) |

## Формат диаграмм

Все диаграммы созданы в формате **PlantUML** и находятся в каталоге `docs/diagrams/`.

### Просмотр диаграмм

#### Online (PlantUML Server)

1. Откройте http://www.plantuml.com/plantuml/uml/
2. Вставьте содержимое `.puml` файла
3. Нажмите "Submit"

#### VS Code

1. Установите расширение "PlantUML"
2. Откройте `.puml` файл
3. `Cmd/Ctrl + Shift + P` → "PlantUML: Preview Current Diagram"

#### CLI

```bash
# Установка
brew install plantuml

# Генерация PNG
plantuml docs/diagrams/*.puml

# Генерация SVG
plantuml -tsvg docs/diagrams/*.puml
```

## Структура файлов

```
docs/diagrams/
├── c4-level1-context.puml          # C4 Level 1: System Context
├── c4-level2-container.puml        # C4 Level 2: Container Diagram
├── c4-level3-bff-component.puml    # C4 Level 3: BFF Components
├── c4-level3-reports-component.puml # C4 Level 3: Reports Service
├── c4-level3-etl-component.puml    # C4 Level 3: ETL Pipeline
├── c4-level3-cdc-component.puml    # C4 Level 3: CDC Pipeline
├── c4-level4-bff-classes.puml      # C4 Level 4: BFF Class Diagram
├── c4-level4-reports-classes.puml  # C4 Level 4: Reports Classes
├── c4-level4-etl-classes.puml      # C4 Level 4: ETL Classes
├── c4-level4-data-model.puml       # Data Model Class Diagram
├── sequence-auth-flow.puml         # Auth Flow Sequence
├── sequence-cdc-flow.puml          # CDC Flow Sequence
├── sequence-reports-flow.puml      # Reports Flow Sequence
├── sequence-etl-flow.puml          # ETL Flow Sequence
└── deployment-diagram.puml         # Deployment Diagram
```
