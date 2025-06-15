import sqlite3

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db import is_admin

prayer_names = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]

async def send_qazo_reminder(bot: Bot):
    """
    Sends a daily reminder to non-admin users with their qazo counts and inline buttons.
    """
    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        for user_id in [u[0] for u in users]:
            if not is_admin(user_id):
                counts = {}
                for prayer in prayer_names:
                    cursor.execute("SELECT count FROM qazo WHERE user_id=? AND prayer_name=?", (user_id, prayer))
                    row = cursor.fetchone()
                    counts[prayer] = row[0] if row else 0

                keyboard = []
                for prayer in prayer_names:
                    keyboard.append([InlineKeyboardButton(text=prayer.capitalize(), callback_data="noop")])
                    buttons = [
                        InlineKeyboardButton(text="➖", callback_data=f"dec_{prayer}"),
                        InlineKeyboardButton(text=str(counts[prayer]), callback_data="noop"),
                        InlineKeyboardButton(text="➕", callback_data=f"inc_{prayer}")
                    ]
                    keyboard.append(buttons)

                keyboard.append([InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="back_to_menu")])

                inline_kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

                text = (
                    "<b>Bugungi qazo namozlaringiz:</b>\n\n"
                    "Quyidagi tugmalar orqali o‘qigan yoki o‘qimagan namozlaringizni belgilang."
                )
                try:
                    await bot.send_message(user_id, text, reply_markup=inline_kb)
                except Exception as e:
                    print(f"Failed to send message to {user_id}: {e}")

def setup_scheduler(bot: Bot):
    """
    Sets up the scheduler to send qazo reminders daily at 20:00 Tashkent time.
    """
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(
        send_qazo_reminder,
        trigger="cron",
        hour=22,
        minute=10,
        args=[bot],
        misfire_grace_time=60
    )
    scheduler.start()