import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import ADMIN_ID
from database.db import is_admin, add_user, get_all_channels, is_user_exists
from keyboards.default import admin_menu, check_subscription_menu, main_menu

router = Router()

@router.message(CommandStart())
async def start_command(message: Message):
    user = message.from_user
    try:
        if await is_admin(user.id):
            await add_user(user.id, user.full_name)
            await message.answer(
                "👤 Siz adminsiz. Botdan to'liq foydalanishingiz mumkin.",
                reply_markup=admin_menu(is_main_admin=user.id == ADMIN_ID)
            )
            logging.info(f"Admin /start buyrug'ini ishlatdi: user_id={user.id}")
        else:
            channels = await get_all_channels()
            if not channels:
                if await is_user_exists(user.id):
                    await message.answer(
                        "😊 Siz bilan yana ko'rishganimdan xursandman! Botdan foydalanish uchun menyudan foydalaning:",
                        reply_markup=main_menu()
                    )
                    logging.info(f"Qayta tashrif buyurgan foydalanuvchi: user_id={user.id}")
                else:
                    await add_user(user.id, user.full_name)
                    await message.answer(
                        "🤝 Assalomu aleykum! Botimizga xush kelibsiz. Quyidagi menyudan foydalaning:",
                        reply_markup=main_menu()
                    )
                    logging.info(f"Birinchi marta tashrif buyurgan foydalanuvchi: user_id={user.id}")
            else:
                await message.answer(
                    "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=check_subscription_menu(channels)
                )
                logging.info(f"/start buyrug'i ishlatildi, obuna talab qilindi: user_id={user.id}")
    except Exception as e:
        logging.error(f"start_command da xato: user_id={user.id}, {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

def register_handlers(dp):
    dp.include_router(router)
