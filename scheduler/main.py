import asyncio, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from scheduler.jobs import send_reminders, run_backup
from shared.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
settings = get_settings()

async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    scheduler.add_job(send_reminders, "interval", minutes=5, id="reminders")
    parts = settings.BACKUP_CRON.split()
    if len(parts) == 5:
        scheduler.add_job(run_backup, CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]), id="backup")
    scheduler.start()
    logging.info("Scheduler started")
    try:
        while True: await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
