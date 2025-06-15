import sqlite3
import logging
from datetime import datetime, timedelta
import os
from config import ADMIN_ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DB_NAME = "qazo_bot.db"

def init_db():
    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda")
    print("📂 Baza joylashuvi:", os.path.abspath(DB_NAME))
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Users jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    created_at TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    is_main_admin BOOLEAN DEFAULT 0
                )
            """)
            # Qazo jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qazo (
                    user_id INTEGER,
                    prayer_name TEXT,
                    count INTEGER DEFAULT 0,
                    UNIQUE(user_id, prayer_name),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            # Admins jadvali (eskirgan, endi users da boshqariladi)
            cursor.execute("DROP TABLE IF EXISTS admins")
            # Channels jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY
                )
            """)
            # FAQ jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    answer TEXT,
                    video_url TEXT
                )
            """)
            conn.commit()
            logger.info("Ma'lumotlar bazasi muvaffaqiyatli yaratildi")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini yaratishda xato: {e}")

def user_exists(user_id: int) -> bool:
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"user_exists tekshiruvida xato: user_id={user_id}, {e}")
        return False

def add_user(user_id: int, full_name: str):
    if user_exists(user_id):
        return
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, full_name, created_at)
                VALUES (?, ?, ?)
            """, (user_id, full_name, datetime.now().isoformat()))
            conn.commit()
            logger.info(f"Yangi foydalanuvchi qo‘shildi: user_id={user_id}")
    except Exception as e:
        logger.error(f"add_user da xato: user_id={user_id}, {e}")

def is_admin(user_id: int) -> bool:
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin, is_main_admin FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                is_admin_val, is_main_admin_val = result
                return bool(is_admin_val) or bool(is_main_admin_val) or user_id == ADMIN_ID
            return user_id == ADMIN_ID
    except Exception as e:
        logger.error(f"is_admin tekshiruvida xato: user_id={user_id}, {e}")
        return False

def add_admin(user_id: int) -> bool:
    if not user_exists(user_id):
        logger.warning(f"add_admin: Foydalanuvchi topilmadi: user_id={user_id}")
        return False
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if user_id == ADMIN_ID:
                cursor.execute("UPDATE users SET is_main_admin = 1 WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Admin qo‘shildi: user_id={user_id}")
            return True
    except Exception as e:
        logger.error(f"add_admin da xato: user_id={user_id}, {e}")
        return False

def remove_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        logger.warning(f"remove_admin: Asosiy adminni o‘chirib bo‘lmaydi: user_id={user_id}")
        return False
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_admin = 0, is_main_admin = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Admin o‘chirildi: user_id={user_id}")
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"remove_admin da xato: user_id={user_id}, {e}")
        return False

def get_all_admins():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_admin = 1 OR is_main_admin = 1")
            admins = [row[0] for row in cursor.fetchall()]
            if ADMIN_ID and ADMIN_ID not in admins:
                admins.append(ADMIN_ID)
            logger.info(f"Adminlar ro‘yxati olindi: {admins}")
            return sorted(admins)
    except Exception as e:
        logger.error(f"get_all_admins da xato: {e}")
        return []

def get_all_users():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = [{"user_id": row[0]} for row in cursor.fetchall()]
            logger.info(f"Foydalanuvchilar ro‘yxati olindi: {len(users)} users")
            return users
    except Exception as e:
        logger.error(f"get_all_users da xato: {e}")
        return []

def get_stats():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            # Daily (bugungi kun qo‘shilganlar)
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (datetime.now().date().isoformat(),))
            daily = cursor.fetchone()[0]
            # Weekly (so‘nggi 7 kun)
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?",
                          ((datetime.now() - timedelta(days=7)).isoformat(),))
            weekly = cursor.fetchone()[0]
            # Monthly (so‘nggi 30 kun)
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?",
                          ((datetime.now() - timedelta(days=30)).isoformat(),))
            monthly = cursor.fetchone()[0]
            logger.info(f"Statistika olindi: total={total}, daily={daily}, weekly={weekly}, monthly={monthly}")
            return {
                "daily": daily,
                "weekly": weekly,
                "monthly": monthly,
                "total": total
            }
    except Exception as e:
        logger.error(f"get_stats da xato: {e}")
        return {"daily": 0, "weekly": 0, "monthly": 0, "total": 0}

def add_channel(channel_id: str):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO channels (channel_id) VALUES (?)", (channel_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Kanal qo‘shildi: channel_id={channel_id}")
            else:
                logger.info(f"Kanal allaqachon mavjud: channel_id={channel_id}")
    except Exception as e:
        logger.error(f"add_channel da xato: channel_id={channel_id}, {e}")

def remove_channel(channel_id: str):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Kanal o‘chirildi: channel_id={channel_id}")
            else:
                logger.warning(f"Kanal topilmadi yoki allaqachon o‘chirilgan: channel_id={channel_id}")
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"remove_channel da xato: channel_id={channel_id}, {e}")
        return False

def get_all_channels():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT channel_id FROM channels")
            channels = [row[0] for row in cursor.fetchall()]
            logger.info(f"Kanallar ro‘yxati: {channels}")
            return channels
    except Exception as e:
        logger.error(f"get_all_channels da xato: {e}")
        return []

def add_faq(question: str, answer: str, video_url: str = None):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO faq (question, answer, video_url)
                VALUES (?, ?, ?)
            """, (question, answer, video_url))
            conn.commit()
            logger.info(f"FAQ qo‘shildi: question={question}")
    except Exception as e:
        logger.error(f"add_faq da xato: {e}")

def get_all_faq():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, question, answer, video_url FROM faq")
            rows = cursor.fetchall()
            faqs = [{"id": row[0], "question": row[1], "answer": row[2], "video_url": row[3]} for row in rows]
            logger.info(f"FAQ ro‘yxati olindi: {len(faqs)} savol")
            return faqs
    except Exception as e:
        logger.error(f"get_all_faq da xato: {e}")
        return []

def get_user_qazo(user_id: int) -> dict:
    prayers = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            qazo_counts = {}
            for prayer in prayers:
                cursor.execute("SELECT count FROM qazo WHERE user_id = ? AND prayer_name = ?", (user_id, prayer))
                result = cursor.fetchone()
                count = int(result[0]) if result else 0
                qazo_counts[prayer] = count
            logger.info(f"Qazo ma'lumotlari olingan: user_id={user_id}")
            return qazo_counts
    except Exception as e:
        logger.error(f"get_user_qazo da xato: user_id={user_id}, {e}")
        return {prayer: 0 for prayer in prayers}

def update_qazo_count(user_id: int, prayer: str, delta: int):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO qazo (user_id, prayer_name, count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, prayer_name)
                DO UPDATE SET count = MAX(count + ?, 0)
            """, (user_id, prayer, max(delta, 0), delta))
            conn.commit()
            logger.info(f"Qazo hisobi yangilandi: user_id={user_id}, prayer={prayer}, delta={delta}")
    except Exception as e:
        logger.error(f"update_qazo_count da xato: user_id={user_id}, prayer={prayer}, {e}")

def is_user_exists(user_id: int) -> bool:
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return bool(result)
    except Exception as e:
        logger.error(f"is_user_exists da xato: user_id={user_id}, {e}")
        return False