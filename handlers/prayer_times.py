import logging
from datetime import datetime

from aiogram import types, Dispatcher, F, Router
from aiogram.enums.parse_mode import ParseMode

from keyboards.default import prayer_regions_menu, prayer_cities_menu, prayer_times_menu
from utils.namoz_parser import get_prayer_times

router = Router()

@router.callback_query(F.data == "namoz_vaqtlari")
async def prayer_region_menu(callback: types.CallbackQuery):
    try:
        kb = prayer_regions_menu()
        await callback.message.edit_text("🗺 Qaysi viloyatdansiz?", reply_markup=kb)
        logging.info(f"Viloyatlar menyusi ko'rsatildi: user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"prayer_region_menu da xato: {e}, user_id={callback.from_user.id}")
        await callback.message.edit_text("❌ Viloyat tanlashda xatolik.", parse_mode=ParseMode.HTML)
    await callback.answer()

@router.callback_query(F.data.startswith("region_"))
async def city_list(callback: types.CallbackQuery):
    try:
        region = callback.data.replace("region_", "")
        kb = prayer_cities_menu(region)
        await callback.message.edit_text(
            f"🏙 {region}dagi qaysi shahar/tumandasiz?",
            reply_markup=kb
        )
        logging.info(f"Shaharlar menyusi ko'rsatildi: region={region}, user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"city_list da xato: {e}, callback.data={callback.data}")
        await callback.message.edit_text("❌ Viloyatni tanlashda xatolik.", parse_mode=ParseMode.HTML)
    await callback.answer()

@router.callback_query(F.data.startswith("city_"))
async def show_times(callback: types.CallbackQuery):
    try:
        full_data = callback.data.replace("city_", "")
        city, region = full_data.split("_", 1)
        times = get_prayer_times(city)
        if not times:
            await callback.message.edit_text("❌ Namoz vaqtlarini olishda xatolik.", parse_mode=ParseMode.HTML)
            await callback.answer()
            return

        keys = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
        uz_names = {
            "Fajr": "Bomdod", "Sunrise": "Quyosh", "Dhuhr": "Peshin",
            "Asr": "Asr", "Maghrib": "Shom", "Isha": "Xufton"
        }

        current_date = datetime.now().date()
        text = f"🕌 <b>{city} shahri uchun {current_date} namoz vaqtlari:</b>\n\n"
        for k in keys:
            if k in times:
                text += f"• {uz_names[k]}: {times[k]}\n"

        kb = prayer_times_menu(region)
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        logging.info(f"Namoz vaqtlari ko'rsatildi: city={city}, user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"show_times da xato: {e}, callback.data={callback.data}")
        await callback.message.edit_text("❌ Namoz vaqtlarini ko'rsatishda xatolik.", parse_mode=ParseMode.HTML)
    await callback.answer()

@router.callback_query(F.data == "back_to_prayer_regions")
async def back_to_prayer_regions(callback: types.CallbackQuery):
    await prayer_region_menu(callback)

@router.callback_query(F.data.startswith("back_to_prayer_cities_"))
async def back_to_prayer_cities(callback: types.CallbackQuery):
    try:
        region = callback.data.replace("back_to_prayer_cities_", "")
        kb = prayer_cities_menu(region)
        await callback.message.edit_text(
            f"🏙 {region}dagi qaysi shahar/tumandasiz?",
            reply_markup=kb
        )
        logging.info(f"Shaharlar menyusiga qaytildi: region={region}, user_id={callback.from_user.id}")
    except Exception as e:
        logging.error(f"back_to_prayer_cities da xato: {e}, callback.data={callback.data}")
        await callback.message.edit_text("❌ Shahar tanlashda xatolik.", parse_mode=ParseMode.HTML)
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.include_router(router)
