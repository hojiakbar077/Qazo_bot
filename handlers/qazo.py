import sqlite3
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.default import main_menu, qazo_menu, qazo_hisoblash_menu
from states.states import QazoHisobState

prayer_names = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]

async def qazo_menu_handler(callback: types.CallbackQuery):
    """
    Displays the qazo menu with current prayer counts and inline buttons.
    """
    user_id = callback.from_user.id

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        counts = {}
        for p in prayer_names:
            cursor.execute("SELECT count FROM qazo WHERE user_id=? AND prayer_name=?", (user_id, p))
            row = cursor.fetchone()
            counts[p] = row[0] if row else 0

    text = (
        "<b>Sizdagi mavjud qazolar:</b>\n\n"
        "– Qazo oson o‘qish usuli\n"
        "– 1 oyda 15 yillik qazo o‘qish"
    )

    kb = qazo_menu(counts)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

async def increment_qazo(callback: types.CallbackQuery):
    """
    Increments the qazo count for a specific prayer and refreshes the menu.
    """
    user_id = callback.from_user.id
    prayer = callback.data.replace("inc_", "")

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO qazo (user_id, prayer_name, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, prayer_name)
            DO UPDATE SET count = count + 1
        """, (user_id, prayer))
        conn.commit()

    await callback.answer("➕ Qo‘shildi")
    await refresh_qazo_menu(callback)

async def decrement_qazo(callback: types.CallbackQuery):
    """
    Decrements the qazo count for a specific prayer if count > 0 and refreshes the menu.
    """
    user_id = callback.from_user.id
    prayer = callback.data.replace("dec_", "")

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM qazo WHERE user_id=? AND prayer_name=?", (user_id, prayer))
        current = cursor.fetchone()
        current_count = current[0] if current else 0

        if current_count > 0:
            cursor.execute("UPDATE qazo SET count = count - 1 WHERE user_id=? AND prayer_name=?", (user_id, prayer))
            conn.commit()
            await callback.answer("➖ Ayirildi")
            await refresh_qazo_menu(callback)
        else:
            await callback.answer("⚠️ 0 dan pastga tushmaydi", show_alert=True)

async def refresh_qazo_menu(callback: types.CallbackQuery):
    """
    Refreshes the entire qazo menu with updated counts.
    """
    user_id = callback.from_user.id

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        counts = {}
        for p in prayer_names:
            cursor.execute("SELECT count FROM qazo WHERE user_id=? AND prayer_name=?", (user_id, p))
            row = cursor.fetchone()
            counts[p] = row[0] if row else 0

    text = (
        "<b>Sizdagi mavjud qazolar:</b>\n\n"
        "– Qazo oson o‘qish usuli\n"
        "– 1 oyda 15 yillik qazo o‘qish"
    )

    kb = qazo_menu(counts)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

async def qazo_start(callback: types.CallbackQuery, state: FSMContext):
    """
    Initiates the qazo calculation process with a video link and range selection.
    """
    text = (
        "📌 <b>Avvalo bir nechta muhim qismlarni bilishingiz kerak:</b>\n"
        "1. Namozning farz bo‘lishi\n"
        "2. Balog‘at yoshi\n"
        "3. Quyidagi videoni tomosha qiling 👇\n\n"
        "🎥 <a href='https://www.youtube.com/watch?v=46ClRRH3Sfo'>Shayxning tushuntiruvchi videosi</a>\n\n"
        "❓ <b>Qazo vaqtingiz 1 yildan oshganmi?</b>"
    )
    kb = qazo_hisoblash_menu()
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QazoHisobState.choosing_range)
    await callback.answer()

async def handle_range_choice(callback: types.CallbackQuery, state: FSMContext):
    """
    Handles the user's choice of qazo range (years, months, days).
    """
    if callback.data == "range_years":
        await callback.message.edit_text("❓ Necha yil qazo namoz bor deb o‘ylaysiz? (masalan: 3)")
        await state.set_state(QazoHisobState.choosing_years)
    elif callback.data == "range_months":
        await callback.message.edit_text("❓ Necha oy qazo namozingiz bor deb o‘ylaysiz? (masalan: 6)")
        await state.set_state(QazoHisobState.choosing_months)
    elif callback.data == "range_days":
        await callback.message.edit_text("❓ Necha kun qazo namozingiz bor deb o‘ylaysiz? (masalan: 25)")
        await state.set_state(QazoHisobState.choosing_days)
    await callback.answer()

async def process_qazo_years(message: types.Message, state: FSMContext):
    """
    Processes the user's input for years of qazo prayers.
    """
    try:
        years = int(message.text.strip())
        if years <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❗ Iltimos, faqat musbat butun son kiriting.")

    user_id = message.from_user.id
    prayers = {p: 365 * years for p in prayer_names}

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        for p, c in prayers.items():
            cursor.execute("""
                INSERT INTO qazo (user_id, prayer_name, count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, prayer_name)
                DO UPDATE SET count = count + ?
            """, (user_id, p, c, c))
        conn.commit()

    await message.answer("✅ Yillik qazo hisoblandi.", reply_markup=main_menu())
    await state.clear()

async def process_qazo_months(message: types.Message, state: FSMContext):
    """
    Processes the user's input for months of qazo prayers.
    """
    try:
        months = int(message.text.strip())
        if months <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❗ Iltimos, faqat musbat butun son kiriting.")

    user_id = message.from_user.id
    prayers = {p: 30 * months for p in prayer_names}

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        for p, c in prayers.items():
            cursor.execute("""
                INSERT INTO qazo (user_id, prayer_name, count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, prayer_name)
                DO UPDATE SET count = count + ?
            """, (user_id, p, c, c))
        conn.commit()

    await message.answer("✅ Oylik qazo hisoblandi.", reply_markup=main_menu())
    await state.clear()

async def process_qazo_days(message: types.Message, state: FSMContext):
    """
    Processes the user's input for days of qazo prayers.
    """
    try:
        days = int(message.text.strip())
        if days <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❗ Iltimos, faqat musbat butun son kiriting.")

    user_id = message.from_user.id
    prayers = {p: days for p in prayer_names}

    with sqlite3.connect("qazo_bot.db") as conn:
        cursor = conn.cursor()
        for p, c in prayers.items():
            cursor.execute("""
                INSERT INTO qazo (user_id, prayer_name, count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, prayer_name)
                DO UPDATE SET count = count + ?
            """, (user_id, p, c, c))
        conn.commit()

    await message.answer("✅ Kunlik qazo hisoblandi.", reply_markup=main_menu())
    await state.clear()

async def noop_handler(callback: types.CallbackQuery):
    """
    Handles no-operation callback to prevent unnecessary responses.
    """
    await callback.answer()

async def back_to_menu(callback: types.CallbackQuery):
    """
    Deletes the current message to return to the main menu.
    """
    await callback.message.delete()

def register_handlers(dp: Dispatcher):
    """
    Registers all callback and message handlers for the qazo functionality.
    """
    dp.callback_query(F.data == "qazo_menu")(qazo_menu_handler)
    dp.callback_query(F.data == "qazo_hisoblash")(qazo_start)
    dp.callback_query(F.data.in_({"range_years", "range_months", "range_days"}))(handle_range_choice)
    dp.callback_query(F.data == "back_to_menu")(back_to_menu)
    dp.callback_query(F.data.startswith("inc_"))(increment_qazo)
    dp.callback_query(F.data.startswith("dec_"))(decrement_qazo)
    dp.callback_query(F.data == "noop")(noop_handler)
    dp.message(QazoHisobState.choosing_years)(process_qazo_years)
    dp.message(QazoHisobState.choosing_months)(process_qazo_months)
    dp.message(QazoHisobState.choosing_days)(process_qazo_days)