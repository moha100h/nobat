import httpx, logging
from datetime import date, timedelta
from shared.config import get_settings
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)
settings = get_settings()
_H = {"X-Api-Key": settings.INTERNAL_API_KEY}

async def _get(path, tid=None):
    h = {**_H}
    if tid: h["X-Tenant-Id"] = str(tid)
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{settings.BACKEND_URL}{path}", headers=h)
        r.raise_for_status()
        return r.json()

async def _post(path, tid=None, **kw):
    h = {**_H}
    if tid: h["X-Tenant-Id"] = str(tid)
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{settings.BACKEND_URL}{path}", headers=h, **kw)
        r.raise_for_status()
        return r.json()

async def send_reminders():
    try:
        tenants = await _get("/api/v1/tenants/")
        tomorrow = str(date.today() + timedelta(days=1))
        for t in tenants:
            if t["status"] != "active": continue
            try:
                bookings = await _get(f"/api/v1/bookings/?d={tomorrow}&status=confirmed", tid=t["id"])
                if not bookings: continue
                bot = Bot(token=t["bot_token"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                for b in bookings:
                    if b.get("reminder_sent"): continue
                    try:
                        cust = await _get(f"/api/v1/users/customers/{b['customer_id']}", tid=t["id"])
                        await bot.send_message(cust["tg_id"], f"⏰ <b>یادآوری نوبت</b>\n\n📅 فردا {tomorrow}\n🕐 ساعت {b['start_time']}\n\nلطفاً به موقع حاضر باشید.")
                        logger.info(f"Reminder sent booking {b['id']}")
                    except Exception as e:
                        logger.warning(f"Reminder booking {b['id']}: {e}")
                await bot.session.close()
            except Exception as e:
                logger.warning(f"Tenant {t['id']}: {e}")
    except Exception as e:
        logger.error(f"send_reminders: {e}")

async def run_backup():
    try:
        result = await _post("/api/v1/backups/db")
        logger.info(f"Backup: {result.get('file')}")
        if settings.MASTER_BOT_TOKEN and settings.MASTER_ADMIN_ID:
            bot = Bot(token=settings.MASTER_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            await bot.send_message(settings.MASTER_ADMIN_ID, f"💾 <b>بکاپ خودکار انجام شد</b>\nفایل: {result.get('file')}")
            await bot.session.close()
    except Exception as e:
        logger.error(f"run_backup: {e}")
