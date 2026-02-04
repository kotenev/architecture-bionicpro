# C4 Level 4: Code (Class Diagrams)

## Описание

Class Diagrams показывают структуру кода ключевых сервисов системы BionicPRO.

## BFF Auth Service Classes

```plantuml
@startuml BFF_Classes
!theme plain
title BFF Auth Service - Class Diagram

package "Controllers" {
    class AuthController {
        - pkce_service: PKCEService
        - token_service: TokenService
        - session_service: SessionService
        --
        + login(): Response
        + callback(code, state): Response
        + logout(): Response
        + me(): Response
    }

    class ProxyController {
        - session_service: SessionService
        - token_service: TokenService
        --
        + proxy_request(path): Response
    }
}

package "Services" {
    class PKCEService {
        + generate_verifier(): str
        + generate_challenge(verifier): str
    }

    class TokenService {
        - keycloak_client: KeycloakClient
        - encryption: EncryptionService
        --
        + exchange_code(code, verifier): TokenPair
        + refresh_tokens(session_id): TokenPair
        + get_access_token(session_id): str
    }

    class SessionService {
        - redis_client: RedisClient
        --
        + create_session(user_info): str
        + get_session(session_id): Session
        + validate_session(session_id): bool
        + rotate_session_id(old_id): str
    }

    class EncryptionService {
        - fernet: Fernet
        --
        + encrypt(plaintext): str
        + decrypt(ciphertext): str
    }
}

package "Clients" {
    class KeycloakClient {
        - base_url: str
        - realm: str
        --
        + get_auth_url(state, challenge): str
        + exchange_code(code, verifier): TokenResponse
        + refresh_token(refresh_token): TokenResponse
        + get_user_info(access_token): UserInfo
    }

    class RedisClient {
        - connection: Redis
        --
        + set(key, value, ttl): void
        + get(key): str
        + delete(key): void
    }
}

package "Models" {
    class TokenPair {
        + access_token: str
        + refresh_token: str
        + expires_in: int
    }

    class Session {
        + session_id: str
        + user_info: UserInfo
        + created_at: datetime
    }

    class UserInfo {
        + sub: str
        + preferred_username: str
        + email: str
        + roles: List[str]
    }
}

AuthController --> PKCEService
AuthController --> TokenService
AuthController --> SessionService
ProxyController --> SessionService
ProxyController --> TokenService
TokenService --> KeycloakClient
TokenService --> EncryptionService
SessionService --> RedisClient
TokenService --> TokenPair
SessionService --> Session

@enduml
```

---

## Reports Service Classes

```plantuml
@startuml Reports_Classes
!theme plain
title Reports Service - Class Diagram

package "Routers" {
    class ReportsRouter {
        - ch_service: ClickHouseService
        - cache_service: CacheService
        --
        + get_reports(user): ReportsList
        + get_report_by_date(date, user): DailyReport
        + get_summary(user): UserSummary
    }

    class CDNRouter {
        - s3_service: S3Service
        - report_generator: ReportGenerator
        --
        + get_cdn_list(user): CDNResponse
        + get_cdn_report(date, user): CDNResponse
        + invalidate_cache(request): void
    }
}

package "Services" {
    class ClickHouseService {
        - client: ClickHouseClient
        --
        + get_user_reports(username): List[ReportDate]
        + get_report_by_date(username, date): DailyReport
        + get_cdc_table_stats(): Dict
    }

    class S3Service {
        - client: S3Client
        - bucket: str
        --
        + check_exists(key): bool
        + put_object(key, data): str
        + delete_prefix(prefix): int
        + get_cdn_url(key): str
    }

    class CacheService {
        - redis: Redis
        --
        + get(key): str
        + set(key, value, ttl): void
        + delete_pattern(pattern): int
    }

    class ReportGenerator {
        - ch_service: ClickHouseService
        - s3_service: S3Service
        --
        + generate_reports_list(user_id, username): dict
        + generate_daily_report(user_id, username, date): dict
    }
}

package "Auth" {
    class JWTHandler {
        - public_key: RSAPublicKey
        --
        + decode_token(token): TokenPayload
        + get_current_user(credentials): User
    }

    class User {
        + sub: str
        + preferred_username: str
        + email: str
        + roles: List[str]
    }
}

package "Models" {
    class ReportsList {
        + reports: List[ReportDate]
        + total: int
        + user: str
    }

    class DailyReport {
        + date: str
        + summary: DailySummary
        + hourly_data: List[HourlyData]
    }

    class DailySummary {
        + total_movements: int
        + avg_response_time_ms: float
        + total_errors: int
    }

    class CDNResponse {
        + cdn_url: str
        + expires_in: int
    }
}

ReportsRouter --> ClickHouseService
ReportsRouter --> CacheService
CDNRouter --> S3Service
CDNRouter --> ReportGenerator
ReportGenerator --> ClickHouseService
ReportGenerator --> S3Service
ReportsRouter --> JWTHandler
JWTHandler --> User

@enduml
```

---

## ETL Jobs Classes

```plantuml
@startuml ETL_Classes
!theme plain
title ETL Jobs - Class Diagram

package "DAGs" {
    class BionicProReportsETL {
        + dag_id: str
        + schedule_interval: str
        --
        + create_dag(): DAG
    }
}

package "Tasks" {
    class ExtractCRMTask {
        - postgres_hook: PostgresHook
        --
        + execute(context): DataFrame
        - fetch_customers(): DataFrame
        - fetch_prostheses(): DataFrame
    }

    class ExtractTelemetryTask {
        - postgres_hook: PostgresHook
        - lookback_hours: int
        --
        + execute(context): DataFrame
        - aggregate_by_hour(): DataFrame
    }

    class TransformTask {
        --
        + execute(context): DataFrame
        - join_datasets(crm, telemetry): DataFrame
        - calculate_metrics(df): DataFrame
    }

    class LoadToClickHouseTask {
        - clickhouse_client: ClickHouseClient
        --
        + execute(context): List[str]
        - insert_data(df): int
        - get_affected_user_ids(df): List[str]
    }

    class InvalidateCacheTask {
        - http_hook: HttpHook
        --
        + execute(context): void
        - invalidate_users(user_ids): void
    }
}

package "Hooks" {
    class PostgresHook {
        - conn_id: str
        --
        + get_pandas_df(sql): DataFrame
    }

    class ClickHouseHook {
        - conn_id: str
        --
        + insert_dataframe(table, df): int
    }

    class HttpHook {
        - conn_id: str
        --
        + run(endpoint, data): Response
    }
}

package "Models" {
    class CRMData {
        + customer_id: UUID
        + customer_name: str
        + ldap_username: str
        + prosthesis_id: UUID
        + chip_id: str
    }

    class TelemetryData {
        + chip_id: str
        + hour: datetime
        + movements_count: int
        + avg_response_time: float
    }

    class TransformedData {
        + user_id: UUID
        + ldap_username: str
        + date: date
        + hour: datetime
        + movements_count: int
        + error_rate: float
    }
}

BionicProReportsETL --> ExtractCRMTask
BionicProReportsETL --> ExtractTelemetryTask
BionicProReportsETL --> TransformTask
BionicProReportsETL --> LoadToClickHouseTask
BionicProReportsETL --> InvalidateCacheTask

ExtractCRMTask --> PostgresHook
ExtractTelemetryTask --> PostgresHook
LoadToClickHouseTask --> ClickHouseHook
InvalidateCacheTask --> HttpHook

ExtractCRMTask --> CRMData
ExtractTelemetryTask --> TelemetryData
TransformTask --> TransformedData

@enduml
```

---

## Data Model

```plantuml
@startuml Data_Model
!theme plain
title BionicPRO - Data Model

package "OLTP: PostgreSQL" {
    class "crm.customers" {
        + id: UUID <<PK>>
        + name: VARCHAR
        + email: VARCHAR <<UK>>
        + ldap_username: VARCHAR <<UK>>
        + created_at: TIMESTAMP
        + updated_at: TIMESTAMP
    }

    class "crm.prostheses" {
        + id: UUID <<PK>>
        + customer_id: UUID <<FK>>
        + model_id: UUID <<FK>>
        + chip_id: VARCHAR <<UK>>
        + serial_number: VARCHAR
    }

    class "crm.prosthesis_models" {
        + id: UUID <<PK>>
        + name: VARCHAR
        + warranty_years: INTEGER
    }

    class "telemetry.raw_telemetry" {
        + id: BIGSERIAL <<PK>>
        + chip_id: VARCHAR
        + event_time: TIMESTAMP
        + movement_type: INTEGER
        + response_time_ms: FLOAT
        + battery_level: FLOAT
        + error_code: INTEGER
    }

    "crm.customers" "1" -- "0..*" "crm.prostheses"
    "crm.prosthesis_models" "1" -- "0..*" "crm.prostheses"
}

package "OLAP: ClickHouse" {
    class "reports.user_prosthesis_stats" <<MergeTree>> {
        + user_id: UUID
        + ldap_username: String
        + date: Date
        + hour: DateTime
        + movements_count: UInt32
        + avg_response_time: Float32
        + error_count: UInt32
        + prosthesis_model: String
        --
        PARTITION BY toYYYYMM(date)
        ORDER BY (ldap_username, date, hour)
    }

    class "reports.crm_customers" <<ReplacingMergeTree>> {
        + id: UUID
        + name: String
        + ldap_username: String
        + _version: UInt64
        + _deleted: UInt8
    }

    class "reports.crm_prostheses" <<ReplacingMergeTree>> {
        + id: UUID
        + customer_id: UUID
        + chip_id: String
        + _version: UInt64
        + _deleted: UInt8
    }
}

"crm.customers" ..> "reports.user_prosthesis_stats" : ETL
"telemetry.raw_telemetry" ..> "reports.user_prosthesis_stats" : ETL
"crm.customers" ..> "reports.crm_customers" : CDC

@enduml
```

## Исходные файлы

- [c4-level4-bff-classes.puml](c4-level4-bff-classes.puml)
- [c4-level4-reports-classes.puml](c4-level4-reports-classes.puml)
- [c4-level4-etl-classes.puml](c4-level4-etl-classes.puml)
- [c4-level4-data-model.puml](c4-level4-data-model.puml)
