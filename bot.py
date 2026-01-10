import os
import asyncio
import logging
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    BufferedInputFile  # Добавляем для надежности
)
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)

# ------------------ CONFIG ------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ------------------ FILES ------------------

# Убедись, что пути правильные
BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"

FILES = {
    "anxiety": ("Тревожность", FILES_DIR / "anxiety.pdf"),
    "burnout": ("Выгорание", FILES_DIR / "burnout.pdf"),
    "growth": ("Личностный рост", FILES_DIR / "growth.pdf"),
    "relations": ("Отношения", FILES_DIR / "relations.pdf"),
    "selfesteem": ("Самооценка", FILES_DIR / "selfesteem.pdf"),
    "sleep": ("Сон", FILES_DIR / "sleep.pdf"),
}

# Логируем наличие файлов
logger.info("Проверка файлов:")
for key, (title, path) in FILES.items():
    if path.exists():
        size = path.stat().st_size
        logger.info(f"✅ {key}: {title} - {size:,} байт")
    else:
        logger.error(f"❌ {key}: {title} - ФАЙЛ НЕ НАЙДЕН: {path}")

# ------------------ KEYBOARD ------------------

def files_keyboard() -> InlineKeyboardMarkup:
    keyboard = []

    for key, (title, _) in FILES.items():
        keyboard.append(
            [InlineKeyboardButton(text=title, callback_data=f"file:{key}")]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ------------------ HANDLERS ------------------

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Выбери тему, и я пришлю тебе материал:",
        reply_markup=files_keyboard(),
    )

@dp.callback_query(lambda c: c.data.startswith("file:"))
async def send_file(callback: types.CallbackQuery):
    key = callback.data.split(":")[1]
    
    logger.info(f"Запрос файла: {key}")
    
    if key not in FILES:
        await callback.answer("Файл не найден", show_alert=True)
        return

    title, path = FILES[key]
    
    # Проверяем существование файла
    if not path.exists():
        logger.error(f"Файл не существует: {path}")
        await callback.answer("Файл отсутствует на сервере", show_alert=True)
        return
    
    try:
        # Получаем размер файла
        file_size = path.stat().st_size
        logger.info(f"Отправка файла: {title}, размер: {file_size:,} байт")
        
        # Уведомляем пользователя
        await callback.answer(f"📤 Отправляю {title}...")
        
        # Пробуем разные способы отправки
        
        # Способ 1: FSInputFile (простой)
        document = FSInputFile(path=path)
        
        # Способ 2: BufferedInputFile (надежнее для больших файлов)
        # with open(path, 'rb') as f:
        #     file_data = f.read()
        # document = BufferedInputFile(file=file_data, filename=path.name)
        
        # Отправляем файл
        await callback.message.answer_document(
            document=document,
            caption=f"📄 {title}"
        )
        
        logger.info(f"✅ Файл отправлен: {title}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке файла {title}: {str(e)}")
        await callback.answer(f"Ошибка: {str(e)[:100]}", show_alert=True)

# ------------------ WEBHOOK APP ------------------

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    
    # Проверяем доступность файлов при старте
    available = sum(1 for _, (_, path) in FILES.items() if path.exists())
    logger.info(f"📁 Доступно файлов: {available}/{len(FILES)}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("📴 Webhook удален")

def main():
    app = web.Application()
    
    # Добавляем проверку работоспособности
    async def health_check(request):
        return web.Response(text="Bot is running")
    
    app.router.add_get('/health', health_check)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)
    
    logger.info(f"🚀 Бот запускается на порту {PORT}")
    logger.info(f"🌐 Webhook URL: {WEBHOOK_URL}")
    logger.info(f"📁 Текущая директория: {BASE_DIR}")
    
    web.run_app(app, port=PORT, access_log=logger)

if __name__ == "__main__":
    main()

