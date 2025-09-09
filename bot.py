# file: english_bot_webhook.py
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties

# --- Конфигурация ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # поставь свой Telegram ID в переменной окружения

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(bot)

# --- Клавиатуры ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("📘 ГДЗ"), KeyboardButton("📝 Домашнее задание")],
        [KeyboardButton("📚 Тема прошлого урока")],
        [KeyboardButton("⏰ Контрольная"), KeyboardButton("🌐 Полезные ссылки")],
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("➕ Добавить ГДЗ"), KeyboardButton("✏️ Изменить ДЗ")],
        [KeyboardButton("📚 Изменить тему"), KeyboardButton("⏰ Установить контрольную")],
        [KeyboardButton("🔙 В меню")],
    ],
    resize_keyboard=True
)

# --- Состояния и временное хранилище ---
admin_state = {}
temp_storage = {}

# --- Данные ---
DATA_FILE = "data.json"
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"gdz": None, "dz": "Пока нет", "tema": "Пока нет", "test_date": None}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# --- Удаление прошлых сообщений бота ---
last_bot_message = {}

async def send_and_delete_old(message: Message, text=None, photo=None, caption=None, keyboard=None):
    chat_id = message.chat.id
    if chat_id in last_bot_message:
        try:
            await bot.delete_message(chat_id, last_bot_message[chat_id])
        except:
            pass
    if photo:
        msg = await message.answer_photo(photo, caption=caption, reply_markup=keyboard)
    else:
        msg = await message.answer(text, reply_markup=keyboard)
    last_bot_message[chat_id] = msg.message_id

# --- Админ-проверка ---
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- Команды /start ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await send_and_delete_old(message, "Привет! Я бот 7А по английскому языку 🇬🇧", keyboard=main_kb)

@dp.message(F.text == "/admin")
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await send_and_delete_old(message, "У вас нет прав ❌")
    await send_and_delete_old(message, "Админ-меню:", keyboard=admin_kb)

# --- Учебные функции ---
@dp.message(F.text == "📘 ГДЗ")
async def show_gdz(message: Message):
    if data["gdz"]:
        await send_and_delete_old(message, photo=data["gdz"]["photo"], caption=data["gdz"].get("text",""))
    else:
        await send_and_delete_old(message, "ГДЗ пока нет 📭")

@dp.message(F.text == "📝 Домашнее задание")
async def show_dz(message: Message):
    await send_and_delete_old(message, f"📌 Домашнее задание:\n{data['dz']}")

@dp.message(F.text == "📚 Тема прошлого урока")
async def show_tema(message: Message):
    await send_and_delete_old(message, f"📚 Тема прошлого урока:\n{data['tema']}")

@dp.message(F.text == "⏰ Контрольная")
async def show_test(message: Message):
    if data["test_date"]:
        await send_and_delete_old(message, f"📢 Ближайшая контрольная: {data['test_date']}")
    else:
        await send_and_delete_old(message, "Контрольной пока нет ✅")

@dp.message(F.text == "🌐 Полезные ссылки")
async def show_links(message: Message):
    await send_and_delete_old(
        message,
        "🌐 Полезные ссылки:\n"
        "- <a href='https://dictionary.cambridge.org/'>Cambridge Dictionary</a>\n"
        "- <a href='https://quizlet.com/'>Quizlet</a>\n"
        "- <a href='https://www.bbc.co.uk/learningenglish'>BBC Learning English</a>\n"
    )

# --- Админ функции ---
@dp.message(F.text == "➕ Добавить ГДЗ")
async def admin_add_gdz(message: Message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = "add_gdz"
    await send_and_delete_old(message, "Пришлите фото ГДЗ 📸", keyboard=admin_kb)

@dp.message(F.text == "✏️ Изменить ДЗ")
async def admin_set_dz(message: Message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = "set_dz"
    await send_and_delete_old(message, "Введите новый текст домашнего задания 📝", keyboard=admin_kb)

@dp.message(F.text == "📚 Изменить тему")
async def admin_set_tema(message: Message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = "set_tema"
    await send_and_delete_old(message, "Введите тему прошлого урока 📚", keyboard=admin_kb)

@dp.message(F.text == "⏰ Установить контрольную")
async def admin_set_test(message: Message):
    if not is_admin(message.from_user.id):
        return
    admin_state[message.from_user.id] = "set_test"
    await send_and_delete_old(message, "Введите дату контрольной (например: 12.09.2025) ⏰", keyboard=admin_kb)

@dp.message(F.text == "🔙 В меню")
async def back_to_menu(message: Message):
    admin_state.pop(message.from_user.id, None)
    await send_and_delete_old(message, "Вы вернулись в меню:", keyboard=main_kb)

# --- Обработка фото ---
@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_admin(message.from_user.id):
        return
    action = admin_state.get(message.from_user.id)
    if action == "add_gdz":
        file_id = message.photo[-1].file_id
        temp_storage[message.from_user.id] = file_id
        admin_state[message.from_user.id] = "add_gdz_text"
        await send_and_delete_old(message, "Хотите добавить описание к ГДЗ? Напишите текст ✏️ (или 'нет')", keyboard=admin_kb)

# --- Обработка текста ---
@dp.message()
async def handle_text(message: Message):
    if not is_admin(message.from_user.id):
        return
    action = admin_state.get(message.from_user.id)
    if not action:
        return

    if action == "set_dz":
        data["dz"] = message.text
        save_data(data)
        admin_state.pop(message.from_user.id)
        await send_and_delete_old(message, "Домашнее задание обновлено ✅", keyboard=admin_kb)

    elif action == "set_tema":
        data["tema"] = message.text
        save_data(data)
        admin_state.pop(message.from_user.id)
        await send_and_delete_old(message, "Тема обновлена ✅", keyboard=admin_kb)

    elif action == "set_test":
        data["test_date"] = message.text
        save_data(data)
        admin_state.pop(message.from_user.id)
        await send_and_delete_old(message, f"Контрольная назначена на {message.text} ✅", keyboard=admin_kb)

    elif action == "add_gdz_text":
        file_id = temp_storage.pop(message.from_user.id)
        text = "" if message.text.lower() == "нет" else message.text
        data["gdz"] = {"photo": file_id, "text": text}  # старое стирается
        save_data(data)
        admin_state.pop(message.from_user.id)
        await send_and_delete_old(message, "ГДЗ добавлено ✅", keyboard=admin_kb)

# --- Webhook endpoint ---
async def handle(request):
    body = await request.json()
    update = bot.parse_update(body)
    await dp.process_update(update)
    return web.Response(text="OK")

app = web.Application()
app.router.add_post(f"/{TOKEN}", handle)

# --- Запуск (Render сам даёт HTTPS) ---
if __name__ == "__main__":
    import aiohttp
    import asyncio

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, port=port)
