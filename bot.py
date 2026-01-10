import os
import asyncio
import logging

from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
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

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ------------------ FILES ------------------

FILES = {
    "anxiety": ("Тревожность", "files/anxiety.pdf"),
    "burnout": ("Выгорание", "files/burnout.pdf"),
    "growth": ("Личностный рост", "files/growth.pdf"),
    "relations": ("Отношения", "files/relations.pdf"),
    "selfesteem": ("Самооценка", "files/selfesteem.pdf"),
    "sleep": ("Сон", "files/sleep.pdf"),
}

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

    if key not in FILES:
        await callback.answer("Файл не найден", show_alert=True)
        return

    title, path = FILES[key]

    try:
        document = FSInputFile(path)
        await callback.message.answer_document(
            document=document,
            caption=f"📄 {title}"
        )
        await callback.answer()
    except FileNotFoundError:
        await callback.answer("Файл отсутствует на сервере", show_alert=True)

# ------------------ WEBHOOK APP ------------------

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook set: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    app = web.Application()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, port=PORT)

if __name__ == "__main__":
    main()


