import os
import logging
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS or str(chat_id) == str(ADMIN_USER_ID)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip()

    if not is_authorized(chat_id):
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    try:
        completion = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion.choices[0].message.content
        await message.reply_text(reply)
    except Exception as e:
        logging.exception("OpenAI 错误:")
        await message.reply_text("出错了，请联系管理员。")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
