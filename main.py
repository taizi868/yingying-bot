
import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
import openai

logging.basicConfig(level=logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    if not message:
        return

    if not (message.text and (message.entities or message.reply_to_message)):
        return  # 忽略未@或未引用的消息

    if not is_authorized(str(message.chat_id)):
        return

    try:
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": message.text}]
        )
        reply = completion["choices"][0]["message"]["content"]
        await message.reply_text(reply)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
