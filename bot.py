import asyncio
import json
import os
import time
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

# ================= НАСТРОЙКИ =================

TOKEN = "8510415452:AAHJpmdHY16SjtKhpXJgQtNY8_LKzzTNglY"

FILES_DIR = "files"
FILE_IDS_PATH = "file_ids.json"
SPAM_TIMEOUT = 10  # секунд между нажатиями кнопок

# ================= ЛОГИ =================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= ХРАНИЛИЩА =================

user_last_click = {}  # анти-спам

if os.path.exists(FILE_IDS_PATH):
    with open(FILE_IDS_PATH, "r", encoding="utf-8") as f:
        file_ids = json.load(f)
else:
    file_ids = {}

def save_file_ids():
    with open(FILE_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(file_ids, f, ensure_ascii=False, indent=2)

# ================= МАТЕРИАЛЫ =================

materials = {
    "🧠 Тревожность": {
        "file": "anxiety.pdf",
        "text": "🧠 *Работа с тревожностью*\n\nМатериал поможет снизить тревогу.",
    },
    "❤️ Самооценка": {
        "file": "selfesteem.pdf",
        "text": "❤️ *Самооценка*\n\nУпражнения для уверенности.",
    },
    "😴 Сон": {
        "file": "sleep.pdf",
        "text": "😴 *Сон*\n\nТехники для засыпания.",
    },
    "🔥 Выгорание": {
        "file": "burnout.pdf",
        "text": "🔥 *Выгорание*\n\nВосстановление энергии.",
    },
    "💬 Отношения": {
        "file": "relations.pdf",
        "text": "💬 *Отношения*\n\nНавыки общения.",
    },
    "🌱 Личностный рост": {
        "file": "growth.pdf",
        "text": "🌱 *Личностный рост*\n\nСаморазвитие.",
    },
}

# ================= ОСНОВНАЯ ЛОГИКА =================

async def main():
    bot = Bot(token=TOKEN, request_timeout=120)
    dp = Dispatcher()

    keyboard = [
        [types.KeyboardButton(text=key)] for key in materials.keys()
    ]

    menu = types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer(
            "👋 Выберите тему 👇",
            reply_markup=menu
        )

    @dp.message(lambda m: m.text in materials)
    async def send_material(message: types.Message):
        user_id = message.from_user.id
        now = time.time()

        # -------- АНТИ-СПАМ --------
        last = user_last_click.get(user_id, 0)
        if now - last < SPAM_TIMEOUT:
            await message.answer("⏳ Пожалуйста, подождите немного…")
            return

        user_last_click[user_id] = now

        topic = message.text
        material = materials[topic]
        filename = material["file"]
        file_path = os.path.join(FILES_DIR, filename)

        await message.answer(material["text"], parse_mode="Markdown")

        # -------- ЕСЛИ file_id УЖЕ ЕСТЬ --------
        if filename in file_ids:
            await message.answer_document(file_ids[filename])
            return

        # -------- ПЕРВАЯ ЗАГРУЗКА --------
        if not os.path.exists(file_path):
            await message.answer("❌ Файл не найден")
            return

        await message.answer("📤 Загружаю файл, это может занять немного времени…")

        document = FSInputFile(file_path)

        msg = await message.answer_document(document)

        # сохраняем file_id
        file_ids[filename] = msg.document.file_id
        save_file_ids()

        await message.answer("✅ Готово! В следующий раз файл придёт мгновенно.")

    logger.info("🤖 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
