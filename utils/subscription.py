from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import logging

async def check_subscription(user_id: int, bot: Bot, required_channels: list) -> bool:
    for channel in required_channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                logging.warning(f"User not subscribed: user_id={user_id}, channel={channel}")
                return False
        except TelegramBadRequest as e:
            logging.error(f"TelegramBadRequest in check_subscription: channel={channel}, user_id={user_id}, {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in check_subscription: channel={channel}, user_id={user_id}, {e}")
            return False
    logging.info(f"User subscribed to all channels: user_id={user_id}")
    return True