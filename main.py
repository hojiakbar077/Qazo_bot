import asyncio
import logging
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from config import BOT_TOKEN, RAILWAY_ENVIRONMENT, PORT, WEBHOOK_URL, WEBHOOK_PATH
from database.db import init_db, close_db
from handlers import start, qazo, prayer_times, faq, admin
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

# Global o'zgaruvchilar
bot: Bot = None
dp: Dispatcher = None


async def setup_bot():
    """Botni sozlash"""
    global bot, dp

    try:
        # Bot yaratish
        bot = Bot(token=BOT_TOKEN,parse_mode=ParseMode.HTML)

        logger.info("Bot obyekti yaratildi")

        # Dispatcher va Storage
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        logger.info("Dispatcher va MemoryStorage sozlandi")

        # Ma'lumotlar bazasini ishga tushirish
        logger.info("PostgreSQL ma'lumotlar bazasi ishga tushirilmoqda")
        await init_db()
        logger.info("Ma'lumotlar bazasi muvaffaqiyatli ulandi")

        # Handlerlarni ro'yxatdan o'tkazish
        dp.include_router(check_subs_router)
        logger.info("check_subs_router qo'shildi")

        # Eski handler registration usulini yangi router usuli bilan almashtirish
        if hasattr(start, 'router'):
            dp.include_router(start.router)
        else:
            start.register_handlers(dp)
        logger.info("Start handlerlari ro'yxatdan o'tdi")

        if hasattr(qazo, 'router'):
            dp.include_router(qazo.router)
        else:
            qazo.register_handlers(dp)
        logger.info("Qazo handlerlari ro'yxatdan o'tdi")

        if hasattr(prayer_times, 'router'):
            dp.include_router(prayer_times.router)
        else:
            prayer_times.register_handlers(dp)
        logger.info("Prayer times handlerlari ro'yxatdan o'tdi")

        if hasattr(faq, 'router'):
            dp.include_router(faq.router)
        else:
            faq.register_handlers(dp)
        logger.info("FAQ handlerlari ro'yxatdan o'tdi")

        if hasattr(admin, 'router'):
            dp.include_router(admin.router)
        else:
            admin.register_handlers(dp)
        logger.info("Admin handlerlari ro'yxatdan o'tdi")

        return True

    except Exception as e:
        logger.error(f"Bot sozlashda xato: {e}")
        return False


async def on_startup():
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")

    # Webhook o'rnatish (production uchun)
    if RAILWAY_ENVIRONMENT == 'production' and WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook o'rnatildi: {webhook_url}")
    else:
        # Webhookni o'chirish (development uchun)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook o'chirildi, polling rejimida ishlamoqda")


async def on_shutdown():
    """Bot to'xtaganda"""
    logger.info("Bot to'xtatilmoqda...")

    # Ma'lumotlar bazasini yopish
    await close_db()

    # Bot sessionni yopish
    if bot:
        await bot.session.close()
        logger.info("Bot sessioni yopildi")


def create_app():
    """Web application yaratish"""
    app = web.Application()

    # Health check endpoint
    async def health_check(request):
        return web.json_response({"status": "ok", "bot": "running"})

    app.router.add_get('/health', health_check)

    # Webhook handler (production uchun)
    if RAILWAY_ENVIRONMENT == 'production':
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    return app


async def main():
    """Asosiy funksiya"""
    logger.info("Dastur boshlanmoqda")

    # Botni sozlash
    setup_success = await setup_bot()
    if not setup_success:
        logger.error("Bot sozlashda xato, dastur to'xtatilmoqda")
        return

    # Signal handlerlar
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} qabul qilindi, dastur to'xtatilmoqda...")
        asyncio.create_task(on_shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await on_startup()

        if RAILWAY_ENVIRONMENT == 'production':
            # Production: webhook rejimi
            logger.info("Production rejimida ishga tushirilmoqda (webhook)")
            app = create_app()

            runner = web.AppRunner(app)
            await runner.setup()

            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()

            logger.info(f"Server {PORT} portda ishga tushdi")

            # Server ishlab turishini kutish
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                pass
            finally:
                await runner.cleanup()
        else:
            # Development: polling rejimi
            logger.info("Development rejimida ishga tushirilmoqda (polling)")
            await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logger.error(f"Dastur ishga tushirishda xato: {e}")
    finally:
        await on_shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logger.error(f"Dastur xatosi: {e}")
