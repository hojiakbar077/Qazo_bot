from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.regions import regions


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Qazolarim", callback_data="qazo_menu"),
            InlineKeyboardButton(text="➕ Qazo hisoblash", callback_data="qazo_hisoblash")
        ],
        [
            InlineKeyboardButton(text="📅 Namoz vaqtlari", callback_data="namoz_vaqtlari"),
            InlineKeyboardButton(text="❓ Tez-tez so‘raladigan savollar", callback_data="faq")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_menu(is_main_admin: bool = False):
    keyboard = [
        [
            InlineKeyboardButton(text="📈 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="admin_add_channel"),
            InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="admin_remove_channel")
        ],
        [
            InlineKeyboardButton(text="📋 Kanallar ro‘yxati", callback_data="admin_list_channels"),
        ],
        [InlineKeyboardButton(text="➕ FAQ qo‘shish", callback_data="admin_add_faq")]
    ]
    if is_main_admin:
        keyboard[2].append(InlineKeyboardButton(text="👥 Adminlarni ko‘rish", callback_data="admin_list_admins"))
        keyboard.append([
            InlineKeyboardButton(text="👤 Yangi admin qo‘shish", callback_data="admin_add_admin"),
            InlineKeyboardButton(text="🗑 Admin o‘chirish", callback_data="admin_remove_admin")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_button_only():
    keyboard = [
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def qazo_menu(counts):
    prayer_names = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]
    keyboard = []
    for p in prayer_names:
        count = counts.get(p, 0)
        prayer_lower = p.lower()
        keyboard.append([InlineKeyboardButton(text=p.lower(), callback_data="noop")])
        keyboard.append([
            InlineKeyboardButton(text="➖", callback_data=f"dec_{prayer_lower}"),
            InlineKeyboardButton(text=str(count), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"inc_{prayer_lower}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def qazo_hisoblash_menu():
    keyboard = [
        [InlineKeyboardButton(text="❗ Ha, 1 yildan oshli", callback_data="range_years")],
        [InlineKeyboardButton(text="✅ Yo‘q, oylik hisoblayman", callback_data="range_months")],
        [InlineKeyboardButton(text="📖 Yo‘q, kunlik hisoblayman", callback_data="range_days")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def prayer_regions_menu():
    keyboard = [
        [InlineKeyboardButton(text=region, callback_data=f"region_{region}")]
        for region in regions.keys()
    ] + [[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def prayer_cities_menu(region):
    cities = regions.get(region, [])
    keyboard = [
        [InlineKeyboardButton(text=city, callback_data=f"city_{city}_{region}")]
        for city in cities
    ] + [[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_prayer_regions")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def prayer_times_menu(region):
    keyboard = [[InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back_to_prayer_cities_{region}")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def check_subscription_menu(channels=None):
    if not channels:
        return InlineKeyboardMarkup(inline_keyboard=[])
    keyboard = [
        [InlineKeyboardButton(text=f"📢 {ch}", url=f"https://t.me/{ch[1:] if ch.startswith('@') else ch}")]
        for ch in channels
    ] + [[InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subs")],
         [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def faq_menu(faqs):
    keyboard = [
        [InlineKeyboardButton(text=faq["question"], callback_data=f"faq_answer_{faq['id']}")]
        for faq in faqs
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_faq_menu():
    keyboard = [
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_faq_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)