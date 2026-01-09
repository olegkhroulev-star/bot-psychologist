import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

FILES = [
    "files/anxiety.pdf",
    "files/stress.pdf",
    "files/burnout.pdf",
    "files/sleep.pdf",
    "files/relations.pdf",
    "files/selfesteem.pdf",
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Начинаю отправку файлов 📂")

    for path in FILES:
        if not os.path.exists(path):
            logging.error(f"❌ Файл не найден: {path}")
            await message.answer(f"Файл не найден: {path}")
            continue

        try:
            logging.info(f"📤 Отправляю файл: {path}")
            await message.answer_document(FSInputFile(path))
            await asyncio.sleep(1)  # важно!
        except Exception as e:
            logging.exception(f"🔥 Ошибка при отправке {path}: {e}")
            await message.answer(f"Ошибка при отправке {path}")

    await message.answer("Готово ✅")


async def main():
    logging.info("🤖 Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



