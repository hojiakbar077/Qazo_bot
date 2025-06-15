import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.db import get_all_channels, is_admin, add_user
from keyboards.default import main_menu, admin_menu
from utils.subscription import check_subscription

router = Router()

@router.callback_query(F.data == "check_subs")
async def handle_check_subs(call: CallbackQuery):
    user = call.from_user
    if is_admin(user.id):
        add_user(user.id, user.full_name)
        await call.message.delete()
        await call.message.answer("✅ Siz adminsiz. Obuna talab qilinmaydi.", reply_markup=admin_menu())
        logging.info(f"Admin uchun obuna tekshiruvi o‘tkazildi: user_id={user.id}")
        return

    channels = get_all_channels()
    if not channels:
        add_user(user.id, user.full_name)
        await call.message.delete()
        await call.message.answer("✅ Hozirda obuna talab qilinmaydi. Botdan foydalanishingiz mumkin.", reply_markup=main_menu())
        logging.info(f"Obuna talab qilinmadi, kanallar bo‘sh: user_id={user.id}")
        return

    if await check_subscription(user.id, call.bot, channels):
        add_user(user.id, user.full_name)
        await call.message.delete()
        await call.message.answer("✅ Obuna tekshirildi. Endi botdan foydalanishingiz mumkin.", reply_markup=main_menu())
        logging.info(f"Obuna tekshirildi: user_id={user.id}")
    else:
        await call.answer("🚫 Hali ham barcha kanallarga obuna emassiz.", show_alert=True)
        logging.warning(f"Obuna tekshiruvi muvaffaqiyatsiz: user_id={user.id}")