# Проектирование базы данных

## 1. Обзор схемы БД

### 1.1 Основные сущности

Система включает следующие основные сущности:
1. **Users** - Пользователи системы
2. **Researches** - Маркетинговые исследования
3. **Reports** - Сгенерированные отчеты
4. **DataSources** - Источники данных
5. **CollectedData** - Собранные данные
6. **AnalysisResults** - Результаты анализа
7. **Verifications** - Результаты верификации источников
8. **Templates** - Шаблоны отчетов
9. **AuditLogs** - Логи аудита

### 1.2 Диаграмма ER (Entity-Relationship)

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│    Users     │ 1     * │    Researches    │ 1     * │   Reports    │
│──────────────│◄────────│──────────────────│◄────────│──────────────│
│ id           │         │ id               │         │ id           │
│ email        │         │ user_id (FK)     │         │ research_id  │
│ password_hash│         │ title            │         │ title        │
│ role         │         │ status           │         │ file_url     │
│ created_at   │         │ product_desc     │         │ format       │
│ ...          │         │ region           │         │ created_at   │
└──────────────┘         │ created_at       │         │ ...          │
                         │ ...              │         └──────────────┘
                         └──────────────────┘
                                 │ 1
                                 │
                                 │ *
                         ┌──────────────────┐         ┌──────────────┐
                         │  CollectedData   │ *     1 │ DataSources  │
                         │──────────────────│◄────────│──────────────│
                         │ id               │         │ id           │
                         │ research_id (FK) │         │ name         │
                         │ source_id (FK)   │         │ type         │
                         │ data             │         │ url          │
                         │ collected_at     │         │ reliability  │
                         │ ...              │         │ ...          │
                         └──────────────────┘         └──────────────┘
                                 │ 1
                                 │
                                 │ *
                         ┌──────────────────┐
                         │   Verifications  │
                         │──────────────────│
                         │ id               │
                         │ data_id (FK)     │
                         │ is_verified      │
                         │ confidence_score │
                         │ verified_at      │
                         │ ...              │
                         └──────────────────┘
```

## 2. Детальное описание таблиц

### 2.1 Таблица: users

**Описание**: Хранит информацию о пользователях системы

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Квоты и лимиты
    research_quota INTEGER DEFAULT 10,
    researches_used INTEGER DEFAULT 0,

    -- Дополнительная информация
    company VARCHAR(255),
    phone VARCHAR(50),

    CONSTRAINT users_role_check CHECK (role IN ('user', 'premium', 'admin'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**Поля**:
- `id`: Уникальный идентификатор (UUID)
- `email`: Email пользователя (уникальный)
- `password_hash`: Хэш пароля (bcrypt)
- `full_name`: Полное имя
- `role`: Роль пользователя (user, premium, admin)
- `is_active`: Активен ли аккаунт
- `is_verified`: Подтвержден ли email
- `research_quota`: Квота исследований в месяц
- `researches_used`: Использовано исследований в текущем месяце

### 2.2 Таблица: researches

**Описание**: Хранит информацию о маркетинговых исследованиях

```sql
CREATE TABLE researches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Основная информация
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    product_description TEXT NOT NULL,
    industry VARCHAR(255),
    region VARCHAR(255) NOT NULL,

    -- Параметры исследования
    target_audience TEXT,
    budget_range VARCHAR(100),
    additional_params JSONB,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Статистика
    progress_percent INTEGER DEFAULT 0,
    estimated_completion_time TIMESTAMP WITH TIME ZONE,

    -- Результаты
    summary_data JSONB,

    CONSTRAINT researches_status_check CHECK (
        status IN ('pending', 'collecting_data', 'analyzing', 'generating_report', 'completed', 'failed', 'cancelled')
    ),
    CONSTRAINT researches_progress_check CHECK (progress_percent >= 0 AND progress_percent <= 100)
);

CREATE INDEX idx_researches_user_id ON researches(user_id);
CREATE INDEX idx_researches_status ON researches(status);
CREATE INDEX idx_researches_created_at ON researches(created_at);
CREATE INDEX idx_researches_region ON researches(region);
CREATE INDEX idx_researches_industry ON researches(industry);
```

**Статусы исследования**:
- `pending`: Ожидает начала обработки
- `collecting_data`: Сбор данных
- `analyzing`: Анализ данных
- `generating_report`: Генерация отчета
- `completed`: Завершено успешно
- `failed`: Завершено с ошибкой
- `cancelled`: Отменено пользователем

### 2.3 Таблица: reports

**Описание**: Хранит информацию о сгенерированных отчетах

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id UUID NOT NULL REFERENCES researches(id) ON DELETE CASCADE,

    -- Основная информация
    title VARCHAR(500) NOT NULL,
    format VARCHAR(20) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,

    -- Хранение файлов
    file_url VARCHAR(1000),
    file_size_bytes BIGINT,

    -- Структура отчета
    structure_data JSONB,

    -- Статистика
    page_count INTEGER,
    word_count INTEGER,
    table_count INTEGER,
    figure_count INTEGER,
    source_count INTEGER,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Метаданные ГОСТ
    gost_compliance_score DECIMAL(3,2),

    CONSTRAINT reports_format_check CHECK (format IN ('pdf', 'docx', 'html')),
    CONSTRAINT reports_version_check CHECK (version > 0),
    CONSTRAINT reports_compliance_check CHECK (gost_compliance_score >= 0 AND gost_compliance_score <= 1)
);

CREATE INDEX idx_reports_research_id ON reports(research_id);
CREATE INDEX idx_reports_format ON reports(format);
CREATE INDEX idx_reports_created_at ON reports(created_at);
CREATE UNIQUE INDEX idx_reports_research_format_version ON reports(research_id, format, version);
```

**Поля**:
- `format`: Формат отчета (pdf, docx, html)
- `version`: Версия отчета (инкрементальная)
- `file_url`: URL файла в object storage
- `structure_data`: JSON со структурой отчета (разделы, подразделы)
- `gost_compliance_score`: Оценка соответствия ГОСТ (0-1)

### 2.4 Таблица: data_sources

**Описание**: Справочник источников данных

```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Основная информация
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(1000),
    description TEXT,

    -- Оценка источника
    reliability_level INTEGER NOT NULL DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- API/Scraping параметры
    api_endpoint VARCHAR(1000),
    api_key_required BOOLEAN DEFAULT FALSE,
    scraping_config JSONB,

    -- Метаданные
    update_frequency VARCHAR(50),
    last_checked_at TIMESTAMP WITH TIME ZONE,
    data_coverage TEXT,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT data_sources_type_check CHECK (
        type IN ('api', 'web_scraping', 'file_download', 'manual')
    ),
    CONSTRAINT data_sources_reliability_check CHECK (reliability_level >= 1 AND reliability_level <= 4)
);

CREATE INDEX idx_data_sources_type ON data_sources(type);
CREATE INDEX idx_data_sources_reliability ON data_sources(reliability_level);
CREATE INDEX idx_data_sources_active ON data_sources(is_active);
```

**Уровни надежности**:
- 1: Высокая (Росстат, министерства)
- 2: Средняя (аналитические агентства)
- 3: Условная (требует проверки)
- 4: Низкая (непроверенные источники)

### 2.5 Таблица: collected_data

**Описание**: Собранные данные для исследований

```sql
CREATE TABLE collected_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id UUID NOT NULL REFERENCES researches(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES data_sources(id),

    -- Данные
    data_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    raw_data TEXT,

    -- Метаданные
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_date DATE,
    is_processed BOOLEAN DEFAULT FALSE,

    -- Статус
    status VARCHAR(50) DEFAULT 'raw',
    error_message TEXT,

    CONSTRAINT collected_data_type_check CHECK (
        data_type IN ('market_stats', 'competitor_info', 'news', 'trend', 'regional_data', 'consumer_data', 'other')
    ),
    CONSTRAINT collected_data_status_check CHECK (
        status IN ('raw', 'processing', 'processed', 'verified', 'rejected')
    )
);

CREATE INDEX idx_collected_data_research_id ON collected_data(research_id);
CREATE INDEX idx_collected_data_source_id ON collected_data(source_id);
CREATE INDEX idx_collected_data_type ON collected_data(data_type);
CREATE INDEX idx_collected_data_collected_at ON collected_data(collected_at);
CREATE INDEX idx_collected_data_status ON collected_data(status);
```

**Типы данных**:
- `market_stats`: Рыночная статистика
- `competitor_info`: Информация о конкурентах
- `news`: Новости
- `trend`: Трендовые данные
- `regional_data`: Региональные данные
- `consumer_data`: Данные о потребителях

### 2.6 Таблица: verifications

**Описание**: Результаты верификации данных

```sql
CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_id UUID NOT NULL REFERENCES collected_data(id) ON DELETE CASCADE,

    -- Результаты верификации
    is_verified BOOLEAN NOT NULL,
    confidence_score DECIMAL(3,2),
    verification_method VARCHAR(100),

    -- Детали проверки
    checks_performed JSONB,
    issues_found JSONB,
    cross_validation_sources JSONB,

    -- Временные метки
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_by VARCHAR(255),

    -- Комментарии
    notes TEXT,

    CONSTRAINT verifications_confidence_check CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_verifications_data_id ON verifications(data_id);
CREATE INDEX idx_verifications_is_verified ON verifications(is_verified);
CREATE INDEX idx_verifications_verified_at ON verifications(verified_at);
```

**Методы верификации**:
- `source_reliability`: Оценка надежности источника
- `cross_validation`: Перекрестная проверка
- `actuality_check`: Проверка актуальности
- `consistency_check`: Проверка согласованности
- `manual_review`: Ручная проверка

### 2.7 Таблица: analysis_results

**Описание**: Результаты анализа данных

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id UUID NOT NULL REFERENCES researches(id) ON DELETE CASCADE,

    -- Тип анализа
    analysis_type VARCHAR(100) NOT NULL,

    -- Результаты
    results JSONB NOT NULL,
    summary TEXT,

    -- Метрики
    confidence_score DECIMAL(3,2),
    data_completeness DECIMAL(3,2),

    -- Визуализации
    visualizations JSONB,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Версионирование
    version INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT analysis_results_type_check CHECK (
        analysis_type IN (
            'market_analysis', 'competitor_analysis', 'trend_analysis',
            'regional_analysis', 'consumer_analysis', 'swot_analysis'
        )
    ),
    CONSTRAINT analysis_confidence_check CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT analysis_completeness_check CHECK (data_completeness >= 0 AND data_completeness <= 1)
);

CREATE INDEX idx_analysis_results_research_id ON analysis_results(research_id);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);
CREATE INDEX idx_analysis_results_created_at ON analysis_results(created_at);
```

**Типы анализа**:
- `market_analysis`: Анализ рынка
- `competitor_analysis`: Конкурентный анализ
- `trend_analysis`: Трендовый анализ
- `regional_analysis`: Региональный анализ
- `consumer_analysis`: Анализ потребителей
- `swot_analysis`: SWOT-анализ

### 2.8 Таблица: templates

**Описание**: Шаблоны отчетов

```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Основная информация
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,

    -- Шаблон
    template_data JSONB NOT NULL,

    -- Параметры
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    -- Версионирование
    version INTEGER NOT NULL DEFAULT 1,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    CONSTRAINT templates_type_check CHECK (
        template_type IN ('report_structure', 'section_template', 'visualization_template')
    )
);

CREATE INDEX idx_templates_type ON templates(template_type);
CREATE INDEX idx_templates_active ON templates(is_active);
CREATE INDEX idx_templates_default ON templates(is_default);
```

### 2.9 Таблица: audit_logs

**Описание**: Логи аудита действий пользователей

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Пользователь
    user_id UUID REFERENCES users(id),

    -- Действие
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,

    -- Детали
    details JSONB,
    ip_address INET,
    user_agent TEXT,

    -- Временная метка
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT audit_logs_action_check CHECK (
        action IN (
            'user_login', 'user_logout', 'user_register',
            'research_create', 'research_update', 'research_delete',
            'report_generate', 'report_download',
            'admin_action'
        )
    )
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
```

## 3. Дополнительные таблицы

### 3.1 Таблица: refresh_tokens

**Описание**: Refresh tokens для JWT аутентификации

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    is_revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

### 3.2 Таблица: notifications

**Описание**: Уведомления для пользователей

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Содержание
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,

    -- Статус
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Связанные сущности
    related_entity_type VARCHAR(50),
    related_entity_id UUID,

    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT notifications_type_check CHECK (
        type IN ('research_completed', 'research_failed', 'quota_warning', 'system_alert')
    )
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

## 4. Триггеры и хранимые процедуры

### 4.1 Триггер: Обновление updated_at

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_researches_updated_at BEFORE UPDATE ON researches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4.2 Хранимая процедура: Сброс месячной квоты

```sql
CREATE OR REPLACE FUNCTION reset_monthly_quotas()
RETURNS void AS $$
BEGIN
    UPDATE users
    SET researches_used = 0
    WHERE researches_used > 0;
END;
$$ LANGUAGE plpgsql;

-- Создание задания для выполнения каждый месяц (требует расширения pg_cron)
-- SELECT cron.schedule('reset-monthly-quotas', '0 0 1 * *', 'SELECT reset_monthly_quotas()');
```

### 4.3 Функция: Проверка доступности квоты

```sql
CREATE OR REPLACE FUNCTION check_research_quota(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_quota INTEGER;
    v_used INTEGER;
BEGIN
    SELECT research_quota, researches_used
    INTO v_quota, v_used
    FROM users
    WHERE id = p_user_id;

    RETURN v_used < v_quota;
END;
$$ LANGUAGE plpgsql;
```

## 5. Представления (Views)

### 5.1 Представление: Активные исследования

```sql
CREATE VIEW active_researches AS
SELECT
    r.id,
    r.user_id,
    u.email as user_email,
    r.title,
    r.status,
    r.progress_percent,
    r.created_at,
    r.estimated_completion_time,
    COUNT(DISTINCT cd.id) as data_items_collected,
    COUNT(DISTINCT rep.id) as reports_generated
FROM researches r
JOIN users u ON r.user_id = u.id
LEFT JOIN collected_data cd ON r.id = cd.research_id
LEFT JOIN reports rep ON r.id = rep.research_id
WHERE r.status IN ('collecting_data', 'analyzing', 'generating_report')
GROUP BY r.id, u.email;
```

### 5.2 Представление: Статистика пользователей

```sql
CREATE VIEW user_statistics AS
SELECT
    u.id,
    u.email,
    u.role,
    u.created_at as registered_at,
    COUNT(DISTINCT r.id) as total_researches,
    COUNT(DISTINCT rep.id) as total_reports,
    MAX(r.created_at) as last_research_at,
    u.research_quota,
    u.researches_used
FROM users u
LEFT JOIN researches r ON u.id = r.user_id
LEFT JOIN reports rep ON r.id = rep.research_id
GROUP BY u.id;
```

## 6. Индексы для производительности

### 6.1 Композитные индексы

```sql
-- Поиск исследований пользователя по статусу
CREATE INDEX idx_researches_user_status ON researches(user_id, status);

-- Поиск данных исследования по типу
CREATE INDEX idx_collected_data_research_type ON collected_data(research_id, data_type);

-- Поиск отчетов по исследованию и формату
CREATE INDEX idx_reports_research_format ON reports(research_id, format);

-- Поиск непрочитанных уведомлений
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
```

### 6.2 JSONB индексы

```sql
-- GIN индексы для JSONB полей
CREATE INDEX idx_researches_additional_params ON researches USING GIN (additional_params);
CREATE INDEX idx_collected_data_data ON collected_data USING GIN (data);
CREATE INDEX idx_analysis_results_results ON analysis_results USING GIN (results);
```

## 7. Партиционирование (для будущего масштабирования)

### 7.1 Партиционирование audit_logs по времени

```sql
-- Создание партиционированной таблицы (PostgreSQL 10+)
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Создание партиций по месяцам
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- И так далее...
```

## 8. Начальные данные (Seed Data)

### 8.1 Источники данных по умолчанию

```sql
INSERT INTO data_sources (name, type, url, reliability_level, description) VALUES
('Росстат', 'api', 'https://rosstat.gov.ru/', 1, 'Федеральная служба государственной статистики'),
('ЦБ РФ', 'api', 'https://www.cbr.ru/', 1, 'Центральный банк Российской Федерации'),
('ЕГРЮЛ', 'api', 'https://egrul.nalog.ru/', 1, 'Единый государственный реестр юридических лиц'),
('hh.ru Статистика', 'api', 'https://stats.hh.ru/', 2, 'Статистика рынка труда'),
('РБК', 'web_scraping', 'https://www.rbc.ru/', 2, 'РБК - новости и аналитика'),
('Интерфакс', 'web_scraping', 'https://www.interfax.ru/', 2, 'Новостное агентство Интерфакс');
```

### 8.2 Шаблоны отчетов по умолчанию

```sql
INSERT INTO templates (name, template_type, template_data, is_default) VALUES
('Стандартный отчет по ГОСТ 7.32-2017', 'report_structure', '{
  "sections": [
    {"id": "title_page", "name": "Титульный лист", "required": true},
    {"id": "abstract", "name": "Реферат", "required": true},
    {"id": "contents", "name": "Содержание", "required": true},
    {"id": "introduction", "name": "Введение", "required": true},
    {"id": "market_analysis", "name": "Анализ рынка", "required": true},
    {"id": "regional_analysis", "name": "Региональный анализ", "required": true},
    {"id": "competitor_analysis", "name": "Конкурентный анализ", "required": true},
    {"id": "trend_analysis", "name": "Анализ трендов", "required": true},
    {"id": "conclusion", "name": "Заключение", "required": true},
    {"id": "references", "name": "Список использованных источников", "required": true},
    {"id": "appendices", "name": "Приложения", "required": false}
  ]
}'::jsonb, true);
```

## 9. Миграции

Для управления миграциями БД рекомендуется использовать **Alembic** (инструмент миграций для SQLAlchemy).

### 9.1 Пример структуры миграций

```
migrations/
├── alembic.ini
├── env.py
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_templates.py
    ├── 003_add_notifications.py
    └── ...
```

## 10. Резервное копирование

### 10.1 Стратегия бэкапов

- **Полный бэкап**: Ежедневно в 02:00 UTC
- **Инкрементальный**: Каждые 6 часов
- **Хранение**: 7 дней локально, 30 дней удаленно

### 10.2 Команды для бэкапа

```bash
# Полный бэкап
pg_dump -U postgres -d marketing_ai -F c -b -v -f backup_$(date +%Y%m%d).dump

# Восстановление
pg_restore -U postgres -d marketing_ai -v backup_20260202.dump
```

---

*Документ подготовлен в рамках Фазы 1 проекта "Искусанный Интеллектом Маркетолух"*
*Дата: 02.02.2026*
