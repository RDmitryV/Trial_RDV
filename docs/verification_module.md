# Модуль верификации источников (Phase 4)

## Обзор

Модуль верификации источников обеспечивает достоверность используемых данных и автоматическую проверку актуальности информации для системы "Искусанный Интеллектом Маркетолух".

## Основные компоненты

### 1. Система оценки надежности (Reliability Assessor)

Оценивает надежность источников данных на основе множества факторов:

- **Репутация домена**: Проверка против списка доверенных источников
- **Исторические показатели**: Статистика успешных/неудачных запросов
- **Свежесть данных**: Давность последнего обновления
- **Качество контента**: Анализ содержимого

#### Оценка надежности (0-1):
- **0.9-1.0** - Отличный (Excellent)
- **0.7-0.89** - Хороший (Good)
- **0.5-0.69** - Приемлемый (Fair)
- **0.3-0.49** - Низкий (Poor)
- **0.0-0.29** - Ненадежный (Unreliable)

#### Белые/черные списки:
- **Доверенные источники**: Официальные государственные сайты, академические ресурсы
- **Заблокированные источники**: Ресурсы с подтвержденной недостоверной информацией

### 2. Проверка актуальности (Freshness Checker)

Автоматически определяет и проверяет актуальность данных:

- **Извлечение даты публикации**: Из метаданных и содержимого
- **Категоризация по свежести**: Разные пороги для разных типов контента
- **Автоматические предупреждения**: Флагирование устаревших данных

#### Пороги актуальности:
- **Рыночные данные**: 30 дней
- **Новости**: 90 дней
- **Статистика**: 365 дней
- **Исследования**: 730 дней
- **Общий контент**: 180 дней

### 3. Cross-validation (Перекрестная проверка)

Сопоставляет данные из разных источников для выявления противоречий:

- **Сравнение содержимого**: Анализ схожести между источниками
- **Выявление противоречий**: Автоматическое обнаружение несоответствий
- **Консенсусное значение**: Определение наиболее вероятного значения
- **Флагирование спорных данных**: Пометка данных с низким согласованием

#### Порог схожести:
- По умолчанию: 0.7 (70% схожести для считания источников совпадающими)

### 4. Фактчекинг (Fact Checker)

Проверяет фактические утверждения и цитаты:

- **Извлечение утверждений**: Числовые данные, статистика
- **Проверка ссылок**: Валидация URL и доступности
- **Извлечение статистики**: Проценты, денежные суммы, годовые данные
- **Верификация через официальные источники**: (в разработке)

#### Паттерны для извлечения:
- Числовые утверждения (проценты, суммы)
- Годовые статистические данные
- Ссылки и цитаты

## API Endpoints

### Верификация источника
```http
POST /api/v1/verification/sources/{source_id}/verify
```

**Параметры:**
- `source_id` (UUID) - ID источника
- `perform_full_check` (bool) - Полная проверка (по умолчанию true)

**Ответ:**
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "status": "verified",
  "reliability_rating": "good",
  "reliability_score": 0.75,
  "is_outdated": false,
  "fact_check_performed": true,
  "fact_check_passed": true,
  "verified_at": "2024-01-15T10:30:00",
  "issues_found": []
}
```

### Верификация данных
```http
POST /api/v1/verification/data/{collected_data_id}/verify
```

**Параметры:**
- `collected_data_id` (UUID) - ID собранных данных
- `perform_cross_validation` (bool) - Перекрестная проверка
- `perform_fact_check` (bool) - Фактчекинг

**Ответ:**
```json
{
  "collected_data_id": "uuid",
  "source_verification": { ... },
  "freshness": {
    "is_fresh": true,
    "days_old": 5,
    "threshold_days": 90
  },
  "cross_validation": {
    "is_validated": true,
    "confidence_score": 0.85,
    "matching_sources": 3,
    "contradicting_sources": 0
  },
  "fact_check": { ... },
  "overall_assessment": {
    "reliability": "high",
    "is_trustworthy": true,
    "confidence_level": "high"
  }
}
```

### Управление доверенными источниками
```http
POST /api/v1/verification/trusted-sources
GET /api/v1/verification/trusted-sources
```

### Управление заблокированными источниками
```http
POST /api/v1/verification/blocked-sources
GET /api/v1/verification/blocked-sources
```

### Отчет о верификации
```http
GET /api/v1/verification/report?source_id={uuid}
GET /api/v1/verification/report?collected_data_id={uuid}
```

## Использование в коде

### Python (Backend)

```python
from app.services.verification import VerificationService

# Инициализация сервиса
service = VerificationService(db_session)

# Верификация источника
verification = await service.verify_source(data_source)

# Верификация данных
result = await service.verify_collected_data(
    collected_data,
    perform_cross_validation=True,
    perform_fact_check=True
)

# Получение отчета
report = await service.get_verification_report(
    source_id=str(source.id)
)
```

### Добавление доверенного источника

```python
from app.services.verification import ReliabilityAssessor

assessor = ReliabilityAssessor(db_session)

trusted_source = await assessor.add_trusted_source(
    domain="rosstat.gov.ru",
    name="Росстат",
    trust_score=0.95,
    category="statistics",
    is_official=True
)
```

### Блокировка источника

```python
blocked_source = await assessor.block_source(
    domain="unreliable-news.com",
    reason="Множественные провалы фактчекинга",
    is_permanent=True
)
```

## Модели данных

### SourceVerification
Результаты верификации источника:
- Статус верификации
- Оценка надежности
- Результаты фактчекинга
- Обнаруженные проблемы

### TrustedSource
Белый список доверенных источников:
- Домен
- Оценка доверия (0-1)
- Категория
- Флаг официального источника

### BlockedSource
Черный список ненадежных источников:
- Домен
- Причина блокировки
- Флаг постоянной блокировки

### DataValidation
Результаты перекрестной проверки:
- Количество совпадающих/противоречащих источников
- Оценка уверенности
- Процент согласованности
- Консенсусное значение

## База данных

### Миграция
Файл миграции: `backend/alembic/versions/001_add_source_verification_tables.py`

Для применения миграции:
```bash
cd backend
alembic upgrade head
```

### Таблицы
- `source_verifications` - результаты верификации источников
- `trusted_sources` - доверенные источники
- `blocked_sources` - заблокированные источники
- `data_validations` - результаты валидации данных

## Тестирование

Тесты находятся в `backend/tests/test_verification.py`

Запуск тестов:
```bash
cd backend
pytest tests/test_verification.py -v
```

### Покрытие тестами:
- Оценка надежности источников
- Управление доверенными/заблокированными источниками
- Проверка свежести данных
- Перекрестная валидация
- Фактчекинг
- Полный workflow верификации

## Интеграция с другими модулями

### Модуль сбора данных
Автоматическая верификация при сборе новых данных.

### Аналитический движок
Использование только проверенных данных для анализа.

### Генератор отчетов
Включение информации о верификации в отчеты.

## Конфигурация

### Пороги свежести
Настройка в `FreshnessChecker`:
```python
checker = FreshnessChecker(db_session)
checker.set_freshness_threshold("market_data", 30)  # 30 дней
```

### Порог схожести для cross-validation
Настройка в `CrossValidator`:
```python
validator = CrossValidator(db_session)
validator.set_similarity_threshold(0.7)  # 70%
```

## Дальнейшее развитие

### Планируемые улучшения:
1. Интеграция с внешними фактчекинговыми API
2. Машинное обучение для улучшения оценки надежности
3. Автоматическое обновление устаревших данных
4. Расширенный NLP для извлечения утверждений
5. Интеграция с официальными API статистических служб

## Примеры использования

### Пример 1: Верификация источника новостей
```python
# Создание источника
news_source = DataSource(
    name="Коммерсантъ",
    source_type=SourceType.NEWS,
    url="https://www.kommersant.ru",
    category="news"
)
db.add(news_source)
await db.commit()

# Верификация
verification = await service.verify_source(news_source)
print(f"Надежность: {verification.reliability_rating}")
print(f"Оценка: {verification.reliability_score}")
```

### Пример 2: Перекрестная проверка рыночных данных
```python
# Сбор данных из нескольких источников
data_list = await collect_market_data_from_sources()

# Верификация с cross-validation
for data in data_list:
    result = await service.verify_collected_data(
        data,
        perform_cross_validation=True
    )

    if result["cross_validation"]["agreement_percentage"] < 50:
        print(f"Внимание: низкое согласование источников")
```

## Поддержка

Для вопросов и предложений:
- GitHub Issues: https://github.com/RDmitryV/Trial_RDV/issues
- Документация: https://github.com/RDmitryV/Trial_RDV/wiki
