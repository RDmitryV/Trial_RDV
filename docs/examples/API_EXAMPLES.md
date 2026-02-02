# Примеры использования API

Данное руководство содержит практические примеры работы с REST API системы "Искусанный Интеллектом Маркетолух".

## 📋 Содержание

- [Аутентификация](#аутентификация)
- [Управление исследованиями](#управление-исследованиями)
- [Работа с отчетами](#работа-с-отчетами)
- [Управление пользователями](#управление-пользователями)
- [Обработка ошибок](#обработка-ошибок)

## 🔐 Аутентификация

### Регистрация нового пользователя

```bash
curl -X POST https://api.marketoluh.ru/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Иван Петров"
  }'
```

**Ответ (201 Created):**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "full_name": "Иван Петров",
  "is_active": false,
  "created_at": "2026-02-02T10:00:00Z"
}
```

### Вход в систему

```bash
curl -X POST https://api.marketoluh.ru/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePassword123!"
```

**Ответ (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Использование токена:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET https://api.marketoluh.ru/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

### Обновление токена

```bash
curl -X POST https://api.marketoluh.ru/v1/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Управление исследованиями

### Создание нового исследования

```bash
curl -X POST https://api.marketoluh.ru/v1/researches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Анализ рынка доставки здоровой еды",
    "product_description": "Мобильное приложение для заказа и доставки готовых блюд правильного питания с подсчетом калорий и персональными рекомендациями от нутрициолога",
    "industry": "food_delivery",
    "region": "moscow",
    "target_audience": {
      "age_min": 25,
      "age_max": 40,
      "interests": ["health", "fitness", "nutrition"],
      "income_level": "middle_high"
    },
    "competitors": [
      "Delivery Club (раздел здоровое питание)",
      "Grow Food",
      "Just For You"
    ],
    "budget": {
      "min": 500000,
      "max": 2000000,
      "currency": "RUB"
    }
  }'
```

**Ответ (201 Created):**
```json
{
  "id": "research-uuid",
  "title": "Анализ рынка доставки здоровой еды",
  "status": "pending",
  "created_at": "2026-02-02T10:00:00Z",
  "estimated_completion": "2026-02-02T10:05:00Z"
}
```

### Получение списка исследований

```bash
# Все исследования
curl -X GET https://api.marketoluh.ru/v1/researches \
  -H "Authorization: Bearer $TOKEN"

# С фильтрацией
curl -X GET "https://api.marketoluh.ru/v1/researches?status=completed&limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "total": 25,
  "items": [
    {
      "id": "research-uuid-1",
      "title": "Анализ рынка доставки здоровой еды",
      "status": "completed",
      "industry": "food_delivery",
      "region": "moscow",
      "created_at": "2026-02-01T10:00:00Z",
      "completed_at": "2026-02-01T10:04:32Z"
    },
    {
      "id": "research-uuid-2",
      "title": "Фитнес-приложение для iOS",
      "status": "processing",
      "industry": "mobile_apps",
      "region": "russia",
      "created_at": "2026-02-02T09:30:00Z",
      "progress": 45
    }
  ]
}
```

### Получение конкретного исследования

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": "research-uuid",
  "title": "Анализ рынка доставки здоровой еды",
  "status": "completed",
  "product_description": "...",
  "industry": "food_delivery",
  "region": "moscow",
  "target_audience": {...},
  "competitors": [...],
  "budget": {...},
  "results": {
    "market_size": 85000000000,
    "market_growth": 15.5,
    "competition_level": "high",
    "entry_barriers": "medium",
    "trends": [
      "Рост спроса на здоровое питание",
      "Увеличение доли онлайн-заказов",
      "Персонализация питания"
    ]
  },
  "created_at": "2026-02-01T10:00:00Z",
  "completed_at": "2026-02-01T10:04:32Z"
}
```

### Проверка статуса исследования

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid/status \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": "research-uuid",
  "status": "processing",
  "progress": 75,
  "current_stage": "competitor_analysis",
  "stages": [
    {"name": "data_collection", "status": "completed"},
    {"name": "market_analysis", "status": "completed"},
    {"name": "competitor_analysis", "status": "processing"},
    {"name": "trend_analysis", "status": "pending"},
    {"name": "report_generation", "status": "pending"}
  ],
  "estimated_completion": "2026-02-02T10:05:00Z"
}
```

### Удаление исследования

```bash
curl -X DELETE https://api.marketoluh.ru/v1/researches/research-uuid \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (204 No Content)**

## 📄 Работа с отчетами

### Скачивание отчета в PDF

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid/report/pdf \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf
```

### Скачивание отчета в DOCX

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid/report/docx \
  -H "Authorization: Bearer $TOKEN" \
  -o report.docx
```

### Получение метаданных отчета

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid/report/metadata \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "research_id": "research-uuid",
  "title": "Анализ рынка доставки здоровой еды",
  "pages": 42,
  "sections": [
    {"name": "Введение", "pages": 3},
    {"name": "Анализ рынка", "pages": 12},
    {"name": "Конкурентный анализ", "pages": 10},
    {"name": "Анализ трендов", "pages": 8},
    {"name": "Заключение", "pages": 5},
    {"name": "Приложения", "pages": 4}
  ],
  "sources_count": 48,
  "charts_count": 15,
  "tables_count": 8,
  "file_size_pdf": 2458624,
  "file_size_docx": 1856432,
  "generated_at": "2026-02-01T10:04:32Z"
}
```

### Получение превью отчета

```bash
curl -X GET https://api.marketoluh.ru/v1/researches/research-uuid/report/preview \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "summary": "Рынок доставки здоровой еды в Москве...",
  "key_findings": [
    "Размер рынка: 85 млрд руб.",
    "Темпы роста: 15.5% в год",
    "Основные конкуренты: Delivery Club, Grow Food, Just For You"
  ],
  "recommendations": [
    "Фокус на персонализации",
    "Интеграция с фитнес-трекерами",
    "Премиум сегмент"
  ]
}
```

## 👤 Управление пользователями

### Получение информации о текущем пользователе

```bash
curl -X GET https://api.marketoluh.ru/v1/me \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "Иван Петров",
  "subscription": {
    "plan": "pro",
    "status": "active",
    "researches_limit": 100,
    "researches_used": 15,
    "expires_at": "2026-03-01T00:00:00Z"
  },
  "created_at": "2026-01-01T10:00:00Z"
}
```

### Обновление профиля

```bash
curl -X PATCH https://api.marketoluh.ru/v1/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иван Александрович Петров",
    "company": "ООО Стартап",
    "position": "Маркетолог"
  }'
```

### Изменение пароля

```bash
curl -X POST https://api.marketoluh.ru/v1/me/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!"
  }'
```

## 🔧 Дополнительные примеры

### Пагинация

```bash
# Первая страница (10 элементов)
curl -X GET "https://api.marketoluh.ru/v1/researches?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Вторая страница
curl -X GET "https://api.marketoluh.ru/v1/researches?limit=10&offset=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Сортировка

```bash
# По дате создания (новые первые)
curl -X GET "https://api.marketoluh.ru/v1/researches?sort=-created_at" \
  -H "Authorization: Bearer $TOKEN"

# По названию (А-Я)
curl -X GET "https://api.marketoluh.ru/v1/researches?sort=title" \
  -H "Authorization: Bearer $TOKEN"
```

### Поиск

```bash
# Полнотекстовый поиск
curl -X GET "https://api.marketoluh.ru/v1/researches?search=доставка" \
  -H "Authorization: Bearer $TOKEN"
```

### Batch операции

```bash
# Удаление нескольких исследований
curl -X DELETE https://api.marketoluh.ru/v1/researches/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["uuid-1", "uuid-2", "uuid-3"]
  }'
```

## ⚠️ Обработка ошибок

### Общая структура ошибки

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Человекочитаемое описание ошибки",
    "details": {
      "field": "Дополнительная информация"
    }
  }
}
```

### Типичные ошибки

#### 400 Bad Request - Невалидные данные

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации",
    "details": {
      "product_description": "Минимальная длина 100 символов"
    }
  }
}
```

#### 401 Unauthorized - Не авторизован

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Требуется авторизация"
  }
}
```

#### 403 Forbidden - Доступ запрещен

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Недостаточно прав"
  }
}
```

#### 404 Not Found - Ресурс не найден

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Исследование не найдено"
  }
}
```

#### 429 Too Many Requests - Превышен лимит

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Превышен лимит запросов",
    "details": {
      "limit": 100,
      "reset_at": "2026-02-02T11:00:00Z"
    }
  }
}
```

#### 500 Internal Server Error - Внутренняя ошибка

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Внутренняя ошибка сервера",
    "details": {
      "request_id": "req-uuid"
    }
  }
}
```

### Обработка ошибок (Python)

```python
import requests

def create_research(data, token):
    try:
        response = requests.post(
            "https://api.marketoluh.ru/v1/researches",
            json=data,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        error = e.response.json()["error"]

        if e.response.status_code == 400:
            print(f"Ошибка валидации: {error['message']}")
            print(f"Детали: {error.get('details', {})}")
        elif e.response.status_code == 401:
            print("Необходимо авторизоваться")
        elif e.response.status_code == 429:
            print("Превышен лимит запросов")
            reset_at = error['details']['reset_at']
            print(f"Повторите после {reset_at}")
        else:
            print(f"Ошибка: {error['message']}")

        return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {e}")
        return None
```

## 📚 Полная документация

Интерактивная документация API доступна по адресу:
- Swagger UI: https://api.marketoluh.ru/docs
- ReDoc: https://api.marketoluh.ru/redoc

## 💡 Советы

1. **Используйте токены с ограниченным сроком жизни**
2. **Кэшируйте результаты запросов**
3. **Обрабатывайте rate limits**
4. **Логируйте request_id для отладки**
5. **Используйте версионирование API (v1, v2, ...)**

---

**Версия API:** 1.0.0
**Последнее обновление:** 2026-02-02
