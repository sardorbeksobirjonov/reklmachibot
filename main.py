import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from datetime import datetime

# 🔐 Sozlamalar
BOT_TOKEN = "7549174203:AAHzj6g0iOWUxcNKuUbC1CITujvtAJrAJpw"
CHANNEL_ID = "@reklama_konol"
ADMIN_ID = 7752032178
ADMIN_USERNAME = "@sardorbeksobirjonov"
ADMIN_PASSWORD = "adminparol123"

# 🔑 Parollar ketma-ketligi
PASSWORD_SEQUENCE = ["BFE412", "ABC784", "HFST789", "QWED14"]
user_password_index = {}
user_logs = []
reklama_id = 1

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# 🧠 Holatlar
class ReklamaState(StatesGroup):
    wait_for_password = State()
    wait_for_text = State()

class AdminState(StatesGroup):
    wait_for_admin_password = State()

# ▶️ /start
@dp.message(F.text == "/start")
async def start(msg: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Reklama joylash")],
            [KeyboardButton(text="🔐 Admin tugmasi")]
        ],
        resize_keyboard=True
    )
    await msg.answer(
        "✅ <b>Reklama joylash xizmatiga xush kelibsiz!</b>\n\n"
        "📢 <b>Reklama yuborish tartibi:</b>\n"
        "1. Parolni admin orqali oling.\n"
        "2. \"🟢 Reklama joylash\" tugmasini bosing.\n"
        "3. Parolni kiriting.\n"
        "4. Reklama matni, rasm, video, audio yoki faylni yuboring.\n\n"
        "🔐 <b>Maxsus parollar</b> faqat <b>1 martalik</b> bo‘ladi.\n"
        "💵 Parol narxi: <b>5 000 so‘m</b>\n"
        f"👤 Admin: <a href='https://t.me/{ADMIN_USERNAME[1:]}'>{ADMIN_USERNAME}</a>",
        reply_markup=kb,
        disable_web_page_preview=True
    )

# 🔐 Reklama joylash bosqichi
@dp.message(F.text == "🟢 Reklama joylash")
async def ask_password(msg: Message, state: FSMContext):
    await msg.answer("🔐 Iltimos, maxsus parolni kiriting:")
    await state.set_state(ReklamaState.wait_for_password)

# ✅ Parolni tekshirish
@dp.message(ReklamaState.wait_for_password)
async def check_password(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    password = msg.text.strip()

    current_index = user_password_index.get(user_id, 0)
    if current_index >= len(PASSWORD_SEQUENCE):
        await msg.answer("✅ Siz barcha parollardan foydalandingiz. Yangi parollar uchun admin bilan bog‘laning.")
        await state.clear()
        return

    expected_password = PASSWORD_SEQUENCE[current_index]
    if password == expected_password:
        user_password_index[user_id] = current_index + 1
        await msg.answer("✅ Parol to‘g‘ri! Endi reklamani (matn, rasm, video va h.k.) yuboring:")
        await state.set_state(ReklamaState.wait_for_text)
    else:
        await msg.answer("❌ Bukodni ishlatgansz boshqa kod oling admindan.")

# 📤 Reklama qabul qilish va tasdiqlash
@dp.message(ReklamaState.wait_for_text)
async def confirm_reklama(msg: Message, state: FSMContext):
    await state.update_data(reklama_msg=msg)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_reklama")]
    ])

    await msg.answer("📤 Reklamani tasdiqlash uchun pastdagi tugmani bosing:", reply_markup=keyboard)

# ☑️ Tasdiqlash bosilganda kanalga yuborish
@dp.callback_query(F.data == "confirm_reklama")
async def send_to_channel(callback: CallbackQuery, state: FSMContext):
    global reklama_id
    user = callback.from_user
    data = await state.get_data()
    msg = data.get("reklama_msg")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        caption = f"<b>🆔 ID: {reklama_id}</b>\n\n"

        if msg.text:
            await bot.send_message(CHANNEL_ID, caption + msg.text)
        elif msg.photo:
            await bot.send_photo(CHANNEL_ID, msg.photo[-1].file_id, caption=caption + (msg.caption or ""))
        elif msg.video:
            await bot.send_video(CHANNEL_ID, msg.video.file_id, caption=caption + (msg.caption or ""))
        elif msg.audio:
            await bot.send_audio(CHANNEL_ID, msg.audio.file_id, caption=caption + (msg.caption or ""))
        elif msg.voice:
            await bot.send_voice(CHANNEL_ID, msg.voice.file_id, caption=caption + (msg.caption or ""))
        elif msg.document:
            await bot.send_document(CHANNEL_ID, msg.document.file_id, caption=caption + (msg.caption or ""))
        else:
            await callback.message.answer("❌ Bu turdagi faylni yuborib bo‘lmaydi.")
            await state.clear()
            return

        await bot.send_message(
            ADMIN_ID,
            f"👤 <b>{user.full_name}</b>\n🆔 ID: {user.id}\n🕒 {now}\n🆔 Reklama ID: {reklama_id}"
        )

        user_logs.append({
            "name": user.full_name,
            "id": user.id,
            "text": msg.text or msg.caption or "Multimedia reklama",
            "time": now,
            "reklama_id": reklama_id
        })

        reklama_id += 1
        await callback.message.answer(
            f"✅ <b>Reklamangiz muvaffaqiyatli yuborildi!</b>\n\n📢 Kanal: {CHANNEL_ID}\n🆔 Reklama ID: <b>{reklama_id - 1}</b>"
        )

    except Exception as e:
        await callback.message.answer("❌ Xatolik yuz berdi. Admin bilan bog‘laning.")
        print(f"[XATO] {e}")

    await state.clear()
    await callback.answer()

# 👑 Admin tugmasi
@dp.message(F.text == "🔐 Admin tugmasi")
async def admin_password(msg: Message, state: FSMContext):
    await msg.answer("🛡 Admin parolini kiriting:")
    await state.set_state(AdminState.wait_for_admin_password)

@dp.message(AdminState.wait_for_admin_password)
async def admin_check(msg: Message, state: FSMContext):
    if msg.text == ADMIN_PASSWORD:
        if user_logs:
            text = "📋 <b>Reklama yuborganlar:</b>\n\n"
            for i, u in enumerate(user_logs, 1):
                text += f"{i}. 👤 <b>{u['name']}</b>\n🆔 {u['id']}\n🕒 {u['time']}\n🆔 ID: {u['reklama_id']}\n\n"
            await msg.answer(text)
        else:
            await msg.answer("⛔ Hozircha hech kim reklama yubormagan.")
    else:
        await msg.answer("❌ Noto‘g‘ri admin parol!")
    await state.clear()

# ▶️ Botni ishga tushurish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
