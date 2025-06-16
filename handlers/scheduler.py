from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db import is_admin, get_all_users, get_user_qazo

prayer_names = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]


async def send_qazo_reminder(bot: Bot):
    """
    Sends a daily reminder to non-admin users with their qazo counts and inline buttons.
    """
    try:
        users = await get_all_users()

        for user_data in users:
            user_id = user_data["user_id"]
            if not await is_admin(user_id):
                try:
                    counts = await get_user_qazo(user_id)

                    keyboard = []
                    for prayer in prayer_names:
                        keyboard.append([InlineKeyboardButton(text=prayer.capitalize(), callback_data="noop")])
                        buttons = [
                            InlineKeyboardButton(text="➖", callback_data=f"dec_{prayer}"),
                            InlineKeyboardButton(text=str(counts.get(prayer, 0)), callback_data="noop"),
                            InlineKeyboardButton(text="➕", callback_data=f"inc_{prayer}")
                        ]
                        keyboard.append(buttons)

                    keyboard.append([InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="back_to_menu")])

                    inline_kb = InlineKeyboardMarkup(inline_keyboard=keyboard)

                    text = (
                        "<b>Bugungi qazo namozlaringiz:</b>\n\n"
                        "Quyidagi tugmalar orqali o'qigan yoki o'qimagan namozlaringizni belgilang."
                    )

                    await bot.send_message(user_id, text, reply_markup=inline_kb, parse_mode="HTML")
                except Exception as e:
                    print(f"Failed to send message to {user_id}: {e}")
    except Exception as e:
        print(f"Error in send_qazo_reminder: {e}")


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
