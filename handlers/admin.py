import logging

from aiogram import types, Dispatcher, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database.db import is_admin, get_stats, get_all_users, add_channel, remove_channel, add_faq, get_all_channels, \
    add_admin, remove_admin, get_all_admins
from keyboards.default import admin_menu, main_menu, back_button_only
from states.states import AdminState, FaqStates

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "Admin")
async def admin_panel(message: types.Message):
    user_id = message.from_user.id
    if not await is_admin(user_id):
        logger.warning(f"Admin paneliga kirish rad etildi: user_id={user_id}")
        return await message.answer("❌ Sizda admin huquqlari yo'q.", reply_markup=main_menu())
    is_main_admin = user_id == ADMIN_ID
    logger.info(f"Admin paneliga kirildi: user_id={user_id}, is_main_admin={is_main_admin}")
    await message.answer("👑 Admin paneliga xush kelibsiz!", reply_markup=admin_menu(is_main_admin=is_main_admin))

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Statistikaga kirish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    try:
        stats = await get_stats()
        text = (
            "📊 Bot statistikasi:\n\n"
            f"👤 Kunlik: {stats['daily']}\n"
            f"📅 Haftalik: {stats['weekly']}\n"
            f"🗓 Oylik: {stats['monthly']}\n"
            f"👥 Umumiy: {stats['total']}"
        )
        await callback.message.answer(
            text,
            reply_markup=admin_menu(is_main_admin=callback.from_user.id == ADMIN_ID)
        )
        logger.info(f"Statistika ko'rsatildi: user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"show_stats da xato: user_id={callback.from_user.id}, {e}")
        await callback.message.answer(
            "❌ Statistika olishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def ask_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Xabar yuborish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    await callback.message.answer("Yubormoqchi bo'lgan xabaringizni kiriting:", reply_markup=back_button_only())
    await state.set_state(AdminState.waiting_for_broadcast)
    logger.info(f"Xabar yuborish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(AdminState.waiting_for_broadcast))
async def process_broadcast(message: types.Message, state: FSMContext):
    try:
        users = await get_all_users()
        count = 0
        for u in users:
            if not await is_admin(u["user_id"]):
                try:
                    await message.bot.send_message(u["user_id"], message.text)
                    count += 1
                except Exception as e:
                    logger.warning(f"Xabar yuborishda xato: user_id={u['user_id']}, {e}")
        await message.answer(
            f"✅ Xabar {count} foydalanuvchiga yuborildi.",
            reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
        )
        logger.info(f"Xabar yuborildi: {count} foydalanuvchiga, user_id={message.from_user.id}")
    except Exception as e:
        logger.error(f"process_broadcast da xato: user_id={message.from_user.id}, {e}")
        await message.answer(
            "❌ Xabar yuborishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await state.clear()

@router.callback_query(F.data == "admin_add_channel")
async def ask_add_channel(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Kanal qo'shish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    await callback.message.answer("Kanal usernameni kiriting: @ChannelName", reply_markup=back_button_only())
    await state.set_state(AdminState.waiting_for_channel_add)
    logger.info(f"Kanal qo'shish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(AdminState.waiting_for_channel_add))
async def process_add_channel(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    try:
        member = await message.bot.get_chat_member(chat_id=channel_id, user_id=message.bot.id)
        if member.status not in ("administrator", "creator"):
            await message.answer(
                "⚠️ Bot bu kanalga admin sifatida qo'shilmagan. Avval kanalga admin qiling.",
                reply_markup=back_button_only()
            )
            logger.warning(f"Kanal admin emas: channel_id={channel_id}, user_id={message.from_user.id}")
            return
    except Exception as e:
        await message.answer(
            f"❌ Bot bu kanalga kira olmayapti: {e}",
            reply_markup=back_button_only()
        )
        logger.error(f"process_add_channel da xato: channel_id={channel_id}, {e}")
        return
    await add_channel(channel_id)
    await message.answer(
        f"✅ Kanal {channel_id} saqlandi va tekshiruvdan o'tdi.",
        reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
    )
    logger.info(f"Kanal qo'shildi: channel_id={channel_id}, user_id={message.from_user.id}")
    await state.clear()

@router.callback_query(F.data == "admin_remove_channel")
async def ask_remove_channel(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Kanal o'chirish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    await callback.message.answer("O'chirmoqchi bo'lgan kanal usernameni kiriting: @ChannelName", reply_markup=back_button_only())
    await state.set_state(AdminState.waiting_for_channel_remove)
    logger.info(f"Kanal o'chirish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(AdminState.waiting_for_channel_remove))
async def process_remove_channel(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    try:
        await remove_channel(channel_id)
        await message.answer(
            f"🗑 {channel_id} o'chirildi.",
            reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
        )
        logger.info(f"Kanal o'chirildi: channel_id={channel_id}, user_id={message.from_user.id}")
    except Exception as e:
        logger.error(f"process_remove_channel da xato: channel_id={channel_id}, {e}")
        await message.answer(
            "❌ Kanal o'chirishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await state.clear()

@router.callback_query(F.data == "admin_list_channels")
async def show_channels(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Kanallar ro'yxatiga kirish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    try:
        channels = await get_all_channels()
        if not channels:
            await callback.message.answer(
                "❌ Hozircha ulangan kanallar mavjud emas.",
                reply_markup=back_button_only()
            )
        else:
            text = "<b>📋 Ulangan kanallar ro'yxati:</b>\n\n"
            for ch in channels:
                text += f"• {ch}\n"
            await callback.message.answer(
                text,
                reply_markup=admin_menu(is_main_admin=callback.from_user.id == ADMIN_ID)
            )
        logger.info(f"Kanallar ro'yxati ko'rsatildi: user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"show_channels da xato: user_id={callback.from_user.id}, {e}")
        await callback.message.answer(
            "❌ Kanallar ro'yxatini olishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await callback.answer()

@router.callback_query(F.data == "admin_list_admins")
async def show_admins(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Adminlar ro'yxatiga kirish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    if callback.from_user.id != ADMIN_ID:
        logger.warning(f"Adminlar ro'yxatini ko'rish faqat asosiy admin uchun: user_id={callback.from_user.id}")
        await callback.message.answer(
            "❌ Bu funksiya faqat asosiy admin uchun mavjud.",
            reply_markup=back_button_only()
        )
        await callback.answer()
        return
    try:
        admins = await get_all_admins()
        if not admins:
            await callback.message.answer(
                "❌ Hozircha adminlar mavjud emas.",
                reply_markup=back_button_only()
            )
        else:
            text = "<b>👥 Adminlar ro'yxati:</b>\n\n"
            for admin_id in admins:
                try:
                    user = await callback.bot.get_chat(admin_id)
                    full_name = user.full_name or "Noma'lum"
                    username = f" (@{user.username})" if user.username else ""
                    role = "Asosiy admin" if admin_id == ADMIN_ID else "Admin"
                    text += f"• ID: {admin_id} | Ism: {full_name}{username} | Rol: {role}\n"
                except Exception as e:
                    role = "Asosiy admin" if admin_id == ADMIN_ID else "Admin"
                    text += f"• ID: {admin_id} | Ism: (ma'lumot olinmadi: {e}) | Rol: {role}\n"
                    logger.warning(f"Admin ma'lumotlari olinmadi: admin_id={admin_id}, {e}")
            await callback.message.answer(
                text,
                reply_markup=admin_menu(is_main_admin=True)
            )
        logger.info(f"Adminlar ro'yxati ko'rsatildi: user_id={callback.from_user.id}, admin_count={len(admins)}")
    except Exception as e:
        logger.error(f"show_admins da xato: user_id={callback.from_user.id}, {e}")
        await callback.message.answer(
            "❌ Adminlar ro'yxatini olishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await callback.answer()

@router.callback_query(F.data == "admin_add_admin")
async def ask_add_admin(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Admin qo'shish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    if callback.from_user.id != ADMIN_ID:
        logger.warning(f"Admin qo'shish faqat asosiy admin uchun: user_id={callback.from_user.id}")
        await callback.message.answer(
            "❌ Bu funksiya faqat asosiy admin uchun mavjud.",
            reply_markup=back_button_only()
        )
        await callback.answer()
        return
    await callback.message.answer(
        "Yangi admin qo'shish uchun foydalanuvchi ID'sini kiriting (masalan: 123456789):",
        reply_markup=back_button_only()
    )
    await state.set_state(AdminState.waiting_for_admin_add)
    logger.info(f"Admin qo'shish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(AdminState.waiting_for_admin_add))
async def process_add_admin(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Iltimos, faqat raqamli ID kiriting (masalan: 123456789).",
            reply_markup=back_button_only()
        )
        logger.warning(f"Noto'g'ri admin ID kiritildi: user_id={message.from_user.id}, input={message.text}")
        return
    try:
        if await is_admin(user_id):
            await message.answer(
                "⚠️ Bu foydalanuvchi allaqachon admin.",
                reply_markup=back_button_only()
            )
            logger.info(f"Admin allaqachon mavjud: user_id={user_id}, so'rovchi={message.from_user.id}")
            await state.clear()
            return
        if await add_admin(user_id):
            try:
                await message.bot.send_message(
                    user_id,
                    "🎉 Siz endi botning adminisiz!",
                    reply_markup=admin_menu(is_main_admin=user_id == ADMIN_ID)
                )
                logger.info(f"Admin xabardor qilindi: user_id={user_id}")
            except Exception as e:
                await message.answer(
                    f"✅ Foydalanuvchi admin qilib tayinlandi, lekin xabar yuborib bo'lmadi: {e}",
                    reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
                )
                logger.warning(f"Admin xabar yuborishda xato: user_id={user_id}, {e}")
            await message.answer(
                f"✅ Foydalanuvchi (ID: {user_id}) admin qilib tayinlandi.",
                reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
            )
        else:
            await message.answer(
                "❌ Bu ID bilan foydalanuvchi topilmadi. Avval botda ro'yxatdan o'tganligiga ishonch hosil qiling.",
                reply_markup=back_button_only()
            )
            logger.warning(f"Admin qo'shish muvaffaqiyatsiz: user_id={user_id}, foydalanuvchi topilmadi")
    except Exception as e:
        logger.error(f"process_add_admin da xato: user_id={user_id}, so'rovchi={message.from_user.id}, {e}")
        await message.answer(
            "❌ Admin qo'shishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await state.clear()

@router.callback_query(F.data == "admin_remove_admin")
async def ask_remove_admin(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"Admin o'chirish rad etildi: user_id={callback.from_user.id}")
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return
    if callback.from_user.id != ADMIN_ID:
        logger.warning(f"Admin o'chirish faqat asosiy admin uchun: user_id={callback.from_user.id}")
        await callback.message.answer(
            "❌ Bu funksiya faqat asosiy admin uchun mavjud.",
            reply_markup=back_button_only()
        )
        await callback.answer()
        return
    await callback.message.answer(
        "O'chirmoqchi bo'lgan adminning ID'sini kiriting (masalan: 123456789):",
        reply_markup=back_button_only()
    )
    await state.set_state(AdminState.waiting_for_admin_remove)
    logger.info(f"Admin o'chirish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(AdminState.waiting_for_admin_remove))
async def process_remove_admin(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Iltimos, faqat raqamli ID kiriting (masalan: 123456789).",
            reply_markup=back_button_only()
        )
        logger.warning(f"Noto'g'ri admin ID kiritildi: user_id={message.from_user.id}, input={message.text}")
        return
    try:
        if not await is_admin(user_id):
            await message.answer(
                "⚠️ Bu foydalanuvchi admin emas.",
                reply_markup=back_button_only()
            )
            logger.info(f"Admin topilmadi: user_id={user_id}, so'rovchi={message.from_user.id}")
            await state.clear()
            return
        if await remove_admin(user_id):
            try:
                await message.bot.send_message(
                    user_id,
                    "ℹ️ Sizning admin huquqlaringiz olib tashlandi.",
                    reply_markup=main_menu()
                )
                logger.info(f"Admin xabardor qilindi: user_id={user_id}")
            except Exception as e:
                await message.answer(
                    f"✅ Admin huquqlari olib tashlandi, lekin xabar yuborib bo'lmadi: {e}",
                    reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
                )
                logger.warning(f"Admin xabar yuborishda xato: user_id={user_id}, {e}")
            await message.answer(
                f"✅ Foydalanuvchi (ID: {user_id}) adminlikdan olib tashlandi.",
                reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
            )
        else:
            await message.answer(
                "❌ Bu ID bilan admin topilmadi yoki asosiy adminni o'chirib bo'lmaydi.",
                reply_markup=back_button_only()
            )
            logger.warning(f"Admin o'chirish muvaffaqiyatsiz: user_id={user_id}, so'rovchi={message.from_user.id}")
    except Exception as e:
        logger.error(f"process_remove_admin da xato: user_id={user_id}, so'rovchi={message.from_user.id}, {e}")
        await message.answer(
            "❌ Admin o'chirishda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await state.clear()

@router.callback_query(F.data == "admin_add_faq")
async def start_add_faq(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        logger.warning(f"FAQ qo'shish rad etildi: user_id={callback.from_user.id}")
        await callback.message.answer(
            "❌ Siz admin emassiz.",
            reply_markup=back_button_only()
        )
        await callback.answer()
        return
    await callback.message.answer(
        "✍️ Iltimos, savol matnini kiriting:",
        reply_markup=back_button_only()
    )
    await state.set_state(FaqStates.waiting_for_question)
    logger.info(f"FAQ qo'shish so'raldi: user_id={callback.from_user.id}")
    await callback.answer()

@router.message(StateFilter(FaqStates.waiting_for_question))
async def process_faq_question(message: types.Message, state: FSMContext):
    try:
        await state.update_data(question=message.text)
        await message.answer(
            "📝 Endi shu savolga javobni yozing:",
            reply_markup=back_button_only()
        )
        await state.set_state(FaqStates.waiting_for_answer)
        logger.info(f"FAQ savoli kiritildi: user_id={message.from_user.id}")
    except Exception as e:
        logger.error(f"process_faq_question da xato: user_id={message.from_user.id}, {e}")
        await message.answer(
            "❌ Savol saqlashda xato yuz berdi.",
            reply_markup=back_button_only()
        )
        await state.clear()

@router.message(StateFilter(FaqStates.waiting_for_answer))
async def process_faq_answer(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        question = data["question"]
        answer = message.text
        await add_faq(question, answer)
        await message.answer(
            "✅ FAQ muvaffaqiyatli saqlandi!",
            reply_markup=admin_menu(is_main_admin=message.from_user.id == ADMIN_ID)
        )
        logger.info(f"FAQ javobi saqlandi: user_id={message.from_user.id}, question={question}")
    except Exception as e:
        logger.error(f"process_faq_answer da xato: user_id={message.from_user.id}, {e}")
        await message.answer(
            "❌ FAQ saqlashda xato yuz berdi.",
            reply_markup=back_button_only()
        )
    await state.clear()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Xabarni o'chirishda xato: user_id={callback.from_user.id}, {e}")
    try:
        if not await is_admin(callback.from_user.id):
            await callback.message.answer(
                "Asosiy menyuga qaytdingiz!",
                reply_markup=main_menu()
            )
        else:
            await callback.message.answer(
                "Asosiy menyuga qaytdingiz!",
                reply_markup=admin_menu(is_main_admin=callback.from_user.id == ADMIN_ID)
            )
        await state.clear()
        logger.info(f"Orqaga qaytildi: user_id={callback.from_user.id}")
    except Exception as e:
        logger.error(f"back_to_menu da xato: user_id={callback.from_user.id}, {e}")
        await callback.message.answer(
            "Asosiy menyuga qaytishda xato yuz berdi.",
            reply_markup=main_menu()
        )
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.include_router(router)
