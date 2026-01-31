-- ============================================================================
-- ClickHouse OLAP Database Schema
-- BionicPRO Reports - Витрина отчётности
-- ============================================================================

-- Создание базы данных для отчётов
CREATE DATABASE IF NOT EXISTS reports;

-- ============================================================================
-- Основная витрина: user_prosthesis_stats
-- Агрегированные данные телеметрии + данные клиентов из CRM
-- Партиционирование по дате для быстрого доступа и TTL
-- ============================================================================
CREATE TABLE IF NOT EXISTS reports.user_prosthesis_stats
(
    -- Ключевые идентификаторы
    user_id             String,                              -- ID пользователя (external_id из CRM)
    prosthesis_id       UInt32,                              -- ID протеза
    chip_id             String,                              -- ID чипа ESP32

    -- Временные измерения
    report_date         Date,                                -- Дата отчёта
    report_hour         UInt8,                               -- Час (0-23)

    -- Данные из CRM (денормализовано для скорости)
    customer_name       String,                              -- ФИО клиента
    customer_email      String,                              -- Email
    customer_region     LowCardinality(String),              -- Регион (russia, europe)
    customer_branch     String,                              -- Филиал
    prosthesis_model    String,                              -- Модель протеза
    prosthesis_category LowCardinality(String),              -- Категория (arm, leg, hand)
    prosthesis_serial   String,                              -- Серийный номер протеза

    -- Метрики использования
    movements_count     UInt32,                              -- Количество движений
    successful_movements UInt32,                             -- Успешные движения
    success_rate        Float32,                             -- Процент успешных движений

    -- Метрики времени отклика (мс)
    avg_response_time   Float32,                             -- Среднее время отклика
    min_response_time   UInt32,                              -- Минимальное
    max_response_time   UInt32,                              -- Максимальное

    -- Метрики батареи
    avg_battery_level   Float32,                             -- Средний уровень заряда
    min_battery_level   UInt8,                               -- Минимальный уровень
    max_battery_level   UInt8,                               -- Максимальный уровень

    -- Метрики температуры (°C)
    avg_actuator_temp   Float32,                             -- Средняя температура актуатора
    max_actuator_temp   Float32,                             -- Максимальная температура

    -- Ошибки и качество
    error_count         UInt32,                              -- Количество ошибок
    warning_count       UInt32,                              -- Количество предупреждений
    avg_connection_quality Float32,                          -- Среднее качество связи

    -- Метрики миосигналов
    avg_myo_amplitude   Float32,                             -- Средняя амплитуда миосигнала

    -- Служебные поля
    etl_processed_at    DateTime DEFAULT now(),              -- Время обработки ETL
    source_updated_at   DateTime                             -- Время обновления в источнике
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (user_id, report_date, report_hour, prosthesis_id)
TTL report_date + INTERVAL 365 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Материализованное представление: Дневная статистика
-- ============================================================================
CREATE TABLE IF NOT EXISTS reports.user_daily_stats
(
    user_id             String,
    prosthesis_id       UInt32,
    report_date         Date,
    customer_name       String,
    prosthesis_model    String,

    -- Агрегаты за день
    total_movements     UInt64,
    total_successful    UInt64,
    daily_success_rate  Float32,
    avg_response_time   Float32,
    min_battery         UInt8,
    max_temp            Float32,
    total_errors        UInt64,
    active_hours        UInt8,                               -- Количество активных часов

    etl_processed_at    DateTime DEFAULT now()
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (user_id, report_date, prosthesis_id)
TTL report_date + INTERVAL 365 DAY;

-- Материализованное представление для автоматической агрегации
CREATE MATERIALIZED VIEW IF NOT EXISTS reports.mv_user_daily_stats
TO reports.user_daily_stats
AS SELECT
    user_id,
    prosthesis_id,
    report_date,
    any(customer_name) AS customer_name,
    any(prosthesis_model) AS prosthesis_model,
    sum(movements_count) AS total_movements,
    sum(successful_movements) AS total_successful,
    if(sum(movements_count) > 0,
       round(sum(successful_movements) / sum(movements_count) * 100, 2),
       0) AS daily_success_rate,
    avg(avg_response_time) AS avg_response_time,
    min(min_battery_level) AS min_battery,
    max(max_actuator_temp) AS max_temp,
    sum(error_count) AS total_errors,
    count() AS active_hours,
    now() AS etl_processed_at
FROM reports.user_prosthesis_stats
GROUP BY user_id, prosthesis_id, report_date;

-- ============================================================================
-- Представление для API: Отчёт пользователя за период
-- ============================================================================
CREATE VIEW IF NOT EXISTS reports.v_user_report AS
SELECT
    user_id,
    customer_name,
    prosthesis_model,
    prosthesis_serial,
    customer_region,
    report_date,

    -- Суммарные метрики за день
    sum(movements_count) AS daily_movements,
    sum(successful_movements) AS daily_successful,
    round(sum(successful_movements) / nullIf(sum(movements_count), 0) * 100, 2) AS daily_success_rate,

    -- Средние метрики
    round(avg(avg_response_time), 2) AS avg_response_time_ms,
    round(avg(avg_battery_level), 1) AS avg_battery_percent,
    round(avg(avg_actuator_temp), 1) AS avg_temp_celsius,

    -- Экстремумы
    min(min_battery_level) AS min_battery_percent,
    max(max_actuator_temp) AS max_temp_celsius,

    -- Качество
    sum(error_count) AS daily_errors,
    round(avg(avg_connection_quality), 1) AS avg_connection_quality,

    -- Активность
    count() AS active_hours

FROM reports.user_prosthesis_stats
GROUP BY
    user_id,
    customer_name,
    prosthesis_model,
    prosthesis_serial,
    customer_region,
    report_date
ORDER BY report_date DESC;

-- ============================================================================
-- Представление для API: Сводка по пользователю за всё время
-- ============================================================================
CREATE VIEW IF NOT EXISTS reports.v_user_summary AS
SELECT
    user_id,
    any(customer_name) AS customer_name,
    any(prosthesis_model) AS prosthesis_model,
    any(prosthesis_serial) AS prosthesis_serial,
    any(customer_region) AS customer_region,

    min(report_date) AS first_activity_date,
    max(report_date) AS last_activity_date,
    dateDiff('day', min(report_date), max(report_date)) + 1 AS total_days,
    count(DISTINCT report_date) AS active_days,

    sum(movements_count) AS total_movements,
    sum(successful_movements) AS total_successful,
    round(sum(successful_movements) / nullIf(sum(movements_count), 0) * 100, 2) AS overall_success_rate,

    round(avg(avg_response_time), 2) AS avg_response_time_ms,
    round(avg(avg_battery_level), 1) AS avg_battery_percent,

    sum(error_count) AS total_errors,
    round(sum(error_count) / nullIf(count(DISTINCT report_date), 0), 2) AS avg_errors_per_day

FROM reports.user_prosthesis_stats
GROUP BY user_id;

-- ============================================================================
-- Словарь для быстрого поиска данных пользователя
-- ============================================================================
CREATE DICTIONARY IF NOT EXISTS reports.dict_user_info
(
    user_id String,
    customer_name String,
    customer_email String,
    customer_region String,
    prosthesis_model String,
    prosthesis_serial String
)
PRIMARY KEY user_id
SOURCE(CLICKHOUSE(
    HOST 'localhost'
    PORT 9000
    USER 'default'
    TABLE 'user_prosthesis_stats'
    DB 'reports'
))
LAYOUT(HASHED())
LIFETIME(MIN 300 MAX 600);
