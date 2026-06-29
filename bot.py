import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fungsi untuk memanggil API OpenRouter
def ask_openrouter(user_message: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Sanubot Telegram"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Kamu adalah @sanubot, asisten AI pintar yang ramah dan siap membantu menjawab segala pertanyaan dengan logis."},
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            return "Maaf, saya tidak menerima respon valid dari AI."
            
    except Exception as e:
        logger.error(f"Error OpenRouter: {e}")
        return "Aduh, sepertinya otak AI saya sedang mengalami gangguan koneksi. Coba lagi nanti ya!"

# --- DAFTAR COMMAND BOT ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"Halo {user_name}! 👋\n"
        f"Selamat datang di **@sanubot**.\n\n"
        f"Saya adalah bot AI yang ditenagai oleh NVIDIA Nemotron Nano (Reasoning Model).\n"
        f"Kamu bisa mengobrol langsung dengan saya atau menggunakan perintah yang tersedia.\n\n"
        f"Ketik /help untuk melihat daftar perintah lengkap!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Daftar Perintah @sanubot**:\n\n"
        "/start - Memulai ulang bot dan menyapa kamu\n"
        "/help - Menampilkan daftar perintah ini\n"
        "/about - Informasi mengenai bot dan model AI yang digunakan\n"
        "/ping - Memeriksa apakah bot sedang aktif\n\n"
        "💡 *Tips:* Kamu bisa langsung mengetik pesan atau pertanyaan apapun tanpa perintah, dan saya akan langsung menjawabnya!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "ℹ️ **Tentang @sanubot**\n\n"
        "• **Model AI:** NVIDIA Nemotron 3 Nano Omni 30B (Reasoning)\n"
        "• **Provider:** OpenRouter AI\n"
        "• **Platform:** Hosted on Render\n\n"
        "Bot ini dirancang untuk memberikan jawaban cerdas, analisis logis, dan membantu produktivitas harianmu."
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Bot berjalan dengan lancar.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ai_response = ask_openrouter(user_text)
    await update.message.reply_text(ai_response)

def main():
    if not TELEGRAM_BOT_TOKEN or not OPENROUTER_API_KEY:
        logger.error("ERROR: Token Telegram atau API Key OpenRouter belum diisi di .env!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot @sanubot sukses dijalankan!")
    app.run_polling()

if __name__ == '__main__':
    main()
