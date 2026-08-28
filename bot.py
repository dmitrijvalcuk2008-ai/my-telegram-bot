import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from yt_dlp import YoutubeDL

# Ваш токен:
BOT_TOKEN = "8861724210:AAGrIsmkoPrim-FgQpBNBmHPj8FsbZ3oqy4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ХИТРЫЙ ТРЮК ДЛЯ RENDER: Создаем микро-веб-сайт в фоне
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    def log_message(self, format, *args):
        return  # Отключаем спам в логи

def run_health_check():
    port = int(os.environ.get("PORT", 10000))  # Render сам дает порт
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Надішли мені посилання на відео з TikTok або YouTube Shorts, і я його завантажу!")

@dp.message(F.text.startswith("http"))
async def download_video(message: types.Message):
    url = message.text
    status_msg = await message.answer("🔄 Завантажую відео, зачекайте...")
    
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'bestvideo[filesize<45M]+bestaudio/best[filesize<45M]/worst', 
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
    }
    
    try:
        os.makedirs("downloads", exist_ok=True)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in ['.mp4', '.mkv', '.webm', '.3gp']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break

        await status_msg.edit_text("📤 Надсилаю відео у чат...")
        video_file = types.FSInputFile(filename)
        await message.answer_video(video=video_file, caption="Ось ваше відео! 🎉")
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Помилка скачування.\nЛог: {str(e)}")

async def main():
    # Запускаем наш фоновый веб-сайт перед включением бота
    threading.Thread(target=run_health_check, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
