import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL

# Твій токен уже вставлений:
BOT_TOKEN = "8861724210:AAGrIsmkoPrim-FgQpBNBmHPj8FsbZ3oqy4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словник із перекладами для бота
TEXTS = {
    "uk": {
        "welcome": "Привіт! Будь ласка, обери мову спілкування / Please choose your language:",
        "set_lang": "Чудово! Тепер надсилай мені посилання на відео з **TikTok, Instagram, Facebook або YouTube**, і я його завантажу!",
        "loading": "🔄 Завантажую та обробляю відео, зачекайте...",
        "sending": "📤 Надсилаю чисте відео у чат...",
        "done": "Ось ваше відео! 🎉",
        "error": "❌ Помилка скачування. Перевірте посилання або спробуйте інше відео."
    },
    "en": {
        "welcome": "Hello! Please choose your language / Будь ласка, обери мову спілкування:",
        "set_lang": "Great! Now send me a link to a video from **TikTok, Instagram, Facebook, or YouTube**, and I will download it!",
        "loading": "🔄 Downloading and processing video, please wait...",
        "sending": "📤 Sending clean video to the chat...",
        "done": "Here is your video! 🎉",
        "error": "❌ Download error. Check the link or try another video."
    },
    "es": {
        "welcome": "¡Hola! Por favor, elige tu idioma / Будь ласка, обери мову спілкування:",
        "set_lang": "¡Genial! Ahora envíame un enlace de video de **TikTok, Instagram, Facebook o YouTube**, ¡и lo descargaré!",
        "loading": "🔄 Descargando y procesando el video, por favor espera...",
        "sending": "📤 Enviando video limpio al chat...",
        "done": "¡Aquí está tu video! 🎉",
        "error": "❌ Error de descarga. Verifica el enlace o prueba con otro video."
    }
}

# Тимчасова пам'ять для збереження вибору мови (поки бот запущений)
user_languages = {}

# Функція створення кнопок вибору мови
def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Українська", callback_data="lang_uk")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.button(text="🇪🇸 Español", callback_data="lang_es")
    builder.adjust(1) # Кнопки будуть одна під одною
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # При старті завжди пропонуємо вибрати мову
    await message.answer(TEXTS["uk"]["welcome"], reply_markup=get_language_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def callbacks_num(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang # Запам'ятовуємо мову користувача
    
    # Прибираємо кнопки і пишемо підтвердження обраною мовою
    await callback.message.edit_text(TEXTS[lang]["set_lang"])
    await callback.answer()

@dp.message(F.text.startswith("http"))
async def download_video(message: types.Message):
    url = message.text
    # Перевіряємо, яку мову обрав користувач (якщо не обрав — ставимо українську за замовчуванням)
    lang = user_languages.get(message.from_user.id, "uk")
    
    status_msg = await message.answer(TEXTS[lang]["loading"])
    
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'bestvideo[ext=mp4][filesize<45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<45M]/best[filesize<45M]/worst',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'extractor_args': {
            'youtube': {'player_client': ['android']},
            'tiktok': {'no_watermark': True}
        },
    }
    
    try:
        os.makedirs("downloads", exist_ok=True)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in ['.mp4', '.mkv', '.webm', '.3gp', '.mov']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break

        await status_msg.edit_text(TEXTS[lang]["sending"])
        video_file = types.FSInputFile(filename)
        await message.answer_video(video=video_file, caption=TEXTS[lang]["done"])
        
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"{TEXTS[lang]['error']}\n\nLog: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
