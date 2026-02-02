# REST API Спецификация

## 1. Общая информация

### 1.1 Базовый URL
```
Development: http://localhost:8000/api/v1
Production: https://api.marketoluh.ai/api/v1
```

### 1.2 Аутентификация
- **Тип**: JWT (JSON Web Tokens)
- **Header**: `Authorization: Bearer <access_token>`
- **Access Token**: Срок жизни 15 минут
- **Refresh Token**: Срок жизни 7 дней

### 1.3 Формат ответов
Все ответы возвращаются в формате JSON.

#### Успешный ответ:
```json
{
  "success": true,
  "data": { ... }
}
```

#### Ответ с ошибкой:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  }
}
```

### 1.4 HTTP Status Codes
- `200 OK`: Успешный запрос
- `201 Created`: Ресурс создан
- `204 No Content`: Успешно, нет содержимого
- `400 Bad Request`: Ошибка валидации
- `401 Unauthorized`: Не авторизован
- `403 Forbidden`: Доступ запрещен
- `404 Not Found`: Ресурс не найден
- `422 Unprocessable Entity`: Ошибка валидации данных
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Внутренняя ошибка сервера

## 2. Authentication Endpoints

### 2.1 POST /auth/register
Регистрация нового пользователя.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Иван Иванов",
  "company": "ООО Компания" (optional)
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "Иван Иванов",
      "role": "user",
      "is_verified": false
    },
    "message": "Регистрация успешна. Проверьте email для подтверждения."
  }
}
```

### 2.2 POST /auth/login
Вход в систему.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "Иван Иванов",
      "role": "user"
    }
  }
}
```

### 2.3 POST /auth/refresh
Обновление access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

### 2.4 POST /auth/logout
Выход из системы (отзыв refresh token).

**Headers:** `Authorization: Bearer <access_token>`

**Response (204):** No Content

### 2.5 POST /auth/verify-email
Подтверждение email (после регистрации).

**Request:**
```json
{
  "token": "verification_token_from_email"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Email успешно подтвержден"
  }
}
```

### 2.6 POST /auth/forgot-password
Запрос на восстановление пароля.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Инструкции по восстановлению пароля отправлены на email"
  }
}
```

## 3. Research Endpoints

### 3.1 POST /researches
Создание нового исследования.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "title": "Исследование рынка доставки здоровой еды в Москве",
  "product_description": "Мобильное приложение для доставки здоровой еды",
  "industry": "Общественное питание",
  "region": "Москва и Московская область",
  "target_audience": "Молодые профессионалы 25-40 лет",
  "budget_range": "средний",
  "additional_params": {
    "competitors_to_analyze": ["Delivery Club", "СберМаркет"],
    "focus_areas": ["market_size", "competitors", "trends"]
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "research": {
      "id": "uuid",
      "title": "Исследование рынка доставки здоровой еды в Москве",
      "status": "pending",
      "progress_percent": 0,
      "created_at": "2026-02-02T10:00:00Z",
      "estimated_completion_time": "2026-02-02T10:15:00Z"
    }
  }
}
```

### 3.2 GET /researches
Получение списка исследований пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status` (optional): Filter by status
- `page` (optional, default=1): Page number
- `limit` (optional, default=20): Items per page
- `sort_by` (optional, default=created_at): Sort field
- `order` (optional, default=desc): Sort order (asc/desc)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "researches": [
      {
        "id": "uuid",
        "title": "Исследование рынка...",
        "status": "completed",
        "progress_percent": 100,
        "created_at": "2026-02-02T10:00:00Z",
        "completed_at": "2026-02-02T10:12:00Z",
        "reports_count": 2
      }
    ],
    "pagination": {
      "total": 15,
      "page": 1,
      "limit": 20,
      "pages": 1
    }
  }
}
```

### 3.3 GET /researches/{research_id}
Получение детальной информации об исследовании.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "research": {
      "id": "uuid",
      "title": "Исследование рынка...",
      "status": "completed",
      "progress_percent": 100,
      "product_description": "Мобильное приложение...",
      "industry": "Общественное питание",
      "region": "Москва и Московская область",
      "target_audience": "Молодые профессионалы 25-40 лет",
      "created_at": "2026-02-02T10:00:00Z",
      "completed_at": "2026-02-02T10:12:00Z",
      "summary_data": {
        "market_size": "15 млрд руб.",
        "key_competitors": ["Delivery Club", "СберМаркет"],
        "growth_rate": "25% год к году"
      },
      "reports": [
        {
          "id": "uuid",
          "format": "pdf",
          "file_url": "https://...",
          "created_at": "2026-02-02T10:12:00Z"
        }
      ]
    }
  }
}
```

### 3.4 DELETE /researches/{research_id}
Удаление исследования.

**Headers:** `Authorization: Bearer <access_token>`

**Response (204):** No Content

### 3.5 GET /researches/{research_id}/status
Получение статуса выполнения исследования (для polling).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "analyzing",
    "progress_percent": 65,
    "current_stage": "Анализ конкурентов",
    "estimated_completion_time": "2026-02-02T10:15:00Z",
    "stages": [
      {"name": "Сбор данных", "status": "completed"},
      {"name": "Анализ рынка", "status": "completed"},
      {"name": "Анализ конкурентов", "status": "in_progress"},
      {"name": "Генерация отчета", "status": "pending"}
    ]
  }
}
```

## 4. Report Endpoints

### 4.1 GET /reports
Получение списка отчетов пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `research_id` (optional): Filter by research
- `format` (optional): Filter by format
- `page`, `limit`, `sort_by`, `order`: Same as researches

**Response (200):**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "uuid",
        "research_id": "uuid",
        "research_title": "Исследование рынка...",
        "format": "pdf",
        "file_url": "https://...",
        "file_size_bytes": 2458624,
        "page_count": 45,
        "created_at": "2026-02-02T10:12:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

### 4.2 GET /reports/{report_id}
Получение информации об отчете.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "report": {
      "id": "uuid",
      "research_id": "uuid",
      "title": "Маркетинговое исследование...",
      "format": "pdf",
      "version": 1,
      "file_url": "https://storage.../report.pdf",
      "file_size_bytes": 2458624,
      "page_count": 45,
      "word_count": 8500,
      "table_count": 12,
      "figure_count": 15,
      "source_count": 34,
      "gost_compliance_score": 0.98,
      "structure_data": {
        "sections": [
          {"name": "Введение", "pages": "3-5"},
          {"name": "Анализ рынка", "pages": "6-18"}
        ]
      },
      "created_at": "2026-02-02T10:12:00Z"
    }
  }
}
```

### 4.3 GET /reports/{report_id}/download
Скачивание отчета.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
- Content-Type: `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="report.pdf"`
- Binary file content

### 4.4 POST /reports/{report_id}/regenerate
Перегенерация отчета (например, в другом формате).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "format": "docx"
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "message": "Отчет поставлен в очередь на генерацию",
    "task_id": "celery_task_id"
  }
}
```

## 5. User Endpoints

### 5.1 GET /users/me
Получение профиля текущего пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "Иван Иванов",
      "company": "ООО Компания",
      "role": "user",
      "is_active": true,
      "is_verified": true,
      "research_quota": 10,
      "researches_used": 3,
      "created_at": "2026-01-15T08:00:00Z",
      "last_login_at": "2026-02-02T09:00:00Z"
    }
  }
}
```

### 5.2 PATCH /users/me
Обновление профиля текущего пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "full_name": "Иван Петрович Иванов",
  "company": "ООО Новая Компания",
  "phone": "+7 (999) 123-45-67"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": { ... }
  }
}
```

### 5.3 POST /users/me/change-password
Изменение пароля.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Пароль успешно изменен"
  }
}
```

### 5.4 GET /users/me/statistics
Получение статистики пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "statistics": {
      "total_researches": 15,
      "completed_researches": 12,
      "in_progress_researches": 2,
      "failed_researches": 1,
      "total_reports": 24,
      "researches_by_month": [
        {"month": "2026-01", "count": 8},
        {"month": "2026-02", "count": 7}
      ],
      "most_researched_industries": [
        {"industry": "Общественное питание", "count": 5},
        {"industry": "E-commerce", "count": 3}
      ],
      "quota_usage": {
        "quota": 10,
        "used": 3,
        "remaining": 7,
        "reset_date": "2026-03-01T00:00:00Z"
      }
    }
  }
}
```

## 6. Admin Endpoints

### 6.1 GET /admin/users
Получение списка всех пользователей (только admin).

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:** `page`, `limit`, `sort_by`, `order`, `role`, `is_active`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "Иван Иванов",
        "role": "user",
        "is_active": true,
        "researches_count": 15,
        "created_at": "2026-01-15T08:00:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

### 6.2 PATCH /admin/users/{user_id}
Обновление пользователя (только admin).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "role": "premium",
  "research_quota": 50,
  "is_active": true
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": { ... }
  }
}
```

### 6.3 GET /admin/statistics
Получение общей статистики системы (только admin).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "statistics": {
      "total_users": 1523,
      "active_users_last_30_days": 456,
      "total_researches": 5432,
      "researches_in_progress": 23,
      "total_reports_generated": 10864,
      "avg_research_time_minutes": 12.5,
      "system_health": {
        "api_uptime": "99.9%",
        "celery_queue_size": 5,
        "avg_response_time_ms": 245
      }
    }
  }
}
```

### 6.4 GET /admin/data-sources
Управление источниками данных (только admin).

**Response (200):**
```json
{
  "success": true,
  "data": {
    "data_sources": [
      {
        "id": "uuid",
        "name": "Росстат",
        "type": "api",
        "reliability_level": 1,
        "is_active": true,
        "last_checked_at": "2026-02-02T05:00:00Z",
        "success_rate": 0.98
      }
    ]
  }
}
```

## 7. Notification Endpoints

### 7.1 GET /notifications
Получение уведомлений пользователя.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `is_read` (optional): Filter by read status
- `type` (optional): Filter by type
- `page`, `limit`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "uuid",
        "type": "research_completed",
        "title": "Исследование завершено",
        "message": "Ваше исследование 'Рынок доставки еды' завершено",
        "is_read": false,
        "related_entity_type": "research",
        "related_entity_id": "uuid",
        "created_at": "2026-02-02T10:12:00Z"
      }
    ],
    "unread_count": 3,
    "pagination": { ... }
  }
}
```

### 7.2 PATCH /notifications/{notification_id}/read
Отметить уведомление как прочитанное.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Уведомление отмечено как прочитанное"
  }
}
```

### 7.3 POST /notifications/mark-all-read
Отметить все уведомления как прочитанные.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "marked_count": 5
  }
}
```

## 8. WebSocket Endpoints

### 8.1 WS /ws/research/{research_id}
WebSocket для получения real-time обновлений о ходе исследования.

**Connection:** `ws://localhost:8000/ws/research/{research_id}?token={access_token}`

**Server Messages:**
```json
{
  "type": "progress_update",
  "data": {
    "progress_percent": 45,
    "current_stage": "Анализ рынка",
    "message": "Обработано 15 из 30 источников данных"
  }
}
```

```json
{
  "type": "stage_completed",
  "data": {
    "stage": "Сбор данных",
    "duration_seconds": 120
  }
}
```

```json
{
  "type": "research_completed",
  "data": {
    "research_id": "uuid",
    "reports": [...]
  }
}
```

```json
{
  "type": "error",
  "data": {
    "error_code": "DATA_COLLECTION_ERROR",
    "message": "Не удалось получить данные из источника X"
  }
}
```

## 9. Rate Limiting

### 9.1 Лимиты для разных ролей

**User (бесплатный)**:
- 100 requests per minute
- 1000 requests per day
- 10 researches per month

**Premium User**:
- 500 requests per minute
- 10000 requests per day
- 50 researches per month

**Admin**:
- No limits

### 9.2 Rate Limit Headers

Каждый ответ содержит заголовки:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643800800
```

### 9.3 Rate Limit Exceeded Response (429)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "details": {
      "retry_after": 30
    }
  }
}
```

## 10. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 422 | Ошибка валидации входных данных |
| UNAUTHORIZED | 401 | Не авторизован |
| FORBIDDEN | 403 | Доступ запрещен |
| NOT_FOUND | 404 | Ресурс не найден |
| RATE_LIMIT_EXCEEDED | 429 | Превышен лимит запросов |
| QUOTA_EXCEEDED | 403 | Превышена месячная квота исследований |
| RESEARCH_IN_PROGRESS | 400 | Исследование уже выполняется |
| INVALID_TOKEN | 401 | Недействительный токен |
| TOKEN_EXPIRED | 401 | Токен истек |
| EMAIL_ALREADY_EXISTS | 400 | Email уже зарегистрирован |
| INVALID_CREDENTIALS | 401 | Неверный email или пароль |
| INTERNAL_ERROR | 500 | Внутренняя ошибка сервера |

---

*Документ подготовлен в рамках Фазы 1 проекта "Искусанный Интеллектом Маркетолух"*
*Дата: 02.02.2026*
