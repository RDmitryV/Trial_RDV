# Технологический стек проекта

## 1. Backend

### 1.1 Core Framework
- **Python 3.11+**: Основной язык программирования
- **FastAPI 0.109+**: Web framework для REST API
  - Высокая производительность (на уровне NodeJS/Go)
  - Автоматическая генерация OpenAPI документации
  - Встроенная валидация через Pydantic
  - Async/await support

### 1.2 Database & ORM
- **PostgreSQL 15+**: Основная реляционная БД
  - JSONB support для гибких данных
  - Full-text search
  - Надежность и масштабируемость
- **SQLAlchemy 2.0+**: ORM для работы с БД
  - Async support
  - Type hints
  - Migration support через Alembic
- **Alembic**: Управление миграциями БД

### 1.3 Caching & Message Queue
- **Redis 7+**:
  - Кэширование данных
  - Session storage
  - Message broker для Celery
  - Rate limiting storage
- **Celery 5.3+**: Асинхронная обработка задач
  - Сбор данных в фоне
  - Генерация отчетов
  - Периодические задачи (Celery Beat)

### 1.4 AI/ML Stack
- **LangChain 0.1+**: Framework для работы с LLM
  - Orchestration агентов
  - Memory management
  - Chain композиция
  - Tool integration
- **OpenAI API (GPT-4)**: Основной LLM
  - Анализ текстов
  - Генерация контента
  - Извлечение инсайтов
- **Anthropic Claude API**: Альтернативный LLM
  - Резервный вариант
  - Specialized tasks
- **spaCy 3.7+**: NLP библиотека
  - Токенизация
  - Named Entity Recognition
  - POS tagging
  - Русский язык support

### 1.5 Data Processing
- **Pandas 2.2+**: Обработка табличных данных
- **NumPy 1.26+**: Численные вычисления
- **Matplotlib 3.8+**: Визуализация данных для отчетов
- **Plotly 5.18+**: Интерактивные графики
- **Seaborn 0.13+**: Статистические визуализации

### 1.6 Web Scraping
- **BeautifulSoup4 4.12+**: Парсинг HTML
- **Scrapy 2.11+**: Framework для скрапинга
  - Middleware support
  - Item pipelines
  - Rate limiting
- **Playwright 1.41+**: Автоматизация браузера
  - JavaScript-рендеренные страницы
  - Dynamic content
- **httpx 0.26+**: Async HTTP client
  - HTTP/2 support
  - Connection pooling

### 1.7 Report Generation
- **python-docx 1.1+**: Генерация DOCX документов
  - Стилизация по ГОСТ
  - Таблицы и изображения
  - Автонумерация
- **ReportLab 4.0+** или **WeasyPrint 60+**: Генерация PDF
  - ReportLab: низкоуровневый контроль
  - WeasyPrint: HTML/CSS to PDF
- **Jinja2 3.1+**: Шаблонизация документов

### 1.8 Authentication & Security
- **python-jose[cryptography] 3.3+**: JWT токены
- **passlib[bcrypt] 1.7+**: Хэширование паролей
- **python-multipart 0.0.6+**: Form data handling

### 1.9 Validation & Configuration
- **Pydantic 2.5+**: Data validation
  - Type checking
  - JSON schema generation
- **pydantic-settings**: Configuration management
- **python-dotenv 1.0+**: Environment variables

### 1.10 Testing
- **pytest 7.4+**: Testing framework
- **pytest-asyncio 0.23+**: Async tests
- **pytest-cov 4.1+**: Code coverage
- **httpx[test]**: API testing
- **Faker 22+**: Test data generation
- **factory-boy 3.3+**: Test fixtures

### 1.11 Code Quality
- **ruff 0.1+**: Fast Python linter & formatter
  - Замена для flake8, black, isort
  - Rust-based, очень быстрый
- **mypy 1.8+**: Static type checker
- **pre-commit 3.6+**: Git hooks

### 1.12 Monitoring & Logging
- **structlog 24.1+**: Structured logging
- **sentry-sdk[fastapi] 1.39+**: Error tracking
- **prometheus-client 0.19+**: Metrics collection
- **opentelemetry**: Distributed tracing (опционально)

## 2. Frontend

### 2.1 Core
- **React 18+**: UI библиотека
  - Concurrent features
  - Automatic batching
  - Hooks
- **TypeScript 5.3+**: Type safety
  - Static typing
  - Better IDE support
  - Refactoring safety

### 2.2 State Management
- **Redux Toolkit 2.0+** или **Zustand 4.4+**:
  - Redux Toolkit: для сложных приложений
  - Zustand: для простых случаев, меньше boilerplate
- **TanStack Query (React Query) 5.17+**: Server state management
  - Caching
  - Background updates
  - Optimistic updates

### 2.3 Routing
- **React Router 6.21+**: Client-side routing
  - Nested routes
  - Lazy loading
  - Route guards

### 2.4 UI Components & Styling
- **Tailwind CSS 3.4+**: Utility-first CSS framework
  - Responsive design
  - Dark mode support
  - JIT compilation
- **shadcn/ui**: Component library
  - Radix UI primitives
  - Customizable
  - Accessible
- **Headless UI**: Unstyled accessible components
- **React Icons 5.0+**: Icon library

### 2.5 Forms & Validation
- **React Hook Form 7.49+**: Form management
  - Performance focused
  - Minimal re-renders
- **Zod 3.22+**: Schema validation
  - TypeScript-first
  - Compose schemas

### 2.6 Data Visualization
- **Recharts 2.10+**: React charting library
  - Composable charts
  - Responsive
- **Chart.js 4.4+** с **react-chartjs-2**: Alternative charting

### 2.7 HTTP Client
- **Axios 1.6+**: HTTP client
  - Interceptors
  - Request/response transformation
  - Automatic JSON handling

### 2.8 Development Tools
- **Vite 5.0+**: Build tool
  - Fast HMR
  - Optimized production builds
  - Plugin ecosystem
- **ESLint 8.56+**: Linting
- **Prettier 3.1+**: Code formatting
- **Vitest 1.2+**: Unit testing
- **Playwright 1.41+**: E2E testing

## 3. DevOps & Infrastructure

### 3.1 Containerization
- **Docker 24+**: Контейнеризация
- **Docker Compose 2.24+**: Локальная разработка
  - Multi-container apps
  - Development environment

### 3.2 CI/CD
- **GitHub Actions**: CI/CD pipeline
  - Automated testing
  - Automated deployments
  - Code quality checks

### 3.3 Orchestration (Production)
- **Kubernetes 1.28+** (опционально): Container orchestration
- **Helm 3+** (опционально): K8s package manager
- **Docker Swarm** (альтернатива): Simpler orchestration

### 3.4 Reverse Proxy & Load Balancing
- **Nginx 1.25+**: Reverse proxy
  - Static file serving
  - Load balancing
  - SSL termination
- **Traefik 2.10+** (альтернатива): Modern HTTP reverse proxy

### 3.5 Monitoring & Observability
- **Prometheus 2.48+**: Metrics collection
- **Grafana 10.2+**: Metrics visualization
  - Dashboards
  - Alerting
- **Sentry**: Error tracking
- **Loki** (опционально): Log aggregation
- **Jaeger** (опционально): Distributed tracing

### 3.6 Infrastructure as Code
- **Terraform 1.7+** (опционально): Infrastructure provisioning
- **Ansible 2.16+** (опционально): Configuration management

## 4. Storage

### 4.1 Object Storage
- **MinIO**: S3-compatible object storage
  - Self-hosted
  - S3 API compatibility
- **AWS S3** (production): Cloud object storage
- **Yandex Object Storage** (альтернатива): Russian cloud provider

### 4.2 File System
- **Local filesystem**: Development
- **NFS/EFS** (production): Shared filesystem

## 5. Third-Party Services

### 5.1 LLM Providers
- **OpenAI API**: Primary LLM
- **Anthropic Claude API**: Secondary LLM

### 5.2 Email
- **SendGrid**: Transactional email
- **AWS SES** (альтернатива): Amazon email service
- **Mailgun** (альтернатива): Email service

### 5.3 Analytics (опционально)
- **Google Analytics**: Web analytics
- **Posthog**: Product analytics (self-hosted option)

### 5.4 Payment (будущее)
- **ЮKassa**: Russian payment gateway
- **Stripe** (опционально): International payments

## 6. Development Tools

### 6.1 Version Control
- **Git**: Version control
- **GitHub**: Code hosting
  - Issues tracking
  - Project boards
  - Actions (CI/CD)
  - Code review

### 6.2 API Development
- **Postman**: API testing
- **Swagger UI**: API documentation
- **Insomnia** (альтернатива): API testing

### 6.3 Database Management
- **pgAdmin 4**: PostgreSQL GUI
- **DBeaver**: Universal database tool
- **Redis Insight**: Redis GUI

### 6.4 IDE/Editors
- **VSCode**: Recommended IDE
  - Python extension
  - TypeScript support
  - Docker extension
- **PyCharm Professional**: Python IDE
- **WebStorm**: JavaScript/TypeScript IDE

## 7. Зависимости проекта

### 7.1 Backend Requirements (requirements.txt)

```txt
# Web Framework
fastapi[all]==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Caching & Queue
redis==5.0.1
celery[redis]==5.3.6
flower==2.0.1

# AI/ML
langchain==0.1.0
openai==1.10.0
anthropic==0.8.1
spacy==3.7.2

# Data Processing
pandas==2.2.0
numpy==1.26.3
matplotlib==3.8.2
plotly==5.18.0
seaborn==0.13.1

# Web Scraping
beautifulsoup4==4.12.3
scrapy==2.11.0
playwright==1.41.0
httpx==0.26.0

# Report Generation
python-docx==1.1.0
reportlab==4.0.9
weasyprint==60.2
Jinja2==3.1.3

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==42.0.0

# Validation & Config
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
faker==22.1.0
factory-boy==3.3.0

# Code Quality
ruff==0.1.14
mypy==1.8.0

# Monitoring
structlog==24.1.0
sentry-sdk[fastapi]==1.39.2
prometheus-client==0.19.0
```

### 7.2 Frontend Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "@reduxjs/toolkit": "^2.0.1",
    "@tanstack/react-query": "^5.17.19",
    "axios": "^1.6.5",
    "zod": "^3.22.4",
    "react-hook-form": "^7.49.3",
    "recharts": "^2.10.4",
    "react-icons": "^5.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12",
    "tailwindcss": "^3.4.1",
    "eslint": "^8.56.0",
    "prettier": "^3.1.1",
    "vitest": "^1.2.0",
    "@playwright/test": "^1.41.0"
  }
}
```

## 8. Обоснование выбора технологий

### 8.1 Почему Python/FastAPI для backend?
- **Экосистема AI/ML**: Лучшая поддержка для работы с LLM
- **FastAPI**: Высокая производительность, автодокументация, async support
- **Data Science**: Pandas, NumPy для обработки данных
- **Rapid Development**: Быстрая разработка и прототипирование

### 8.2 Почему React/TypeScript для frontend?
- **React**: Наиболее популярный UI фреймворк, большая экосистема
- **TypeScript**: Type safety, лучший DX, меньше ошибок
- **Component-based**: Переиспользование компонентов
- **Strong Community**: Множество библиотек и ресурсов

### 8.3 Почему PostgreSQL?
- **Reliability**: Проверенная СУБД с высокой надежностью
- **JSONB**: Гибкость для хранения неструктурированных данных
- **Full-text Search**: Встроенный поиск
- **ACID**: Транзакционная целостность
- **Open Source**: Бесплатная и open-source

### 8.4 Почему LangChain?
- **Abstraction**: Упрощает работу с различными LLM
- **Orchestration**: Композиция агентов и chains
- **Memory**: Встроенное управление контекстом
- **Tools Integration**: Легко расширяется инструментами

## 9. Альтернативные технологии

### 9.1 Backend Alternatives
- **Django**: Более монолитный, больше "batteries included"
- **Flask**: Более легковесный, но требует больше настройки
- **Node.js/NestJS**: Для JavaScript-only команд

### 9.2 Frontend Alternatives
- **Vue.js**: Проще для новичков
- **Svelte**: Меньший bundle size
- **Next.js**: SSR/SSG из коробки

### 9.3 Database Alternatives
- **MongoDB**: NoSQL, более гибкая схема
- **MySQL/MariaDB**: Широко используется
- **TimescaleDB**: Time-series данные

---

*Документ подготовлен в рамках Фазы 1 проекта "Искусанный Интеллектом Маркетолух"*
*Дата: 02.02.2026*
