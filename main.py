
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private' and update.effective_user.id != ADMIN_USER_ID:
        return
    await update.message.reply_text("你好，我是盈盈，有什么可以帮您？")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if update.effective_chat.type == 'private' and update.effective_user.id != ADMIN_USER_ID:
        return
    if update.effective_chat.type in ['group', 'supergroup'] and chat_id not in ALLOWED_CHAT_IDS:
        return
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_API_MODEL,
            messages=[{"role": "user", "content": update.message.text}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text("出错了，请联系管理员。")

def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
