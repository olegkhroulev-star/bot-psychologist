import os
import logging
import aiohttp
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ==================== НАСТРОЙКИ ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

WEBHOOK_HOST = os.getenv(
    "WEBHOOK_HOST",
    "https://bot-psychologist-1-utv7.onrender.com"
)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== ФАЙЛЫ ====================
GITHUB_BASE_URL = "https://raw.githubusercontent.com/olegkhroulev-star/bot-psychologist/main/files/"

FILES = {
    "anxiety": ("🧠 Тревожность", "anxiety.pdf"),
    "burnout": ("🔥 Выгорание", "burnout.pdf"),
    "growth": ("🌱 Личностный рост", "growth.pdf"),
    "relations": ("💬 Отношения", "relations.pdf"),
    "selfesteem": ("❤️ Самооценка", "selfesteem.pdf"),
    "sleep": ("😴 Сон", "sleep.pdf"),
}

# ==================== КЛАВИАТУРА ====================
def keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=f"file:{key}")]
            for key, (title, _) in FILES.items()
        ]
    )

# ==================== ОБРАБОТЧИКИ ====================
@dp.message(CommandStart())
async def start(message: types.Message):
    logger.info(f"/start from {message.from_user.id}")
    await message.answer(
        "👋 Привет!\n\nВыбери тему, чтобы получить материал:",
        reply_markup=keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith("file:"))
async def send_file(callback: types.CallbackQuery):
    key = callback.data.split(":")[1]

    if key not in FILES:
        await callback.answer("Файл не найден", show_alert=True)
        return

    title, filename = FILES[key]
    url = GITHUB_BASE_URL + filename

    await callback.answer(f"Отправляю {title}…")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Download error {resp.status}")
                data = await resp.read()

        document = BufferedInputFile(data, filename=filename)
        await callback.message.answer_document(
            document=document,
            caption=title
        )

        logger.info(f"Sent {filename}")

    except Exception as e:
        logger.error(f"File send error: {e}")
        await callback.answer("Ошибка при отправке", show_alert=True)

# ==================== WEBHOOK ====================
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set: {WEBHOOK_URL}")

# ==================== APP ====================
def main():
    app = web.Application()

    async def health(request):
        return web.Response(text="OK")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    dp.startup.register(on_startup)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    logger.info("Bot started")
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()


