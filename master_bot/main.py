import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import from_url
from master_bot.config import settings
from master_bot.handlers import start, tenants, announcements, tickets, reports, discounts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Connecting to Redis: %s", settings.REDIS_URL)
    redis = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)
    bot = Bot(
        token=settings.MASTER_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=RedisStorage(redis=redis))
    for r in [start, tenants, announcements, tickets, reports, discounts]:
        dp.include_router(r.router)
    logger.info("Master Bot started — polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception:
        logger.error("start_polling crashed:\n%s", traceback.format_exc())
        raise
    finally:
        await bot.session.close()
        await redis.aclose()
        logger.info("Master Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
