import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== HTTP СЕРВЕР (ДЛЯ RENDER) =====
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"🌐 Web server started on port {port}")

# ===== TELEGRAM BOT =====
async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer("🤖 Бот работает!")

    logger.info("🤖 Bot polling started")
    await dp.start_polling(bot)

# ===== MAIN =====
async def main():
    await asyncio.gather(
        start_web_server(),  # порт для Render
        start_bot(),         # polling
    )

if __name__ == "__main__":
    asyncio.run(main())


