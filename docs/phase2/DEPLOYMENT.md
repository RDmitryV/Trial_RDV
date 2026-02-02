# Deployment Guide - Phase 2

## Prerequisites

- Docker and Docker Compose installed
- Git
- OpenAI API key or Anthropic API key

## Quick Start (Development)

### 1. Clone the Repository

```bash
git clone https://github.com/RDmitryV/Trial_RDV.git
cd Trial_RDV
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required environment variables:
- `SECRET_KEY`: Generate a secure random key
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: Your LLM API key

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Backend API (port 8000)
- Celery worker (background tasks)
- Flower (Celery monitoring, port 5555)

### 4. Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the Application

- API Documentation: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc
- Celery Flower: http://localhost:5555
- API Health Check: http://localhost:8000/health

## Manual Setup (Without Docker)

### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL

```bash
createdb marketoluh_db
# Update DATABASE_URL in .env
```

### 3. Set Up Redis

Install and start Redis:
```bash
# On Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# On macOS
brew install redis
brew services start redis
```

### 4. Run Migrations

```bash
cd backend
alembic upgrade head
```

### 5. Start the Application

```bash
# Terminal 1: API Server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker
cd backend
celery -A app.celery_app worker --loglevel=info

# Terminal 3 (optional): Flower
cd backend
celery -A app.celery_app flower --port=5555
```

## Testing the MVP

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response.

### 3. Create a Research

```bash
curl -X POST "http://localhost:8000/api/v1/research/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Анализ рынка доставки еды",
    "product_description": "Мобильное приложение для доставки здоровой еды",
    "industry": "Общественное питание",
    "region": "Москва",
    "research_type": "market"
  }'
```

### 4. Analyze Research

```bash
curl -X POST "http://localhost:8000/api/v1/research/{research_id}/analyze" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Production Deployment

### Environment Variables

For production, ensure you set:
- `DEBUG=false`
- `ENVIRONMENT=production`
- Strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- Production database URL
- HTTPS for CORS origins
- Sentry DSN for error tracking (optional)

### Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure Sentry for error tracking
- [ ] Enable rate limiting
- [ ] Review CORS settings

### Scaling

For production scale:
1. Use managed PostgreSQL (AWS RDS, DigitalOcean, etc.)
2. Use managed Redis (AWS ElastiCache, Redis Cloud, etc.)
3. Deploy multiple backend instances behind a load balancer
4. Scale Celery workers horizontally
5. Use container orchestration (Kubernetes, ECS)

## Monitoring

- API metrics: http://localhost:8000/metrics (if Prometheus client is enabled)
- Celery tasks: http://localhost:5555
- Database: Use pgAdmin or DBeaver
- Logs: Check Docker logs with `docker-compose logs -f backend`

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

### Redis Connection Issues

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Migration Issues

```bash
# Check current migration version
docker-compose exec backend alembic current

# Downgrade one revision
docker-compose exec backend alembic downgrade -1

# Upgrade to head
docker-compose exec backend alembic upgrade head
```

### API Not Responding

```bash
# Check backend logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend
```

## Backup and Restore

### Database Backup

```bash
docker-compose exec postgres pg_dump -U marketoluh marketoluh_db > backup.sql
```

### Database Restore

```bash
docker-compose exec -T postgres psql -U marketoluh marketoluh_db < backup.sql
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```
