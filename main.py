import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json

BOT_OWNER_ID = 1859265885
GROUP_WHITELIST = [-1002259994346, -1002361784153]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id < 0 and update.message.chat_id not in GROUP_WHITELIST:
        return
    await update.message.reply_text("你好，我是盈盈AI客服，有问题@我试试看～")

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    for entry in faq_data:
        if entry['q'] in msg:
            await update.message.reply_text(entry['a'])
            return
    if update.message.from_user.id == BOT_OWNER_ID:
        await update.message.reply_text("老板我没听懂～")
    return

with open("faq_data.json", "r", encoding="utf-8") as f:
    faq_data = json.load(f)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, faq_handler))
    app.run_polling()
