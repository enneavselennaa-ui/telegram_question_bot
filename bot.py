import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openpyxl import Workbook
from datetime import datetime
import os
import shutil
from aiogram.exceptions import TelegramMigrateToChat

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8573719664:AAF1FYleLXiKWxxz9MsP--cn5zGQ92ySefg"  # токен от BotFather
ADMIN_CHAT_ID = -1003752500482     # ID твоего канала
DB_NAME = "questions.db"
BACKUP_FOLDER = "backups"
# ===============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- КНОПКА "Задать вопрос" ----------
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📝 Задать вопрос")]],
    resize_keyboard=True
)

# ---------- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ----------
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                user_id INTEGER,
                username TEXT,
                question TEXT
            )
        """)
        await db.commit()

# ---------- БЭКАП БАЗЫ ДАННЫХ ----------
def backup_db():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    backup_name = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
    shutil.copy(DB_NAME, os.path.join(BACKUP_FOLDER, backup_name))

# ---------- КОМАНДА /start ----------
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте!\n\nНажмите кнопку ниже, чтобы задать вопрос 👇",
        reply_markup=keyboard
    )

# ---------- КНОПКА "Задать вопрос" ----------
@dp.message(lambda m: m.text == "📝 Задать вопрос")
async def ask_question(message: types.Message):
    await message.answer(
        "Отлично. Ты в безопасном анонимном чате.\n\n"
        "Напиши свой вопрос прямо в этот диалог.\n"
        "Опиши ситуацию так, как чувствуешь. Можно коротко или подробно — как тебе комфортнее.",
        reply_markup=keyboard
    )

# ---------- ПРИЁМ ВОПРОСА ----------
@dp.message()
async def handle_question(message: types.Message):
    global ADMIN_CHAT_ID  # должно быть в начале функции

    if message.text.startswith("/") or message.text == "📝 Задать вопрос":
        return

    # сохраняем в БД
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO questions (date, user_id, username, question) VALUES (?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                message.from_user.id,
                message.from_user.username,
                message.text
            )
        )
        await db.commit()

    # отвечаем пользователю
    await message.answer(
        "Спасибо за вопрос! ❤️ Твоё сообщение получено.\n\n"
        "Если хочешь задать ещё один вопрос — просто нажми кнопку «Задать вопрос».",
        reply_markup=keyboard
    )

    # пересылаем в канал только текст вопроса
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"❓ Новый вопрос\n\n{message.text}"
        )
    except TelegramMigrateToChat as e:
        ADMIN_CHAT_ID = e.new_chat_id
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"❓ Новый вопрос\n\n{message.text}"
        )

# ---------- КОМАНДА /export (только админ) ----------
@dp.message(lambda m: m.text == "/export")
async def export_excel(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Questions"
    ws.append(["Дата", "User ID", "Username", "Вопрос"])

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT date, user_id, username, question FROM questions") as cursor:
            async for row in cursor:
                ws.append(row)

    file_name = "questions.xlsx"
    wb.save(file_name)
    await message.answer_document(types.FSInputFile(file_name))

# ---------- ЗАПУСК БОТА ----------
async def main():
    await init_db()
    backup_db()
    # старт polling с игнорированием старых апдейтов
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
