import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()


def read_env_value(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip().strip('"').strip("'")
    return None


TELEGRAM_BOT_TOKEN = read_env_value("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = read_env_value("OPENROUTER_API_KEY", "openrouter_api_key")
GROQ_API_KEY = read_env_value("GROQ_API_KEY", "groq_api_key")
GOOGLE_API_KEY = read_env_value("GOOGLE_API_KEY", "google_api_key")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
SUPPORTED_PROVIDERS = {
    "openrouter": "OpenRouter",
    "groq": "Groq",
    "google": "Google AI Studio",
}

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def get_user_provider(context: ContextTypes.DEFAULT_TYPE) -> str:
    provider = context.user_data.get("provider")
    if provider:
        return provider.lower()
    return os.getenv("DEFAULT_PROVIDER", "openrouter").lower()


def get_provider_api_key(provider: str, context: ContextTypes.DEFAULT_TYPE | None = None) -> str | None:
    if context:
        stored_key = context.user_data.get(f"{provider}_api_key")
        if stored_key:
            return stored_key

    key_map = {
        "openrouter": OPENROUTER_API_KEY,
        "groq": GROQ_API_KEY,
        "google": GOOGLE_API_KEY,
    }
    return key_map.get(provider)


def ask_openrouter(user_message: str, context: ContextTypes.DEFAULT_TYPE | None = None) -> str:
    api_key = get_provider_api_key("openrouter", context)
    if not api_key:
        return "API key OpenRouter belum tersedia. Silakan isi di .env atau kirim /setkey openrouter <api_key>."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Sanubot Telegram",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Kamu adalah @sanubot, asisten AI pintar yang ramah dan siap membantu menjawab segala pertanyaan dengan logis."},
            {"role": "user", "content": user_message},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        return "Maaf, saya tidak menerima respon valid dari AI."

    except Exception as e:
        logger.error(f"Error OpenRouter: {e}")
        return "Aduh, sepertinya otak AI saya sedang mengalami gangguan koneksi. Coba lagi nanti ya!"


def ask_groq(user_message: str, context: ContextTypes.DEFAULT_TYPE | None = None) -> str:
    api_key = get_provider_api_key("groq", context)
    if not api_key:
        return "API key Groq belum tersedia. Silakan isi di .env atau kirim /setkey groq <api_key>."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "Kamu adalah @sanubot, asisten AI ramah yang membantu dengan jawaban ringkas dan jelas."},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "Maaf, saya tidak menerima respon valid dari AI.")
        return "Maaf, saya tidak menerima respon valid dari AI."

    except Exception as e:
        logger.error(f"Error Groq: {e}")
        return "Aduh, saya gagal menghubungi Groq. Coba lagi nanti ya!"


def ask_google(user_message: str, context: ContextTypes.DEFAULT_TYPE | None = None) -> str:
    api_key = get_provider_api_key("google", context)
    if not api_key:
        return "API key Google AI Studio belum tersedia. Silakan isi di .env atau kirim /setkey google <api_key>."

    url = f"https://generativelanguage.googleapis.com/v1/models/{GOOGLE_MODEL}:generateMessage?key={api_key}"
    payload = {
        "messages": [
            {
                "author": "user",
                "content": [
                    {"type": "text", "text": user_message}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "candidates" in data and len(data["candidates"]) > 0:
            content = data["candidates"][0].get("content", [])
            if content and isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        return item.get("text", "Maaf, saya tidak menerima respon valid dari AI.")
        return "Maaf, saya tidak menerima respon valid dari AI."

    except Exception as e:
        logger.error(f"Error Google AI Studio: {e}")
        return "Aduh, saya gagal menghubungi Google AI Studio. Coba lagi nanti ya!"


def ask_ai(user_message: str, context: ContextTypes.DEFAULT_TYPE | None = None) -> str:
    provider = get_user_provider(context) if context else os.getenv("DEFAULT_PROVIDER", "openrouter")
    if provider == "groq":
        return ask_groq(user_message, context)
    if provider == "google":
        return ask_google(user_message, context)
    return ask_openrouter(user_message, context)


# --- DAFTAR COMMAND BOT ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"Halo {user_name}! 👋\n"
        f"Selamat datang di **@sanubot**.\n\n"
        f"Saya adalah bot AI yang bisa memakai provider OpenRouter, Groq, atau Google AI Studio.\n"
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
        "/ping - Memeriksa apakah bot sedang aktif\n"
        "/provider - Melihat provider aktif atau mengubahnya\n"
        "/setkey - Menyimpan API key untuk provider tertentu\n\n"
        "Contoh:\n"
        "/provider groq\n"
        "/provider google\n"
        "/setkey groq gsk_xxx\n"
        "/setkey google your_key\n\n"
        "💡 *Tips:* Kamu bisa langsung mengetik pesan atau pertanyaan apapun tanpa perintah, dan saya akan langsung menjawabnya!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "ℹ️ **Tentang @sanubot**\n\n"
        "• **Provider yang tersedia:** OpenRouter, Groq, Google AI Studio\n"
        "• **Platform:** Hosted on Render\n\n"
        "Bot ini dirancang untuk memberikan jawaban cerdas, analisis logis, dan membantu produktivitas harianmu."
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! Bot berjalan dengan lancar.")


async def provider_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        current_provider = get_user_provider(context)
        options = ", ".join(SUPPORTED_PROVIDERS.keys())
        await update.message.reply_text(
            f"Provider aktif saat ini: {current_provider}\nPilih salah satu: {options}\nContoh: /provider groq"
        )
        return

    provider = args[0].lower()
    if provider not in SUPPORTED_PROVIDERS:
        await update.message.reply_text(
            f"Provider tidak dikenal. Pilih salah satu: {', '.join(SUPPORTED_PROVIDERS.keys())}"
        )
        return

    context.user_data["provider"] = provider
    await update.message.reply_text(f"Provider diubah ke: {SUPPORTED_PROVIDERS[provider]}")


async def setkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Penggunaan: /setkey <provider> <api_key>\nContoh: /setkey groq gsk_xxx"
        )
        return

    provider = args[0].lower()
    if provider not in SUPPORTED_PROVIDERS:
        await update.message.reply_text(
            f"Provider tidak dikenal. Pilih salah satu: {', '.join(SUPPORTED_PROVIDERS.keys())}"
        )
        return

    api_key = " ".join(args[1:])
    context.user_data[f"{provider}_api_key"] = api_key
    context.user_data["provider"] = provider
    await update.message.reply_text(
        f"API key untuk {SUPPORTED_PROVIDERS[provider]} disimpan untuk akun ini."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ai_response = ask_ai(user_text, context)
    await update.message.reply_text(ai_response)


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("ERROR: Token Telegram belum diisi di .env!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("provider", provider_command))
    app.add_handler(CommandHandler("setkey", setkey_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot @sanubot sukses dijalankan!")
    app.run_polling()


if __name__ == "__main__":
    main()
