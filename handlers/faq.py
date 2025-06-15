import logging

from aiogram import types, Dispatcher, F

from database.db import get_all_faq


async def faq_command(callback: types.CallbackQuery):
    from keyboards.default import faq_menu, main_menu
    try:
        faqs = get_all_faq()
        if not faqs:
            await callback.message.answer("❌ Hozircha savollar mavjud emas.", reply_markup=main_menu())
            await callback.answer()
            return
        text = "<b>❓ Tez-tez so‘raladigan savollar:</b>\n\nQuyidagi savollardan birini tanlang:"
        kb = faq_menu(faqs)
        await callback.message.edit_text(text, reply_markup=kb)
        logging.info(f"FAQ ro‘yxati ko‘rsatildi: user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"faq_command da xato: {e}, user_id={callback.from_user.id}")
        await callback.message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())
    await callback.answer()

async def faq_answer(callback: types.CallbackQuery):
    from keyboards.default import back_to_faq_menu, main_menu
    try:
        faq_id = int(callback.data.replace("faq_answer_", ""))
        faqs = get_all_faq()
        faq = next((f for f in faqs if f["id"] == faq_id), None)
        if faq:
            answer = faq["answer"]
            video_url = faq["video_url"]
            text = f"{answer}"
            if video_url:
                text += f"\n\n📹 Video: {video_url}"
            await callback.message.edit_text(text, reply_markup=back_to_faq_menu())
            logging.info(f"FAQ javobi ko‘rsatildi: faq_id={faq_id}, user_id={callback.from_user.id}")
        else:
            await callback.message.answer("❌ Bu savol topilmadi.", reply_markup=main_menu())
            logging.warning(f"FAQ topilmadi: faq_id={faq_id}, user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"faq_answer da xato: {e}, callback.data={callback.data}, user_id={callback.from_user.id}")
        await callback.message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())
    await callback.answer()

async def back_to_faq_list(callback: types.CallbackQuery):
    from keyboards.default import faq_menu, main_menu
    try:
        faqs = get_all_faq()
        if not faqs:
            await callback.message.edit_text("❌ Hozircha savollar mavjud emas.", reply_markup=main_menu())
        else:
            text = "<b>❓ Tez-tez so‘raladigan savollar:</b>\n\nQuyidagi savollardan birini tanlang:"
            kb = faq_menu(faqs)
            await callback.message.edit_text(text, reply_markup=kb)
        logging.info(f"FAQ ro‘yxatiga qaytildi: user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"back_to_faq_list da xato: {e}, user_id={callback.from_user.id}")
        await callback.message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())
    await callback.answer()

async def back_to_main_menu(callback: types.CallbackQuery):
    from keyboards.default import main_menu
    try:
        await callback.message.edit_text("📢 Botdan foydalanish uchun menyudan foydalaning:", reply_markup=main_menu())
        logging.info(f"Asosiy menyuga qaytildi: user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"back_to_main_menu da xato: {e}, user_id={callback.from_user.id}")
        await callback.message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.callback_query(F.data == "faq")(faq_command)
    dp.callback_query(F.data.startswith("faq_answer_"))(faq_answer)
    dp.callback_query(F.data == "back_to_faq_list")(back_to_faq_list)
    dp.callback_query(F.data == "back_to_main_menu")(back_to_main_menu)