# Nobat — سیستم نوبت‌دهی SaaS تلگرامی

## نصب سریع

```bash
git clone https://github.com/moha100h/nobat.git
cd nobat
chmod +x install.sh
./install.sh
```

## دستورات

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
git pull && docker compose build --no-cache && docker compose up -d
```

## ساختار

```
nobat/
├── backend/          # FastAPI REST API
├── master_bot/       # بات مدیریت مرکزی (aiogram 3)
├── scheduler/        # یادآور + بکاپ خودکار
├── shared/           # config, security, jalali
├── docker-compose.yml
└── install.sh
```
