
import logging
import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

openai.api_key = os.getenv("OPENAI_API_KEY")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    response = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo"),
        messages=[{"role": "user", "content": query}]
    )
    await update.message.reply_text(response.choices[0].message.content)

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run_polling()
