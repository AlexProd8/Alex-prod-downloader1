import logging
import os
import tempfile
import traceback
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем состояние диалога
VIDEO_LINK = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет!\nОтправьте ссылку на видео с TikTok или Instagram, и я попробую его скачать и отправить обратно."
    )
    return VIDEO_LINK

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()
    
    # Простая проверка корректности ссылки
    if not url.startswith("http"):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку.")
        return VIDEO_LINK

    await update.message.reply_text("Скачиваю видео, пожалуйста, подождите...")

    # Настройки для yt-dlp
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',
        'format': 'mp4',
        'quiet': True,
        # Примечание: опции для удаления водяных знаков зависят от платформы и видео.
        # В большинстве случаев скачивается то, что возвращает платформа.
    }
    
    try:
        # Создаем временную директорию для скачивания
        with tempfile.TemporaryDirectory() as tmpdirname:
            ydl_opts['outtmpl'] = os.path.join(tmpdirname, '%(id)s.%(ext)s')
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
            
            # Отправляем видео пользователю
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
    except Exception:
        logger.error("Ошибка при скачивании видео:\n%s", traceback.format_exc())
        await update.message.reply_text(
            "Не удалось скачать видео. Возможно, ссылка некорректна или видео недоступно."
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            VIDEO_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
