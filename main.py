
import os
import json
import logging
import asyncio
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)

# 初始化日志
logging.basicConfig(level=logging.INFO)

# 获取环境变量
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

# 加载 FAQ 数据
FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

# 判断群组是否被允许
def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

# 判断是否需要响应（必须被@或引用）
def should_respond(message):
    return message.reply_to_message or ("@YingYingHelperBot" in message.text)

# 消息处理函数
async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat_id
    text = message.text.strip()

    if not is_authorized(chat_id):
        return

    if not should_respond(message):
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": text}]
        )
        reply = response.choices[0].message.content
        await message.reply_text(reply)
    except Exception as e:
        logging.exception("OpenAI 错误:")
        await message.reply_text("出错了，请联系管理员。")

# 管理员指令：查看状态
async def handle_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        return
    await update.message.reply_text("盈盈 AI 当前运行正常。")

# 启动机器人
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("状态", handle_status))
    app.run_polling()

if __name__ == "__main__":
    main()
