import os
import logging
from pathlib import Path
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ==================== КОНФИГУРАЦИЯ ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8510415452:AAGeHIEFqF7ZZGBHWIrvDKCBfrONGuxc19E"

# Webhook URL (Render автоматически дает домен)
WEBHOOK_HOST = "https://bot-psychologist-1-utv7.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

PORT = int(os.getenv("PORT", 10000))

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== ФАЙЛЫ ====================
BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"

# Проверяем папку с файлами
if not FILES_DIR.exists():
    logger.warning(f"Папка files не найдена! Создаю...")
    FILES_DIR.mkdir()

FILES = {
    "anxiety": ("🧠 Тревожность", FILES_DIR / "anxiety.pdf"),
    "burnout": ("🔥 Выгорание", FILES_DIR / "burnout.pdf"),
    "growth": ("🌱 Личностный рост", FILES_DIR / "growth.pdf"),
    "relations": ("💬 Отношения", FILES_DIR / "relations.pdf"),
    "selfesteem": ("❤️ Самооценка", FILES_DIR / "selfesteem.pdf"),
    "sleep": ("😴 Сон", FILES_DIR / "sleep.pdf"),
}

# Логируем файлы
logger.info("=" * 50)
logger.info("ПРОВЕРКА ФАЙЛОВ:")
for key, (title, path) in FILES.items():
    if path.exists():
        size_kb = path.stat().st_size / 1024
        logger.info(f"✅ {title:20} - {size_kb:.1f} КБ")
    else:
        logger.error(f"❌ {title:20} - НЕ НАЙДЕН: {path}")
logger.info("=" * 50)

# ==================== КЛАВИАТУРА ====================
def get_keyboard():
    buttons = []
    for key, (title, _) in FILES.items():
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"file:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==================== ОБРАБОТЧИКИ ====================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    logger.info(f"📩 /start от пользователя {message.from_user.id}")
    
    await message.answer(
        "👋 *Привет! Я бот-помощник психолога.*\n\n"
        "Выберите тему, чтобы получить материал:",
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 *Помощь*\n\n"
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - эта справка\n\n"
        "Просто выберите тему из меню ниже.",
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith("file:"))
async def process_file(callback: types.CallbackQuery):
    """Обработчик выбора файла"""
    key = callback.data.split(":")[1]
    
    if key not in FILES:
        await callback.answer("❌ Ошибка: файл не найден", show_alert=True)
        return
    
    title, path = FILES[key]
    logger.info(f"📤 Запрос файла: {title} от {callback.from_user.id}")
    
    if not path.exists():
        await callback.answer("❌ Файл временно недоступен", show_alert=True)
        return
    
    try:
        # Уведомляем пользователя
        await callback.answer(f"📤 Отправляю {title}...")
        
        # Читаем файл
        with open(path, 'rb') as f:
            file_data = f.read()
        
        # Проверяем размер
        file_size = len(file_data)
        if file_size > 50 * 1024 * 1024:  # 50 MB лимит Telegram
            await callback.message.answer(f"⚠️ Файл слишком большой ({file_size//(1024*1024)} МБ)")
            return
        
        # Отправляем
        document = BufferedInputFile(file=file_data, filename=path.name)
        await callback.message.answer_document(
            document=document,
            caption=f"📄 {title}"
        )
        
        logger.info(f"✅ Файл отправлен: {title}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки {title}: {str(e)}")
        await callback.answer("❌ Ошибка при отправке", show_alert=True)

@dp.message()
async def other_messages(message: types.Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "🤔 Я понимаю только команды /start и /help\n"
        "Или выберите тему из меню:",
        reply_markup=get_keyboard()
    )

# ==================== WEBHOOK НАСТРОЙКИ ====================
async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("🔄 Устанавливаю webhook...")
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    
    # Информация о боте
    me = await bot.get_me()
    logger.info(f"🤖 Бот: @{me.username} ({me.first_name})")

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("🔄 Удаляю webhook...")
    await bot.delete_webhook()
    logger.info("✅ Webhook удален")

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
def main():
    """Основная функция запуска"""
    app = web.Application()
    
    # Health check endpoint (обязательно для Render!)
    async def health_check(request):
        return web.Response(text="🚀 Bot is running!")
    
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Регистрируем обработчики
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Регистрируем webhook обработчик
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    
    logger.info("=" * 50)
    logger.info(f"🚀 ЗАПУСК БОТА НА ПОРТУ: {PORT}")
    logger.info(f"🌐 WEBHOOK URL: {WEBHOOK_URL}")
    logger.info(f"📁 РАБОЧАЯ ДИРЕКТОРИЯ: {BASE_DIR}")
    logger.info("=" * 50)
    
    # Запускаем сервер
    web.run_app(
        app,
        host="0.0.0.0",  # Обязательно для Render!
        port=PORT,
        access_log=logger
    )

if __name__ == "__main__":
    main()

