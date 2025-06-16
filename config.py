import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway uchun qo'shimcha sozlamalar
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID .env faylida topilmadi yoki noto'g'ri!")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env faylida topilmadi yoki noto'g'ri!")


class Config:
    # Bot sozlamalari
    BOT_TOKEN: str = BOT_TOKEN

    # Database sozlamalari
    DATABASE_URL: Optional[str] = DATABASE_URL
    PGHOST: str = os.getenv('PGHOST', 'localhost')
    PGPORT: str = os.getenv('PGPORT', '5432')
    PGDATABASE: str = os.getenv('PGDATABASE', 'qazobot')
    PGUSER: str = os.getenv('PGUSER', 'postgres')
    PGPASSWORD: str = os.getenv('PGPASSWORD', '')

    # Railway sozlamalari
    RAILWAY_ENVIRONMENT: str = RAILWAY_ENVIRONMENT
    PORT: int = PORT

    # Bot sozlamalari
    WEBHOOK_URL: Optional[str] = WEBHOOK_URL
    WEBHOOK_PATH: str = WEBHOOK_PATH

    # Admin sozlamalari
    ADMIN_IDS: list = [ADMIN_ID]

    # Logging sozlamalari
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Sozlamalarni tekshirish"""
        # if not cls.BOT_TOKEN:
        #     raise ValueError("BOT_TOKEN environment variable is required")

        if cls.RAILWAY_ENVIRONMENT == 'production' and not cls.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is required for production")

# Sozlamalarni tekshirish
# Config.validate()
