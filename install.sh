#!/usr/bin/env bash
set -euo pipefail
RED='\033[0;31m';GREEN='\033[0;32m';BLUE='\033[0;34m';YELLOW='\033[0;33m';NC='\033[0m'
info(){    echo -e "${BLUE}[INFO]${NC}  $*"; }
success(){ echo -e "${GREEN}[OK]${NC}    $*"; }
warn(){    echo -e "${YELLOW}[WARN]${NC}  $*"; }
error(){   echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

command -v docker >/dev/null 2>&1 || error "Docker not found."
docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1 || error "Docker Compose not found."
command -v curl >/dev/null 2>&1 || error "curl not found."

# اگر .env از قبل وجود داشت، فقط آپدیت کن
if [ -f .env ]; then
    warn ".env already exists — running update mode."
    info "Pulling latest code..."
    git pull --ff-only || warn "git pull failed, continuing with local code."
    info "Rebuilding containers..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    success "Update done!"
    docker compose ps
    exit 0
fi

# نصب اول
read -rp "MASTER_BOT_TOKEN: " MASTER_BOT_TOKEN
[[ -z "$MASTER_BOT_TOKEN" ]] && error "توکن الزامی است"
read -rp "MASTER_ADMIN_ID: " MASTER_ADMIN_ID
[[ -z "$MASTER_ADMIN_ID" ]] && error "آیدی الزامی است"
[[ ! "$MASTER_ADMIN_ID" =~ ^[0-9]+$ ]] && error "آیدی باید عدد باشد"

# حذف webhook احتمالی قبلی
info "Deleting any existing Telegram webhook..."
curl -s "https://api.telegram.org/bot${MASTER_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" | grep -q '"ok":true' \
    && success "Webhook deleted." || warn "Could not delete webhook (may not exist)."

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

# صبر برای backend
info "Waiting for backend to become healthy..."
RETRIES=60
until [ "$(docker inspect -f '{{.State.Health.Status}}' nobat_backend 2>/dev/null)" = "healthy" ] || [ $RETRIES -eq 0 ]; do
  sleep 2; RETRIES=$((RETRIES-1)); echo -n "."
done
echo ""
[ $RETRIES -eq 0 ] && error "Backend did not become healthy. Run: docker compose logs backend"
success "Backend healthy."

# صبر برای master_bot
info "Waiting for master_bot to start..."
RETRIES=30
until docker compose logs master_bot 2>/dev/null | grep -q "Master Bot started"; do
  sleep 2; RETRIES=$((RETRIES-1)); echo -n "."
  [ $RETRIES -eq 0 ] && break
done
echo ""
if [ $RETRIES -eq 0 ]; then
    warn "master_bot did not log 'started' in time. Logs:"
    docker compose logs master_bot --tail 20
else
    success "Master Bot is running!"
fi

success "Done!"
docker compose ps
