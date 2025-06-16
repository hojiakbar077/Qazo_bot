import logging
from datetime import datetime, timedelta
import os
from config import ADMIN_ID, DATABASE_URL
import asyncpg
from typing import Optional, List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Connection pool
pool: Optional[asyncpg.Pool] = None


async def get_connection():
    global pool
    if pool is None:
        await init_db()
    return pool


async def init_db():
    global pool
    logger.info("PostgreSQL ma'lumotlar bazasi ishga tushirilmoqda")
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )

        async with pool.acquire() as conn:
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   user_id
                                   BIGINT
                                   PRIMARY
                                   KEY,
                                   full_name
                                   TEXT,
                                   created_at
                                   TIMESTAMP,
                                   is_admin
                                   BOOLEAN
                                   DEFAULT
                                   FALSE,
                                   is_main_admin
                                   BOOLEAN
                                   DEFAULT
                                   FALSE
                               )
                               """)
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS qazo
                               (
                                   user_id
                                   BIGINT,
                                   prayer_name
                                   TEXT,
                                   count
                                   INTEGER
                                   DEFAULT
                                   0,
                                   UNIQUE
                               (
                                   user_id,
                                   prayer_name
                               ),
                                   FOREIGN KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   user_id
                               ) ON DELETE CASCADE
                                   )
                               """)
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS channels
                               (
                                   channel_id
                                   TEXT
                                   PRIMARY
                                   KEY
                               )
                               """)
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS faq
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   question
                                   TEXT,
                                   answer
                                   TEXT,
                                   video_url
                                   TEXT
                               )
                               """)
        logger.info("PostgreSQL ma'lumotlar bazasi yaratildi")
    except Exception as e:
        logger.error(f"init_db xatoligi: {e}")
        raise


async def user_exists(user_id: int) -> bool:
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1 FROM users WHERE user_id = $1", user_id)
            return result is not None
    except Exception as e:
        logger.error(f"user_exists xato: {e}")
        return False


async def add_user(user_id: int, full_name: str):
    if await user_exists(user_id):
        return
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            await conn.execute("""
                               INSERT INTO users (user_id, full_name, created_at)
                               VALUES ($1, $2, $3)
                               """, user_id, full_name, datetime.now())
            logger.info(f"Foydalanuvchi qo'shildi: {user_id}")
    except Exception as e:
        logger.error(f"add_user xato: {e}")


async def is_admin(user_id: int) -> bool:
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("SELECT is_admin, is_main_admin FROM users WHERE user_id = $1", user_id)
            if result:
                return result['is_admin'] or result['is_main_admin'] or user_id == ADMIN_ID
            return user_id == ADMIN_ID
    except Exception as e:
        logger.error(f"is_admin xato: {e}")
        return False


async def add_admin(user_id: int) -> bool:
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            if user_id == ADMIN_ID:
                await conn.execute("UPDATE users SET is_main_admin = TRUE WHERE user_id = $1", user_id)
            else:
                await conn.execute("UPDATE users SET is_admin = TRUE WHERE user_id = $1", user_id)
            logger.info(f"Admin qo'shildi: {user_id}")
            return True
    except Exception as e:
        logger.error(f"add_admin xato: {e}")
        return False


async def remove_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return False
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            result = await conn.execute("UPDATE users SET is_admin = FALSE, is_main_admin = FALSE WHERE user_id = $1",
                                        user_id)
            return result != "UPDATE 0"
    except Exception as e:
        logger.error(f"remove_admin xato: {e}")
        return False


async def get_all_admins():
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users WHERE is_admin = TRUE OR is_main_admin = TRUE")
            admins = [row['user_id'] for row in rows]
            if ADMIN_ID and ADMIN_ID not in admins:
                admins.append(ADMIN_ID)
            return sorted(admins)
    except Exception as e:
        logger.error(f"get_all_admins xato: {e}")
        return []


async def get_all_users():
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users")
            return [{"user_id": row['user_id']} for row in rows]
    except Exception as e:
        logger.error(f"get_all_users xato: {e}")
        return []


async def get_stats():
    try:
        now = datetime.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        pool = await get_connection()
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            daily = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", today)
            weekly = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", week_ago)
            monthly = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= $1", month_ago)

            return {"total": total, "daily": daily, "weekly": weekly, "monthly": monthly}
    except Exception as e:
        logger.error(f"get_stats xato: {e}")
        return {"total": 0, "daily": 0, "weekly": 0, "monthly": 0}


async def add_channel(channel_id: str):
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO channels (channel_id) VALUES ($1) ON CONFLICT DO NOTHING", channel_id)
    except Exception as e:
        logger.error(f"add_channel xato: {e}")


async def remove_channel(channel_id: str):
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)
            return result != "DELETE 0"
    except Exception as e:
        logger.error(f"remove_channel xato: {e}")
        return False


async def get_all_channels():
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT channel_id FROM channels")
            return [row['channel_id'] for row in rows]
    except Exception as e:
        logger.error(f"get_all_channels xato: {e}")
        return []


async def add_faq(question: str, answer: str, video_url: str = None):
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            await conn.execute("""
                               INSERT INTO faq (question, answer, video_url)
                               VALUES ($1, $2, $3)
                               """, question, answer, video_url)
    except Exception as e:
        logger.error(f"add_faq xato: {e}")


async def get_all_faq():
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, question, answer, video_url FROM faq")
            return [
                {"id": row['id'], "question": row['question'], "answer": row['answer'], "video_url": row['video_url']}
                for row in rows]
    except Exception as e:
        logger.error(f"get_all_faq xato: {e}")
        return []


async def get_user_qazo(user_id: int) -> dict:
    prayers = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]
    qazo_counts = {prayer: 0 for prayer in prayers}
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            for prayer in prayers:
                result = await conn.fetchval("""
                                             SELECT count
                                             FROM qazo
                                             WHERE user_id = $1
                                               AND prayer_name = $2
                                             """, user_id, prayer)
                if result:
                    qazo_counts[prayer] = result
        return qazo_counts
    except Exception as e:
        logger.error(f"get_user_qazo xato: {e}")
        return qazo_counts


async def update_qazo_count(user_id: int, prayer: str, delta: int):
    try:
        pool = await get_connection()
        async with pool.acquire() as conn:
            await conn.execute("""
                               INSERT INTO qazo (user_id, prayer_name, count)
                               VALUES ($1, $2, GREATEST($3, 0)) ON CONFLICT (user_id, prayer_name)
                DO
                               UPDATE SET count = GREATEST(qazo.count + $4, 0)
                               """, user_id, prayer, delta, delta)
    except Exception as e:
        logger.error(f"update_qazo_count xato: {e}")


async def is_user_exists(user_id: int) -> bool:
    return await user_exists(user_id)


async def close_db():
    global pool
    if pool:
        await pool.close()
        logger.info("Ma'lumotlar bazasi ulanishi yopildi")
