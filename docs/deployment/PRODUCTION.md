# Production Deployment Guide

Руководство по развертыванию системы "Искусанный Интеллектом Маркетолух" в производственной среде.

## 📋 Содержание

- [Требования](#требования)
- [Архитектура production](#архитектура-production)
- [Подготовка сервера](#подготовка-сервера)
- [Установка зависимостей](#установка-зависимостей)
- [Настройка базы данных](#настройка-базы-данных)
- [Конфигурация приложения](#конфигурация-приложения)
- [Развертывание с Docker](#развертывание-с-docker)
- [Настройка HTTPS](#настройка-https)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Резервное копирование](#резервное-копирование)
- [Обновление системы](#обновление-системы)
- [Troubleshooting](#troubleshooting)

## 💻 Требования

### Минимальные требования

- **ОС**: Ubuntu 20.04 LTS или выше (рекомендуется Ubuntu 22.04 LTS)
- **CPU**: 4 ядра
- **RAM**: 8 GB
- **Диск**: 100 GB SSD
- **Сеть**: 100 Mbps
- **Домен**: с настроенными DNS записями

### Рекомендуемые требования

- **ОС**: Ubuntu 22.04 LTS
- **CPU**: 8+ ядер
- **RAM**: 16+ GB
- **Диск**: 500+ GB SSD
- **Сеть**: 1 Gbps
- **Балансировщик нагрузки**: для высоконагруженных систем

### Программное обеспечение

- Docker 24.0+
- Docker Compose 2.20+
- Nginx (для SSL/TLS терминации)
- Certbot (для Let's Encrypt сертификатов)

## 🏗️ Архитектура production

```
┌──────────────────────────────────────────────────┐
│              Load Balancer (optional)             │
└───────────────────┬──────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────┐
│                   Nginx                           │
│           (SSL/TLS Termination)                   │
└───────────┬───────────────────┬──────────────────┘
            │                   │
            │ (Frontend)        │ (API)
            │                   │
┌───────────▼─────────┐  ┌──────▼──────────────────┐
│   Frontend          │  │   Backend API           │
│   (Vue.js + Nginx)  │  │   (FastAPI + Uvicorn)   │
└─────────────────────┘  └──────┬──────────────────┘
                                │
                         ┌──────▼──────────────────┐
                         │   Celery Workers        │
                         │   (Background Tasks)    │
                         └──────┬──────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
┌───────────▼─────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   PostgreSQL        │  │   Redis     │  │   Object        │
│   (Primary DB)      │  │   (Cache)   │  │   Storage       │
└─────────────────────┘  └─────────────┘  └─────────────────┘
```

## 🔧 Подготовка сервера

### 1. Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget git vim
```

### 2. Настройка firewall

```bash
# Установка UFW
sudo apt install -y ufw

# Разрешение SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение firewall
sudo ufw enable
sudo ufw status
```

### 3. Настройка swap (если RAM < 16 GB)

```bash
# Создание swap файла 4 GB
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Автоматическое монтирование при загрузке
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. Создание пользователя для приложения

```bash
# Создание пользователя
sudo adduser --disabled-password --gecos "" marketoluh

# Добавление в группу docker (после установки Docker)
sudo usermod -aG docker marketoluh
```

## 🐳 Установка зависимостей

### 1. Установка Docker

```bash
# Удаление старых версий
sudo apt remove docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Проверка установки
docker --version
docker compose version
```

### 2. Установка Nginx

```bash
sudo apt install -y nginx

# Запуск и автозагрузка
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 3. Установка Certbot (для SSL)

```bash
sudo apt install -y certbot python3-certbot-nginx
```

## 🗄️ Настройка базы данных

### Вариант 1: PostgreSQL в Docker (рекомендуется)

Уже настроено в docker-compose.yml

### Вариант 2: PostgreSQL на хосте

```bash
# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres psql
```

```sql
CREATE DATABASE marketoluh_db;
CREATE USER marketoluh_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE marketoluh_db TO marketoluh_user;
\q
```

```bash
# Настройка удаленного доступа (если требуется)
sudo vim /etc/postgresql/14/main/postgresql.conf
# Раскомментировать: listen_addresses = 'localhost'

sudo vim /etc/postgresql/14/main/pg_hba.conf
# Добавить: host    marketoluh_db    marketoluh_user    172.18.0.0/16    md5

sudo systemctl restart postgresql
```

## ⚙️ Конфигурация приложения

### 1. Клонирование репозитория

```bash
# Переход в домашнюю директорию пользователя
sudo su - marketoluh
cd ~

# Клонирование
git clone https://github.com/RDmitryV/Trial_RDV.git
cd Trial_RDV
```

### 2. Создание production конфигурации

```bash
cp .env.example .env.production
vim .env.production
```

**Содержимое .env.production:**

```bash
# Application
APP_ENV=production
APP_NAME="Искусанный Интеллектом Маркетолух"
APP_VERSION=1.0.0
DEBUG=false

# Security
SECRET_KEY=your_very_long_random_secret_key_here_min_50_chars
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database
DATABASE_URL=postgresql://marketoluh_user:your_secure_password@db:5432/marketoluh_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://redis:6379/0

# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
# или
ANTHROPIC_API_KEY=your_anthropic_api_key

# Email (для уведомлений)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourdomain.com

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# S3 Storage (optional)
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=marketoluh-reports

# Monitoring
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### 3. Генерация SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 🚀 Развертывание с Docker

### 1. Создание production docker-compose

```bash
cp docker-compose.yml docker-compose.prod.yml
vim docker-compose.prod.yml
```

**Изменения для production:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A app.celery_app worker -l info -c 4
    env_file:
      - .env.production
    depends_on:
      - backend
      - redis

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A app.celery_app beat -l info
    env_file:
      - .env.production
    depends_on:
      - backend
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=https://yourdomain.com/api
    restart: always
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

### 2. Сборка и запуск

```bash
# Сборка образов
docker compose -f docker-compose.prod.yml build

# Запуск в фоновом режиме
docker compose -f docker-compose.prod.yml up -d

# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

# Проверка статуса
docker compose -f docker-compose.prod.yml ps
```

### 3. Применение миграций

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 4. Создание суперпользователя

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.cli create-superuser \
  --email admin@yourdomain.com \
  --password YourSecurePassword123!
```

## 🔒 Настройка HTTPS

### 1. Конфигурация Nginx

```bash
sudo vim /etc/nginx/sites-available/marketoluh
```

```nginx
# Редирект HTTP -> HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS конфигурация
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL параметры
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Увеличенные таймауты для долгих операций
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # API docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
    }

    # WebSocket (если используется)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Максимальный размер загрузки
    client_max_body_size 50M;
}
```

```bash
# Включение конфигурации
sudo ln -s /etc/nginx/sites-available/marketoluh /etc/nginx/sites-enabled/

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

### 2. Получение SSL сертификата

```bash
# Получение сертификата Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автоматическое обновление
sudo certbot renew --dry-run

# Cron для автообновления (добавится автоматически)
sudo crontab -l
```

## 📊 Мониторинг и логирование

### 1. Настройка логирования

```bash
# Создание директории для логов
sudo mkdir -p /var/log/marketoluh
sudo chown marketoluh:marketoluh /var/log/marketoluh
```

### 2. Ротация логов

```bash
sudo vim /etc/logrotate.d/marketoluh
```

```
/var/log/marketoluh/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 marketoluh marketoluh
    sharedscripts
    postrotate
        docker compose -f /home/marketoluh/Trial_RDV/docker-compose.prod.yml restart backend
    endscript
}
```

### 3. Мониторинг с Prometheus + Grafana (опционально)

См. отдельный файл: `docs/deployment/MONITORING.md`

## 💾 Резервное копирование

См. подробное руководство: [BACKUP_RESTORE.md](BACKUP_RESTORE.md)

### Быстрая настройка

```bash
# Скрипт для бэкапа
cat > /home/marketoluh/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/marketoluh/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Бэкап PostgreSQL
docker compose -f /home/marketoluh/Trial_RDV/docker-compose.prod.yml exec -T db \
    pg_dump -U marketoluh_user marketoluh_db | \
    gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Удаление старых бэкапов (старше 30 дней)
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /home/marketoluh/backup.sh

# Cron для ежедневного бэкапа
(crontab -l 2>/dev/null; echo "0 2 * * * /home/marketoluh/backup.sh") | crontab -
```

## 🔄 Обновление системы

### 1. Обновление кода

```bash
cd /home/marketoluh/Trial_RDV

# Бэкап текущей версии
git tag -a v$(date +%Y%m%d) -m "Backup before update"

# Получение обновлений
git fetch origin
git pull origin main
```

### 2. Применение миграций

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 3. Пересборка и перезапуск

```bash
# Пересборка образов
docker compose -f docker-compose.prod.yml build

# Перезапуск с минимальным downtime
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

## 🔍 Troubleshooting

### Проверка здоровья сервисов

```bash
# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи конкретного сервиса
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs celery_worker

# Health check
curl http://localhost:8000/health
```

### Распространенные проблемы

**1. Backend не запускается**

```bash
# Проверка логов
docker compose -f docker-compose.prod.yml logs backend

# Проверка переменных окружения
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE

# Проверка подключения к БД
docker compose -f docker-compose.prod.yml exec backend python -c "from app.database import engine; engine.connect()"
```

**2. Ошибка подключения к PostgreSQL**

```bash
# Проверка статуса PostgreSQL
docker compose -f docker-compose.prod.yml exec db pg_isready

# Проверка логов
docker compose -f docker-compose.prod.yml logs db
```

**3. Celery worker не обрабатывает задачи**

```bash
# Проверка статуса
docker compose -f docker-compose.prod.yml exec celery_worker celery -A app.celery_app inspect active

# Перезапуск worker
docker compose -f docker-compose.prod.yml restart celery_worker
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker compose -f docker-compose.prod.yml logs`
2. Ознакомьтесь с [FAQ](../FAQ.md)
3. Создайте issue: https://github.com/RDmitryV/Trial_RDV/issues

---

**Версия документа:** 1.0.0
**Последнее обновление:** 2026-02-02
