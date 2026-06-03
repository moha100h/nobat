import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import from_url
from master_bot.config import settings
from master_bot.handlers import start, tenants, announcements, tickets, reports, discounts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")

async def main():
    redis = from_url(settings.REDIS_URL)
    bot = Bot(token=settings.MASTER_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=RedisStorage(redis=redis))
    for r in [start, tenants, announcements, tickets, reports, discounts]:
        dp.include_router(r.router)
    logging.info("Master Bot started")
    await dp.start_polling(bot)
