import logging
from datetime import datetime, timedelta
import os
from config import ADMIN_ID, DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    logger.info("PostgreSQL ma'lumotlar bazasi ishga tushirilmoqda")
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        full_name TEXT,
                        created_at TIMESTAMP,
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_main_admin BOOLEAN DEFAULT FALSE
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS qazo (
                        user_id BIGINT,
                        prayer_name TEXT,
                        count INTEGER DEFAULT 0,
                        UNIQUE(user_id, prayer_name),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS channels (
                        channel_id TEXT PRIMARY KEY
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS faq (
                        id SERIAL PRIMARY KEY,
                        question TEXT,
                        answer TEXT,
                        video_url TEXT
                    )
                """)
                conn.commit()
                logger.info("PostgreSQL ma'lumotlar bazasi yaratildi")
    except Exception as e:
        logger.error(f"init_db xatoligi: {e}")

def user_exists(user_id: int) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"user_exists xato: {e}")
        return False

def add_user(user_id: int, full_name: str):
    if user_exists(user_id):
        return
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (user_id, full_name, created_at)
                    VALUES (%s, %s, %s)
                """, (user_id, full_name, datetime.now()))
                conn.commit()
                logger.info(f"Foydalanuvchi qo‘shildi: {user_id}")
    except Exception as e:
        logger.error(f"add_user xato: {e}")

def is_admin(user_id: int) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT is_admin, is_main_admin FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                if result:
                    return result[0] or result[1] or user_id == ADMIN_ID
                return user_id == ADMIN_ID
    except Exception as e:
        logger.error(f"is_admin xato: {e}")
        return False

def add_admin(user_id: int) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if user_id == ADMIN_ID:
                    cursor.execute("UPDATE users SET is_main_admin = TRUE WHERE user_id = %s", (user_id,))
                else:
                    cursor.execute("UPDATE users SET is_admin = TRUE WHERE user_id = %s", (user_id,))
                conn.commit()
                logger.info(f"Admin qo‘shildi: {user_id}")
                return True
    except Exception as e:
        logger.error(f"add_admin xato: {e}")
        return False

def remove_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return False
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET is_admin = FALSE, is_main_admin = FALSE WHERE user_id = %s", (user_id,))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"remove_admin xato: {e}")
        return False

def get_all_admins():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE is_admin = TRUE OR is_main_admin = TRUE")
                admins = [row[0] for row in cursor.fetchall()]
                if ADMIN_ID and ADMIN_ID not in admins:
                    admins.append(ADMIN_ID)
                return sorted(admins)
    except Exception as e:
        logger.error(f"get_all_admins xato: {e}")
        return []

def get_all_users():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users")
                return [{"user_id": row[0]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"get_all_users xato: {e}")
        return []

def get_stats():
    try:
        now = datetime.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                total = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (today,))
                daily = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (week_ago,))
                weekly = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (month_ago,))
                monthly = cursor.fetchone()[0]

                return {"total": total, "daily": daily, "weekly": weekly, "monthly": monthly}
    except Exception as e:
        logger.error(f"get_stats xato: {e}")
        return {"total": 0, "daily": 0, "weekly": 0, "monthly": 0}

def add_channel(channel_id: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO channels (channel_id) VALUES (%s) ON CONFLICT DO NOTHING", (channel_id,))
                conn.commit()
    except Exception as e:
        logger.error(f"add_channel xato: {e}")

def remove_channel(channel_id: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"remove_channel xato: {e}")
        return False

def get_all_channels():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT channel_id FROM channels")
                return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"get_all_channels xato: {e}")
        return []

def add_faq(question: str, answer: str, video_url: str = None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO faq (question, answer, video_url)
                    VALUES (%s, %s, %s)
                """, (question, answer, video_url))
                conn.commit()
    except Exception as e:
        logger.error(f"add_faq xato: {e}")

def get_all_faq():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, question, answer, video_url FROM faq")
                return [{"id": row[0], "question": row[1], "answer": row[2], "video_url": row[3]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"get_all_faq xato: {e}")
        return []

def get_user_qazo(user_id: int) -> dict:
    prayers = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]
    qazo_counts = {prayer: 0 for prayer in prayers}
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for prayer in prayers:
                    cursor.execute("""
                        SELECT count FROM qazo WHERE user_id = %s AND prayer_name = %s
                    """, (user_id, prayer))
                    result = cursor.fetchone()
                    if result:
                        qazo_counts[prayer] = result[0]
        return qazo_counts
    except Exception as e:
        logger.error(f"get_user_qazo xato: {e}")
        return qazo_counts

def update_qazo_count(user_id: int, prayer: str, delta: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO qazo (user_id, prayer_name, count)
                    VALUES (%s, %s, GREATEST(%s, 0))
                    ON CONFLICT (user_id, prayer_name)
                    DO UPDATE SET count = GREATEST(qazo.count + %s, 0)
                """, (user_id, prayer, delta, delta))
                conn.commit()
    except Exception as e:
        logger.error(f"update_qazo_count xato: {e}")

def is_user_exists(user_id: int) -> bool:
    return user_exists(user_id)