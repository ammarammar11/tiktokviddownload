import random
import re

import telegram
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from api import TikTokApiClient, Collection, Video, YouTubeApiClient
from logger import logger

tiktokApiClient = TikTokApiClient()
youtubeApiClient = YouTubeApiClient()


def is_tiktok_link(text: str) -> bool:
    tiktok_pattern = r"(https?://(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+)"
    return bool(re.match(tiktok_pattern, text))


def is_youtube_shorts_link(text: str) -> bool:
    shorts_pattern = r"(https?://(www\.)?youtube\.com/shorts/.+|https?://youtu\.be/.+)"
    return bool(re.match(shorts_pattern, text))


insults = [
    "Только честно, ты даун?",
    "Ну значит ты долбаеб!",
    "Животное безмозглое, научись думать!",
    "Да, да, да... И про кальмара! 🦑",
    "Долбаеб #1",
    "Долбаеб #2",
    "Ебало оффни, дура",
    "Паузу!",
    "Паузу, встала!",
    "Встала!",
    "Палку!",
    "Ха тьфу на тебе в ебало блядь",
    "Саша",
    "Дудецкая",
    "Шоколад",
    "Подружка дедуцкой",
    "Феталь",
    "Фетальный ребенок",
    "52",
    "Кальмар",
    "Никольская",
    "Ректал",
    "Ректальный шао",
    "Макака",
    "Никто никого не рвал, это полный бред",
    "У тебя пиздец на лице © Дамблдор",
    "🦑"
]


def rand_insult() -> str:
    return random.choice(insults)


def build_caption(user: telegram.User, url: str) -> str:
    user_id = user.id
    username = user.username or user.first_name
    user_link = f"[{username}](tg://user?id={user_id})"

    original = f"[оригинал]({url})"

    return fr"От {user_link} \- {original}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    message = update.message
    url = message.text
    chat_id = message.chat_id
    caption = build_caption(message.from_user, url)

    if not is_tiktok_link(url) and not is_youtube_shorts_link(url):
        if random.randint(1, 50) == 1:
            await update.message.reply_text(rand_insult())
        return

    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

    content = None
    try:
        if is_tiktok_link(url):
            content = tiktokApiClient.get_content(url)
        elif is_youtube_shorts_link(url):
            content = youtubeApiClient.get_content(url)
    except Exception as e:
        logger.error(f"Error getting content: {e}")
        await context.bot.send_message(update.message.chat_id,
                                       "Не удалось получить контент. Проверьте ссылку или попробуйте позже.")
        return

    try:
        if isinstance(content, Collection):
            with content as collection:
                media_group = []
                for img in collection.images[:10]:
                    if img.temp.size > 10 * 1024 * 1024:
                        continue

                    with open(img.temp.path, "rb") as image_file:
                        media_group.append(InputMediaPhoto(media=image_file.read()))

                if media_group:
                    await context.bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group,
                        caption=caption,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                    )
                    logger.info("Images sent successfully as media group")
                else:
                    logger.warning("No images to send")
                    await context.bot.send_message(update.message.chat_id,
                                                   "Не удалось подготовить изображения для отправки.")
                    return

                if collection.audio:
                    with open(collection.audio.temp.path, "rb") as audio_file:
                        await context.bot.send_audio(
                            chat_id=chat_id,
                            audio=audio_file,
                            title=collection.audio.title,
                            caption=caption,
                            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                        )
                        logger.info("Audio sent successfully as audio")

        elif isinstance(content, Video):
            with content as video:
                if video.temp.size > 50 * 1024 * 1024:
                    await context.bot.send_message(update.message.chat_id, "Видео слишком большое.")
                    return
                with open(video.temp.path, "rb") as video_file:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        supports_streaming=True,
                        caption=caption,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                    )
                    logger.info("Video sent successfully as media")

    except Exception as e:
        logger.error(f"Error sending content: {e}")
        await context.bot.send_message(update.message.chat_id, "Не удалось отправить контент. Попробуйте позже.")


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 1:
        try:
            n = int(context.args[0])
            await update.message.reply_text(str(random.randint(1, n)))
        except ValueError:
            await update.message.reply_text(rand_insult())
        return
    elif len(context.args) == 2:
        try:
            n = int(context.args[0])
            m = int(context.args[1])
            await update.message.reply_text(str(random.randint(n, m)))
        except ValueError:
            await update.message.reply_text(rand_insult())
        return
    elif len(context.args) > 2:
        await update.message.reply_text(rand_insult())
        return

    await update.message.reply_text(str(random.randint(100000, 1000000 - 1)))


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) <= 1:
        await context.bot.send_message(
            update.message.chat_id,
            rand_insult()
        )
        return

    await context.bot.send_message(
        update.message.chat_id,
        random.choice(context.args)
    )
