#!/usr/bin/env bash
set -euo pipefail
RED='\033[0;31m';GREEN='\033[0;32m';BLUE='\033[0;34m';NC='\033[0m'
info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
success(){ echo -e "${GREEN}[OK]${NC} $*"; }
error(){ echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
command -v docker >/dev/null 2>&1 || error "Docker not found."
docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1 || error "Docker Compose not found."
read -rp "MASTER_BOT_TOKEN: " MASTER_BOT_TOKEN
[[ -z "$MASTER_BOT_TOKEN" ]] && error "توکن الزامی است"
read -rp "MASTER_ADMIN_ID: " MASTER_ADMIN_ID
[[ -z "$MASTER_ADMIN_ID" ]] && error "آیدی الزامی است"
[[ ! "$MASTER_ADMIN_ID" =~ ^[0-9]+$ ]] && error "آیدی باید عدد باشد"
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)
DB_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)
INTERNAL_API_KEY=$(openssl rand -hex 24)
cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
POSTGRES_DB=nobat
POSTGRES_USER=nobat
POSTGRES_PASSWORD=${DB_PASSWORD}
DATABASE_URL=postgresql+asyncpg://nobat:${DB_PASSWORD}@postgres:5432/nobat
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
MASTER_BOT_TOKEN=${MASTER_BOT_TOKEN}
MASTER_ADMIN_ID=${MASTER_ADMIN_ID}
BACKEND_URL=http://backend:8000
INTERNAL_API_KEY=${INTERNAL_API_KEY}
UPLOAD_DIR=/app/uploads
BACKUP_DIR=/app/backups
BACKUP_CRON=0 3 * * *
REMINDER_INTERVAL=300
EOF
success ".env created"
docker compose build --no-cache
docker compose up -d
RETRIES=30
until curl -sf http://localhost:8000/health >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do sleep 3;RETRIES=$((RETRIES-1));echo -n "."; done
echo ""
[ $RETRIES -eq 0 ] && error "Backend did not start. Run: docker compose logs backend"
success "Done!"
docker compose ps
