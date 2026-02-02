# Агентская логика для автономного проведения исследований

## Обзор

Система включает автономного AI-агента, который самостоятельно проводит маркетинговые исследования, принимая решения о следующих шагах на основе паттерна ReAct (Reasoning-Action-Observation).

## Архитектура

### Паттерн ReAct

Агент работает по циклу:

1. **Reasoning (Рассуждение)**: Анализ текущего состояния исследования
2. **Action (Действие)**: Выбор и выполнение следующего действия (поиск, парсинг, анализ)
3. **Observation (Наблюдение)**: Обработка результата
4. **Повторение** до завершения исследования

### Компоненты

#### ResearchAgent

Основной класс агента, который управляет циклом ReAct:

```python
from app.services.agent import ResearchAgent
from app.core.database import get_db

# Создание агента
agent = ResearchAgent(
    db=db_session,
    llm_provider="openai",  # или "anthropic"
    progress_callback=my_callback,  # опционально
)

# Запуск автономного исследования
results = await agent.run(research_object)
```

#### Инструменты агента (Tools)

Агент имеет доступ к следующим инструментам:

1. **search_web(query)** - Поиск информации в интернете
   - Использует DuckDuckGo для поиска
   - Поддерживает различные типы поиска (общий, новости, данные рынка)

2. **parse_url(url)** - Парсинг веб-страницы
   - Извлекает контент с указанного URL
   - Очищает и форматирует данные

3. **search_companies(industry, region)** - Поиск компаний
   - Находит конкурентов в отрасли
   - Фильтрует по региону

4. **get_statistics(metric, region)** - Получение статистики
   - Интегрируется с API статистических служб
   - Предоставляет количественные данные

5. **analyze_sentiment(text)** - Анализ тональности
   - Определяет sentiment текста
   - Полезно для анализа отзывов и новостей

6. **save_finding(data)** - Сохранение находки
   - Сохраняет важные инсайты в базу данных
   - Автоматически категоризирует данные

## API Endpoints

### Запуск агентского исследования

```http
POST /api/v1/researches/{research_id}/run-agent
```

Запускает автономное исследование для указанного research.

**Параметры:**
- `research_id` (path) - ID исследования

**Ответ:**
```json
{
  "id": "uuid",
  "title": "Название исследования",
  "status": "collecting_data",
  ...
}
```

**Примечание:** Исследование выполняется в фоновом режиме. Для отслеживания прогресса используйте WebSocket.

### WebSocket для отслеживания прогресса

```
ws://localhost:8000/api/v1/researches/ws/{research_id}
```

Подключитесь к этому endpoint для получения обновлений в реальном времени.

**Пример сообщений:**

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "message": "Step 1/20: Reasoning...",
  "state": {
    "research_id": "uuid",
    "step_count": 1,
    "findings_count": 0,
    "completed_subtasks": [],
    "pending_subtasks": ["Task 1", "Task 2", ...],
    "is_complete": false
  }
}
```

```json
{
  "type": "completed",
  "timestamp": "2024-01-01T12:10:00",
  "results": {
    "status": "completed",
    "steps_taken": 15,
    "findings_count": 25,
    "report": "Полный текст отчета..."
  }
}
```

## Примеры использования

### Python клиент

```python
import asyncio
import websockets
import json
import requests

# 1. Создать исследование
response = requests.post(
    "http://localhost:8000/api/v1/researches/",
    json={
        "title": "Анализ рынка IT в России",
        "product_description": "Облачное решение для бизнеса",
        "industry": "IT",
        "region": "Russia",
        "research_type": "market"
    },
    headers={"Authorization": f"Bearer {token}"}
)
research_id = response.json()["id"]

# 2. Запустить агента
response = requests.post(
    f"http://localhost:8000/api/v1/researches/{research_id}/run-agent",
    headers={"Authorization": f"Bearer {token}"}
)

# 3. Подключиться к WebSocket для отслеживания прогресса
async def track_progress():
    uri = f"ws://localhost:8000/api/v1/researches/ws/{research_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data.get("type") == "completed":
                print("Исследование завершено!")
                print(f"Отчет: {data['results']['report']}")
                break
            else:
                print(f"Прогресс: {data.get('message', 'Обработка...')}")

asyncio.run(track_progress())
```

### JavaScript/TypeScript клиент

```typescript
// 1. Создать исследование
const research = await fetch('/api/v1/researches/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: 'Анализ рынка IT в России',
    product_description: 'Облачное решение для бизнеса',
    industry: 'IT',
    region: 'Russia',
    research_type: 'market'
  })
}).then(r => r.json());

// 2. Запустить агента
await fetch(`/api/v1/researches/${research.id}/run-agent`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});

// 3. Подключиться к WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/v1/researches/ws/${research.id}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'completed') {
    console.log('Исследование завершено!');
    console.log('Отчет:', data.results.report);
    ws.close();
  } else {
    console.log('Прогресс:', data.message);
    console.log('Состояние:', data.state);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Отправить ping для поддержания соединения
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

## Настройка

### Переменные окружения

```bash
# LLM провайдер
DEFAULT_LLM_PROVIDER=openai  # или anthropic

# API ключи
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Redis для WebSocket (опционально)
REDIS_URL=redis://localhost:6379
```

### Параметры агента

Можно настроить поведение агента:

```python
# В app/services/agent/research_agent.py

class AgentState:
    def __init__(self, research: Research):
        self.max_steps = 20  # Максимальное количество шагов
        # ...
```

## Мониторинг и логирование

Агент автоматически логирует свои действия:

```python
# Добавить свой обработчик прогресса
async def custom_progress_handler(data):
    print(f"[{data['timestamp']}] {data['message']}")

    # Сохранить в базу данных
    await save_to_monitoring_db(data)

    # Отправить уведомление
    await send_notification(data)

agent = ResearchAgent(
    db=db,
    progress_callback=custom_progress_handler
)
```

## Расширение функциональности

### Добавление нового инструмента

1. Создать класс инструмента в `app/services/agent/tools.py`:

```python
class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Description of what this tool does"
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Реализация инструмента
        return {"success": True, "data": "result"}

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                }
            },
            "required": ["param1"]
        }
```

2. Зарегистрировать в `ResearchAgent._init_tools()`:

```python
def _init_tools(self):
    # ... существующие инструменты
    self.tools["my_custom_tool"] = MyCustomTool()
```

## Тестирование

Запуск тестов:

```bash
# Все тесты агента
pytest backend/tests/test_agent.py -v

# Конкретный тест
pytest backend/tests/test_agent.py::TestResearchAgent::test_agent_initialization -v

# С покрытием кода
pytest backend/tests/test_agent.py --cov=app.services.agent --cov-report=html
```

## Производительность

### Оптимизация

1. **Параллельное выполнение**: Агент использует `asyncio` для асинхронного выполнения операций
2. **Кэширование**: Результаты поиска кэшируются в Redis (если настроен)
3. **Rate limiting**: Автоматические задержки между запросами к внешним API

### Ограничения

- Максимум 20 шагов по умолчанию
- Тайм-аут на веб-запросы: 30 секунд
- Максимальный размер контента для анализа: 2000 символов на шаг

## Troubleshooting

### Агент не запускается

1. Проверьте API ключи:
   ```bash
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. Проверьте статус исследования:
   ```bash
   # Исследование должно быть в статусе "created" или "failed"
   ```

3. Проверьте логи:
   ```bash
   tail -f logs/agent.log
   ```

### WebSocket не подключается

1. Проверьте CORS настройки в `app/core/config.py`
2. Убедитесь, что используете правильный протокол (ws:// или wss://)
3. Проверьте файрволл

### Медленная работа

1. Увеличьте тайм-ауты в `web_search_service.py`
2. Уменьшите количество результатов поиска
3. Используйте более быстрый LLM (например, GPT-3.5 вместо GPT-4)

## Дополнительные ресурсы

- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
