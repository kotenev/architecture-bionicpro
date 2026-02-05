/*
 * BionicPRO - Structurizr DSL Architecture Model
 * Полная архитектурная модель системы управления бионическими протезами
 */

workspace "BionicPRO" "Enterprise Architecture for Bionic Prosthetics Management Platform" {

    !identifiers hierarchical

    model {
        # ===========================================================================
        # ACTORS (People)
        # ===========================================================================

        prostheticUser = person "Пользователь протеза" "Владелец бионического протеза, просматривает отчёты об использовании" "User"
        buyer = person "Покупатель" "Заказывает протезы через CRM" "User"
        crmOperator = person "Оператор CRM" "Управляет заказами и клиентами в CRM системе" "Operator"
        mlEngineer = person "ML-инженер" "Анализирует данные телеметрии для улучшения протезов" "Engineer"
        administrator = person "Администратор" "Управляет системой, пользователями и конфигурацией" "Admin"

        # ===========================================================================
        # EXTERNAL SYSTEMS
        # ===========================================================================

        yandexId = softwareSystem "Яндекс ID" "Внешний Identity Provider для аутентификации через Яндекс" "External"
        googleIdp = softwareSystem "Google" "Внешний Identity Provider для аутентификации через Google" "External"
        prosthesisDevice = softwareSystem "Бионический протез" "IoT устройство, передающее телеметрию по 4G" "External,IoT"

        # ===========================================================================
        # BIONICPRO SYSTEM
        # ===========================================================================

        bionicpro = softwareSystem "BionicPRO Platform" "Платформа управления бионическими протезами: отчёты, аналитика, CRM" {

            !docs docs
            !adrs adrs

            # Frontend
            frontend = container "Frontend SPA" "React Single Page Application для пользователей протезов" "React 18, TypeScript" "WebBrowser"

            # Security Layer
            bffAuth = container "BFF Auth Service" "Backend-for-Frontend: хранение токенов, проксирование API" "Python 3.11, Flask 3.0" "Service" {
                authController = component "AuthController" "Endpoints: /auth/login, /auth/callback, /auth/logout" "Flask Blueprint"
                proxyController = component "ProxyController" "Проксирование запросов к Reports Service" "Flask Blueprint"
                pkceService = component "PKCEService" "Генерация PKCE (code_verifier, code_challenge)" "Python"
                tokenService = component "TokenService" "Обмен кода на токены, refresh" "Python"
                sessionService = component "SessionService" "Управление сессиями в Redis" "Python"
                encryptionService = component "EncryptionService" "Шифрование токенов (Fernet)" "Python"
                keycloakClient = component "KeycloakClient" "HTTP клиент для Keycloak" "Python"
            }

            keycloak = container "Keycloak" "Identity Provider: OAuth2/OIDC, LDAP Federation, MFA" "Keycloak 26.5.2" "Identity"
            ldap = container "OpenLDAP" "Directory Service для User Federation" "OpenLDAP 1.5.0" "Database"
            redis = container "Redis" "Session Storage, Token Cache" "Redis 7" "Database"

            # Application Layer
            reportsService = container "Reports Service" "REST API для отчётов об использовании протезов" "Python 3.11, FastAPI 0.109" "Service" {
                reportsRouter = component "ReportsRouter" "Endpoints: /api/reports, /api/reports/{date}" "FastAPI Router"
                cdnRouter = component "CDNRouter" "Endpoints: /api/reports/cdn/*" "FastAPI Router"
                jwtHandler = component "JWTHandler" "Валидация JWT токенов Keycloak" "Python"
                clickhouseService = component "ClickHouseService" "Запросы к ClickHouse OLAP" "Python"
                s3Service = component "S3Service" "Работа с MinIO S3" "Python"
                reportGenerator = component "ReportGenerator" "Генерация JSON отчётов" "Python"
            }

            airflow = container "Apache Airflow" "ETL Orchestrator: планирование и выполнение pipeline" "Apache Airflow 2.8.1" "Service"

            # Data Layer - OLTP
            crmDb = container "CRM Database" "OLTP база клиентов, протезов и заказов" "PostgreSQL 14" "Database"
            telemetryDb = container "Telemetry Database" "OLTP база телеметрии с IoT устройств" "PostgreSQL 14" "Database"

            # Data Layer - OLAP
            clickhouse = container "ClickHouse" "OLAP витрина для аналитики и отчётов" "ClickHouse 24.1" "Database"

            # CDC Pipeline
            kafka = container "Apache Kafka" "Message Broker для CDC событий" "Confluent Kafka 7.5.0" "Queue"
            zookeeper = container "Zookeeper" "Координатор кластера Kafka" "Apache Zookeeper 3.8" "Infrastructure"
            debezium = container "Debezium Connect" "CDC коннектор для PostgreSQL" "Debezium 2.4" "Service"

            # Caching Layer
            minio = container "MinIO S3" "S3-совместимое Object Storage для отчётов" "MinIO" "Database"
            nginxCdn = container "Nginx CDN" "Reverse proxy с HTTP кэшированием" "Nginx 1.25" "Service"

            # Infrastructure DBs
            keycloakDb = container "Keycloak Database" "PostgreSQL для Keycloak" "PostgreSQL 14" "Database"
            airflowDb = container "Airflow Database" "PostgreSQL для Airflow metadata" "PostgreSQL 14" "Database"
        }

        # ===========================================================================
        # RELATIONSHIPS - System Context
        # ===========================================================================

        prostheticUser -> bionicpro "Просматривает отчёты об использовании протеза" "HTTPS"
        buyer -> bionicpro "Оформляет заказы" "HTTPS"
        crmOperator -> bionicpro "Управляет заказами и клиентами" "HTTPS"
        mlEngineer -> bionicpro "Анализирует данные телеметрии" "SQL"
        administrator -> bionicpro "Администрирует систему" "HTTPS"

        prosthesisDevice -> bionicpro "Отправляет телеметрию" "HTTPS/4G"

        bionicpro -> yandexId "Аутентификация через Яндекс" "OAuth2 OIDC"
        bionicpro -> googleIdp "Аутентификация через Google" "OAuth2 OIDC"

        # ===========================================================================
        # RELATIONSHIPS - Container Level
        # ===========================================================================

        # User interactions
        prostheticUser -> bionicpro.frontend "Просматривает отчёты" "HTTPS:3000"
        crmOperator -> bionicpro.crmDb "Работает с CRM" "SQL"
        mlEngineer -> bionicpro.clickhouse "Выполняет аналитические запросы" "HTTP:8123"
        administrator -> bionicpro.keycloak "Управляет пользователями" "HTTP:8080"
        administrator -> bionicpro.airflow "Мониторит ETL" "HTTP:8081"

        # Frontend → Services
        bionicpro.frontend -> bionicpro.bffAuth "API запросы + Session Cookie" "HTTP:8000"
        bionicpro.frontend -> bionicpro.nginxCdn "Загрузка отчётов" "HTTP:8002"
        bionicpro.frontend -> bionicpro.keycloak "OAuth2 redirect (browser)" "HTTP:8080"

        # BFF → Security
        bionicpro.bffAuth -> bionicpro.keycloak "OAuth2 PKCE flow" "HTTP:8080"
        bionicpro.bffAuth -> bionicpro.redis "Хранение зашифрованных токенов" "TCP:6379"
        bionicpro.bffAuth -> bionicpro.reportsService "Проксирование + JWT" "HTTP:8001"

        # Keycloak
        bionicpro.keycloak -> bionicpro.ldap "User Federation" "LDAP:389"
        bionicpro.keycloak -> bionicpro.keycloakDb "Хранение конфигурации" "TCP:5432"
        bionicpro.keycloak -> yandexId "Identity Brokering" "HTTPS"
        bionicpro.keycloak -> googleIdp "Identity Brokering" "HTTPS"

        # Reports Service
        bionicpro.reportsService -> bionicpro.clickhouse "Запросы отчётов" "TCP:9000"
        bionicpro.reportsService -> bionicpro.redis "Кэширование" "TCP:6379"
        bionicpro.reportsService -> bionicpro.minio "S3 операции" "HTTP:9000"

        # CDN
        bionicpro.nginxCdn -> bionicpro.minio "Проксирование" "HTTP:9000"

        # ETL Pipeline
        bionicpro.airflow -> bionicpro.crmDb "Extract CRM data" "TCP:5432"
        bionicpro.airflow -> bionicpro.telemetryDb "Extract Telemetry data" "TCP:5432"
        bionicpro.airflow -> bionicpro.clickhouse "Load transformed data" "TCP:9000"
        bionicpro.airflow -> bionicpro.reportsService "Invalidate cache" "HTTP:8001"
        bionicpro.airflow -> bionicpro.airflowDb "Metadata" "TCP:5432"

        # CDC Pipeline
        bionicpro.crmDb -> bionicpro.debezium "Logical Replication (WAL)" "TCP:5432"
        bionicpro.debezium -> bionicpro.kafka "Publish CDC events" "TCP:9092"
        bionicpro.kafka -> bionicpro.zookeeper "Координация" "TCP:2181"
        bionicpro.kafka -> bionicpro.clickhouse "KafkaEngine consume" "TCP:9092"

        # IoT
        prosthesisDevice -> bionicpro.telemetryDb "Отправка телеметрии" "HTTPS"

        # ===========================================================================
        # RELATIONSHIPS - Component Level (BFF Auth)
        # ===========================================================================

        bionicpro.bffAuth.authController -> bionicpro.bffAuth.pkceService "Генерация PKCE" "Python"
        bionicpro.bffAuth.authController -> bionicpro.bffAuth.tokenService "Обмен кода на токены" "Python"
        bionicpro.bffAuth.authController -> bionicpro.bffAuth.sessionService "Управление сессиями" "Python"
        bionicpro.bffAuth.proxyController -> bionicpro.bffAuth.sessionService "Получение токена" "Python"
        bionicpro.bffAuth.proxyController -> bionicpro.bffAuth.tokenService "Refresh токена" "Python"
        bionicpro.bffAuth.tokenService -> bionicpro.bffAuth.encryptionService "Шифрование токенов" "Python"
        bionicpro.bffAuth.tokenService -> bionicpro.bffAuth.keycloakClient "HTTP запросы к Keycloak" "Python"
        bionicpro.bffAuth.sessionService -> bionicpro.redis "Redis операции" "TCP:6379"
        bionicpro.bffAuth.keycloakClient -> bionicpro.keycloak "OAuth2 endpoints" "HTTP:8080"

        # ===========================================================================
        # RELATIONSHIPS - Component Level (Reports Service)
        # ===========================================================================

        bionicpro.reportsService.reportsRouter -> bionicpro.reportsService.jwtHandler "Валидация токена" "Python"
        bionicpro.reportsService.reportsRouter -> bionicpro.reportsService.clickhouseService "Получение данных" "Python"
        bionicpro.reportsService.cdnRouter -> bionicpro.reportsService.jwtHandler "Валидация токена" "Python"
        bionicpro.reportsService.cdnRouter -> bionicpro.reportsService.s3Service "S3 операции" "Python"
        bionicpro.reportsService.cdnRouter -> bionicpro.reportsService.reportGenerator "Генерация отчётов" "Python"
        bionicpro.reportsService.reportGenerator -> bionicpro.reportsService.clickhouseService "Данные для отчёта" "Python"
        bionicpro.reportsService.reportGenerator -> bionicpro.reportsService.s3Service "Сохранение в S3" "Python"
        bionicpro.reportsService.clickhouseService -> bionicpro.clickhouse "SQL запросы" "TCP:9000"
        bionicpro.reportsService.s3Service -> bionicpro.minio "S3 API" "HTTP:9000"

        # ===========================================================================
        # DEPLOYMENT MODEL
        # ===========================================================================

        deploymentEnvironment "Production" {
            deploymentNode "Docker Host" "Хост для запуска Docker контейнеров" "Linux / macOS / Windows" {
                deploymentNode "docker-network" "Внутренняя сеть Docker" "bridge" {

                    deploymentNode "frontend-container" "React SPA контейнер" "Docker" {
                        containerInstance bionicpro.frontend
                    }

                    deploymentNode "keycloak-container" "Identity Provider контейнер" "Docker" {
                        containerInstance bionicpro.keycloak
                    }

                    deploymentNode "ldap-container" "Directory Service контейнер" "Docker" {
                        containerInstance bionicpro.ldap
                    }

                    deploymentNode "bff-auth-container" "BFF Authentication контейнер" "Docker" {
                        containerInstance bionicpro.bffAuth
                    }

                    deploymentNode "redis-container" "Session Store контейнер" "Docker" {
                        containerInstance bionicpro.redis
                    }

                    deploymentNode "reports-service-container" "Reports API контейнер" "Docker" {
                        containerInstance bionicpro.reportsService
                    }

                    deploymentNode "airflow-container" "ETL Orchestrator контейнер" "Docker" {
                        containerInstance bionicpro.airflow
                    }

                    deploymentNode "crm-db-container" "CRM PostgreSQL контейнер" "Docker" {
                        containerInstance bionicpro.crmDb
                    }

                    deploymentNode "telemetry-db-container" "Telemetry PostgreSQL контейнер" "Docker" {
                        containerInstance bionicpro.telemetryDb
                    }

                    deploymentNode "clickhouse-container" "ClickHouse OLAP контейнер" "Docker" {
                        containerInstance bionicpro.clickhouse
                    }

                    deploymentNode "kafka-container" "Kafka Message Broker контейнер" "Docker" {
                        containerInstance bionicpro.kafka
                    }

                    deploymentNode "zookeeper-container" "Zookeeper координатор контейнер" "Docker" {
                        containerInstance bionicpro.zookeeper
                    }

                    deploymentNode "debezium-container" "CDC Connector контейнер" "Docker" {
                        containerInstance bionicpro.debezium
                    }

                    deploymentNode "minio-container" "S3 Object Storage контейнер" "Docker" {
                        containerInstance bionicpro.minio
                    }

                    deploymentNode "nginx-cdn-container" "CDN Proxy контейнер" "Docker" {
                        containerInstance bionicpro.nginxCdn
                    }

                    deploymentNode "keycloak-db-container" "Keycloak PostgreSQL контейнер" "Docker" {
                        containerInstance bionicpro.keycloakDb
                    }

                    deploymentNode "airflow-db-container" "Airflow PostgreSQL контейнер" "Docker" {
                        containerInstance bionicpro.airflowDb
                    }
                }
            }
        }
    }

    # ===========================================================================
    # VIEWS
    # ===========================================================================

    views {
        systemContext bionicpro "SystemContext" "Контекст системы BionicPRO" {
            include *
            autoLayout
        }

        container bionicpro "Containers" "Контейнерная диаграмма BionicPRO" {
            include *
            autoLayout
        }

        component bionicpro.bffAuth "BFF_Components" "Компоненты BFF Auth Service" {
            include *
            autoLayout
        }

        component bionicpro.reportsService "Reports_Components" "Компоненты Reports Service" {
            include *
            autoLayout
        }

        deployment bionicpro "Production" "Deployment" "Docker Deployment" {
            include *
            autoLayout
        }

        dynamic bionicpro "AuthFlow" "OAuth2 PKCE Authentication Flow" {
            prostheticUser -> bionicpro.frontend "1. Click Login"
            bionicpro.frontend -> bionicpro.bffAuth "2. GET /auth/login"
            bionicpro.bffAuth -> bionicpro.redis "3. Store PKCE verifier"
            bionicpro.frontend -> bionicpro.keycloak "4. Authorization Request"
            bionicpro.keycloak -> bionicpro.ldap "5. Validate credentials"
            bionicpro.frontend -> bionicpro.bffAuth "6. Callback with code"
            bionicpro.bffAuth -> bionicpro.keycloak "7. Exchange code"
            bionicpro.bffAuth -> bionicpro.redis "8. Store tokens"
            autoLayout
        }

        dynamic bionicpro "CDCFlow" "CDC Data Flow (CRM → ClickHouse)" {
            crmOperator -> bionicpro.crmDb "1. INSERT/UPDATE/DELETE"
            bionicpro.crmDb -> bionicpro.debezium "2. WAL event"
            bionicpro.debezium -> bionicpro.kafka "3. Publish to topic"
            bionicpro.kafka -> bionicpro.clickhouse "4. KafkaEngine consume"
            autoLayout
        }

        dynamic bionicpro "ReportsFlow" "Reports with CDN Caching" {
            prostheticUser -> bionicpro.frontend "1. Request report"
            bionicpro.frontend -> bionicpro.bffAuth "2. GET /api/reports/cdn"
            bionicpro.bffAuth -> bionicpro.reportsService "3. Proxy + JWT"
            bionicpro.reportsService -> bionicpro.minio "4. Check S3"
            bionicpro.reportsService -> bionicpro.clickhouse "5. Query OLAP"
            bionicpro.frontend -> bionicpro.nginxCdn "6. GET from CDN"
            bionicpro.nginxCdn -> bionicpro.minio "7. Proxy to S3"
            autoLayout
        }

        dynamic bionicpro "ETLFlow" "ETL Pipeline Flow" {
            bionicpro.airflow -> bionicpro.crmDb "1. Extract CRM"
            bionicpro.airflow -> bionicpro.telemetryDb "2. Extract Telemetry"
            bionicpro.airflow -> bionicpro.clickhouse "3. Load to OLAP"
            bionicpro.airflow -> bionicpro.reportsService "4. Invalidate cache"
            bionicpro.reportsService -> bionicpro.minio "5. Delete from S3"
            autoLayout
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "IoT" {
                background #438dd5
                color #ffffff
                shape Robot
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bb65
                color #000000
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
            element "User" {
                background #08427b
            }
            element "Operator" {
                background #5b9bd5
            }
            element "Engineer" {
                background #70ad47
            }
            element "Admin" {
                background #c00000
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
            element "WebBrowser" {
                shape WebBrowser
            }
            element "Service" {
                shape Hexagon
            }
            element "Identity" {
                background #ff6600
                color #ffffff
                shape Hexagon
            }
            element "Infrastructure" {
                background #999999
                color #ffffff
            }
        }

        theme default
    }

    # ===========================================================================
    # CONFIGURATION
    # ===========================================================================

    configuration {
        scope softwaresystem
    }

}
