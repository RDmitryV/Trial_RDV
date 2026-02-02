# Backup and Restore Guide

Руководство по резервному копированию и восстановлению данных системы "Искусанный Интеллектом Маркетолух".

## 📋 Содержание

- [Стратегия резервного копирования](#стратегия-резервного-копирования)
- [Автоматическое резервное копирование](#автоматическое-резервное-копирование)
- [Ручное резервное копирование](#ручное-резервное-копирование)
- [Восстановление данных](#восстановление-данных)
- [Тестирование бэкапов](#тестирование-бэкапов)

## 🎯 Стратегия резервного копирования

### Что резервируется

1. **База данных PostgreSQL** - пользователи, исследования, настройки
2. **Файлы отчетов** - сгенерированные PDF/DOCX документы
3. **Конфигурация** - .env файлы, docker-compose.yml
4. **Пользовательские данные** - логотипы, настройки брендирования

### Политика хранения

- **Ежедневные бэкапы**: хранятся 30 дней
- **Еженедельные бэкапы**: хранятся 12 недель (3 месяца)
- **Ежемесячные бэкапы**: хранятся 12 месяцев (1 год)
- **Критические бэкапы**: перед обновлениями, хранятся бессрочно

### Место хранения

- **Локально**: на сервере в `/backups`
- **Удаленно**: AWS S3, Yandex Object Storage, или другой S3-совместимый сервис
- **Резервная копия**: в другом датацентре/регионе

## 🤖 Автоматическое резервное копирование

### 1. Создание скрипта бэкапа

```bash
sudo mkdir -p /opt/marketoluh/scripts
sudo vim /opt/marketoluh/scripts/backup.sh
```

```bash
#!/bin/bash

# Конфигурация
APP_DIR="/home/marketoluh/Trial_RDV"
BACKUP_DIR="/home/marketoluh/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}

# Логирование
LOG_FILE="/var/log/marketoluh/backup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "=== Backup started at $(date) ==="

# 1. Бэкап PostgreSQL
echo "Backing up PostgreSQL..."
docker compose -f "$APP_DIR/docker-compose.prod.yml" exec -T db \
    pg_dump -U marketoluh_user -F c marketoluh_db | \
    gzip > "$BACKUP_DIR/daily/db_$DATE.dump.gz"

if [ $? -eq 0 ]; then
    echo "✓ Database backup completed"
else
    echo "✗ Database backup failed"
    exit 1
fi

# 2. Бэкап Redis (опционально)
echo "Backing up Redis..."
docker compose -f "$APP_DIR/docker-compose.prod.yml" exec -T redis \
    redis-cli --rdb /data/dump.rdb BGSAVE
sleep 5
docker cp $(docker compose -f "$APP_DIR/docker-compose.prod.yml" ps -q redis):/data/dump.rdb \
    "$BACKUP_DIR/daily/redis_$DATE.rdb"

# 3. Бэкап файлов отчетов
echo "Backing up report files..."
if [ -d "$APP_DIR/reports" ]; then
    tar -czf "$BACKUP_DIR/daily/reports_$DATE.tar.gz" -C "$APP_DIR" reports/
    echo "✓ Reports backup completed"
fi

# 4. Бэкап конфигурации
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/daily/config_$DATE.tar.gz" \
    -C "$APP_DIR" \
    .env.production \
    docker-compose.prod.yml \
    nginx/

echo "✓ Configuration backup completed"

# 5. Еженедельный бэкап (по воскресеньям)
if [ $(date +%u) -eq 7 ]; then
    echo "Creating weekly backup..."
    cp "$BACKUP_DIR/daily/db_$DATE.dump.gz" "$BACKUP_DIR/weekly/"
    find "$BACKUP_DIR/weekly" -name "db_*.dump.gz" -mtime +84 -delete
fi

# 6. Ежемесячный бэкап (1-го числа)
if [ $(date +%d) -eq 01 ]; then
    echo "Creating monthly backup..."
    cp "$BACKUP_DIR/daily/db_$DATE.dump.gz" "$BACKUP_DIR/monthly/"
    find "$BACKUP_DIR/monthly" -name "db_*.dump.gz" -mtime +365 -delete
fi

# 7. Очистка старых ежедневных бэкапов
echo "Cleaning old daily backups..."
find "$BACKUP_DIR/daily" -name "db_*.dump.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/daily" -name "reports_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/daily" -name "config_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 8. Загрузка в облако (опционально)
if [ -n "$S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/daily/db_$DATE.dump.gz" \
        "s3://$S3_BUCKET/backups/daily/" \
        --storage-class GLACIER
fi

# Статистика
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "=== Backup completed at $(date) ==="
echo "Total backup size: $BACKUP_SIZE"
echo ""
```

```bash
# Права на выполнение
sudo chmod +x /opt/marketoluh/scripts/backup.sh

# Владелец
sudo chown marketoluh:marketoluh /opt/marketoluh/scripts/backup.sh
```

### 2. Настройка cron

```bash
# Редактирование crontab для пользователя marketoluh
sudo crontab -u marketoluh -e
```

Добавить:

```cron
# Ежедневный бэкап в 2:00 ночи
0 2 * * * /opt/marketoluh/scripts/backup.sh

# Проверка места на диске каждый день в 1:00
0 1 * * * df -h | grep -E '/backups|/home' | mail -s "Disk Usage Report" admin@yourdomain.com
```

### 3. Настройка уведомлений

```bash
# Установка mailutils для отправки email
sudo apt install -y mailutils

# Редактирование скрипта для отправки уведомлений
cat >> /opt/marketoluh/scripts/backup.sh << 'EOF'

# Отправка email с результатами
if [ $? -eq 0 ]; then
    echo "Backup completed successfully" | \
        mail -s "✓ Marketoluh Backup Success - $DATE" admin@yourdomain.com
else
    echo "Backup failed! Check logs: $LOG_FILE" | \
        mail -s "✗ Marketoluh Backup FAILED - $DATE" admin@yourdomain.com
fi
EOF
```

## 🖐️ Ручное резервное копирование

### Полный бэкап системы

```bash
cd /home/marketoluh

# Создание директории для бэкапа
mkdir -p manual_backup_$(date +%Y%m%d)
cd manual_backup_$(date +%Y%m%d)

# 1. Бэкап PostgreSQL
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
    pg_dump -U marketoluh_user -F c marketoluh_db > database.dump

# 2. Бэкап Redis
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T redis \
    redis-cli --rdb /data/dump.rdb BGSAVE
sleep 5
docker cp $(docker compose -f ~/Trial_RDV/docker-compose.prod.yml ps -q redis):/data/dump.rdb \
    redis.rdb

# 3. Бэкап файлов приложения
tar -czf app_files.tar.gz -C ~/Trial_RDV \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .

# 4. Бэкап Docker volumes
docker run --rm \
    -v trial_rdv_postgres_data:/source:ro \
    -v $(pwd):/backup \
    alpine tar -czf /backup/postgres_volume.tar.gz -C /source .

docker run --rm \
    -v trial_rdv_redis_data:/source:ro \
    -v $(pwd):/backup \
    alpine tar -czf /backup/redis_volume.tar.gz -C /source .

# 5. Создание архива
cd ..
tar -czf marketoluh_full_backup_$(date +%Y%m%d).tar.gz manual_backup_$(date +%Y%m%d)/

echo "Full backup created: marketoluh_full_backup_$(date +%Y%m%d).tar.gz"
```

### Быстрый бэкап базы данных

```bash
# Текстовый формат (читаемый)
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
    pg_dump -U marketoluh_user marketoluh_db | \
    gzip > db_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Бинарный формат (меньше размер, быстрее)
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
    pg_dump -U marketoluh_user -F c marketoluh_db > db_backup_$(date +%Y%m%d_%H%M%S).dump
```

## 🔄 Восстановление данных

### Восстановление базы данных

#### Из SQL формата

```bash
# 1. Остановка приложения
cd ~/Trial_RDV
docker compose -f docker-compose.prod.yml stop backend celery_worker

# 2. Создание резервной копии текущей БД (на всякий случай)
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U marketoluh_user -F c marketoluh_db > db_before_restore_$(date +%Y%m%d).dump

# 3. Удаление текущей базы (опционально)
docker compose -f docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d postgres -c "DROP DATABASE IF EXISTS marketoluh_db;"

# 4. Создание новой базы
docker compose -f docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d postgres -c "CREATE DATABASE marketoluh_db;"

# 5. Восстановление из бэкапа
gunzip < db_backup_20260202.sql.gz | \
    docker compose -f docker-compose.prod.yml exec -T db \
    psql -U marketoluh_user marketoluh_db

# 6. Применение миграций (если нужно)
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 7. Перезапуск приложения
docker compose -f docker-compose.prod.yml start backend celery_worker
```

#### Из binary dump формата

```bash
# Восстановление из .dump файла
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
    pg_restore -U marketoluh_user -d marketoluh_db --clean --if-exists < db_backup.dump
```

### Восстановление Redis

```bash
# 1. Остановка Redis
docker compose -f ~/Trial_RDV/docker-compose.prod.yml stop redis

# 2. Копирование бэкапа
docker cp redis_backup.rdb $(docker compose -f ~/Trial_RDV/docker-compose.prod.yml ps -q redis):/data/dump.rdb

# 3. Запуск Redis
docker compose -f ~/Trial_RDV/docker-compose.prod.yml start redis
```

### Полное восстановление системы

```bash
# 1. Распаковка бэкапа
tar -xzf marketoluh_full_backup_20260202.tar.gz
cd manual_backup_20260202

# 2. Остановка всех сервисов
docker compose -f ~/Trial_RDV/docker-compose.prod.yml down

# 3. Восстановление volumes
docker run --rm \
    -v trial_rdv_postgres_data:/target \
    -v $(pwd):/backup \
    alpine sh -c "cd /target && tar -xzf /backup/postgres_volume.tar.gz"

docker run --rm \
    -v trial_rdv_redis_data:/target \
    -v $(pwd):/backup \
    alpine sh -c "cd /target && tar -xzf /backup/redis_volume.tar.gz"

# 4. Восстановление файлов приложения
tar -xzf app_files.tar.gz -C ~/Trial_RDV

# 5. Запуск сервисов
docker compose -f ~/Trial_RDV/docker-compose.prod.yml up -d

# 6. Проверка
docker compose -f ~/Trial_RDV/docker-compose.prod.yml ps
curl http://localhost:8000/health
```

## 🧪 Тестирование бэкапов

### Автоматическое тестирование

```bash
cat > /opt/marketoluh/scripts/test_backup.sh << 'EOF'
#!/bin/bash

BACKUP_FILE=$1
TEST_DB="marketoluh_test"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Testing backup: $BACKUP_FILE"

# Создание тестовой базы
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"

docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d postgres -c "CREATE DATABASE $TEST_DB;"

# Восстановление в тестовую базу
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip < "$BACKUP_FILE" | \
        docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
        psql -U marketoluh_user $TEST_DB
else
    cat "$BACKUP_FILE" | \
        docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec -T db \
        psql -U marketoluh_user $TEST_DB
fi

# Проверка целостности
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d $TEST_DB -c "SELECT COUNT(*) FROM users;"

docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d $TEST_DB -c "SELECT COUNT(*) FROM researches;"

# Удаление тестовой базы
docker compose -f ~/Trial_RDV/docker-compose.prod.yml exec db \
    psql -U marketoluh_user -d postgres -c "DROP DATABASE $TEST_DB;"

echo "✓ Backup test completed"
EOF

chmod +x /opt/marketoluh/scripts/test_backup.sh
```

### Ежемесячная проверка бэкапов

```bash
# Добавить в crontab
# Тестирование последнего месячного бэкапа каждое 1-е число в 3:00
0 3 1 * * /opt/marketoluh/scripts/test_backup.sh $(ls -t /home/marketoluh/backups/monthly/db_*.dump.gz | head -1)
```

## 📊 Мониторинг бэкапов

### Проверка размера бэкапов

```bash
# Размер всех бэкапов
du -sh /home/marketoluh/backups/*

# Последние 10 бэкапов с размерами
ls -lht /home/marketoluh/backups/daily/db_*.dump.gz | head -10
```

### Проверка успешности последнего бэкапа

```bash
# Проверка логов
tail -n 50 /var/log/marketoluh/backup.log

# Проверка наличия сегодняшнего бэкапа
TODAY=$(date +%Y%m%d)
ls -la /home/marketoluh/backups/daily/db_${TODAY}_*.dump.gz
```

## 🚨 План disaster recovery

### При потере данных

1. **Немедленно**:
   - Остановите все операции записи
   - Сохраните текущее состояние системы
   - Оцените масштаб потери данных

2. **Восстановление**:
   - Используйте последний валидный бэкап
   - Восстановите базу данных
   - Восстановите файлы
   - Проверьте целостность данных

3. **Проверка**:
   - Проверьте критические функции
   - Проверьте данные пользователей
   - Уведомите пользователей при необходимости

4. **Анализ**:
   - Выявите причину проблемы
   - Предотвратите повторение
   - Обновите процедуры

## 📞 Поддержка

При проблемах с восстановлением:
- Email: admin@yourdomain.com
- GitHub Issues: https://github.com/RDmitryV/Trial_RDV/issues

---

**Версия документа:** 1.0.0
**Последнее обновление:** 2026-02-02
