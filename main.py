import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import start, qazo, prayer_times, faq, admin, scheduler
from handlers.check_subs import router as check_subs_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Bot ishga tushirilmoqda...")
    try:
        bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
        logger.info("Bot obyekti yaratildi")
    except Exception as e:
        logger.error(f"Bot yaratishda xato: {e}")
        return

    try:
        dp = Dispatcher(storage=MemoryStorage())
        logger.info("Dispatcher va MemoryStorage sozlandi")
        dp.include_router(check_subs_router)
        logger.info("check_subs_router qo‘shildi")
    except Exception as e:
        logger.error(f"Dispatcher sozlashda xato: {e}")
        return

    try:
        init_db()
        logger.info("Ma'lumotlar bazasi ishga tushirildi")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini ishga tushirishda xato: {e}")
        return

    try:
        start.register_handlers(dp)
        logger.info("Start handlerlari ro‘yxatdan o‘tdi")
        qazo.register_handlers(dp)
        logger.info("Qazo handlerlari ro‘yxatdan o‘tdi")
        prayer_times.register_handlers(dp)
        logger.info("Prayer times handlerlari ro‘yxatdan o‘tdi")
        faq.register_handlers(dp)
        logger.info("FAQ handlerlari ro‘yxatdan o‘tdi")
        admin.register_handlers(dp)
        logger.info("Admin handlerlari ro‘yxatdan o‘tdi")
    except Exception as e:
        logger.error(f"Handlerlarni ro‘yxatdan o‘tkazishda xato: {e}")
        return

    try:
        scheduler.setup_scheduler(bot)
        logger.info("Scheduler sozlandi va ishga tushirildi")
    except Exception as e:
        logger.error(f"Scheduler sozlashda xato: {e}")
        return

    try:
        logger.info("Polling boshlanmoqda...")
        await dp.start_polling(bot)
        logger.info("Polling muvaffaqiyatli yakunlandi")
    except Exception as e:
        logger.error(f"Pollingda xato: {e}")

if __name__ == "__main__":
    logger.info("Dastur boshlanmoqda")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Dastur yakunlashda xato: {e}")