
import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
from openai import OpenAI
from collections import defaultdict

logging.basicConfig(level=logging.INFO)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL_DEFAULT = "gpt-3.5-turbo"
OPENAI_MODEL_ALT = "gpt-4o"
GPT4_DAILY_LIMIT = 30

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")
REPLY_ONLY_IF_MENTIONED = True
ALLOW_PRIVATE_ONLY_ADMIN = True

# memory
FAQ_DATA = {}
user_model_usage = defaultdict(lambda: {"gpt4_used": 0, "reset": datetime.utcnow().date()})
admin_ids = {str(ADMIN_USER_ID)}
user_prefs = {}

if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

def is_admin(user_id):
    return str(user_id) in admin_ids

def is_allowed(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    user_id = str(message.from_user.id)
    chat_id = str(message.chat_id)
    text = message.text.strip()

    # 限制私聊
    if update.effective_chat.type == "private" and not is_admin(user_id):
        return

    # 限制群聊 @
    if update.effective_chat.type != "private" and REPLY_ONLY_IF_MENTIONED:
        if context.bot.username.lower() not in text.lower():
            return

    if not is_allowed(chat_id):
        return

    # FAQ
    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    # 模型选择与限额逻辑
    today = datetime.utcnow().date()
    if user_model_usage[user_id]["reset"] != today:
        user_model_usage[user_id] = {"gpt4_used": 0, "reset": today}

    if user_model_usage[user_id]["gpt4_used"] < GPT4_DAILY_LIMIT:
        model = OPENAI_MODEL_ALT
        user_model_usage[user_id]["gpt4_used"] += 1
    else:
        model = OPENAI_MODEL_DEFAULT
        await message.reply_text("您今日 GPT-4 使用次数已达上限，已为您切换为 GPT-3.5 模型。")

    try:
        completion = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion.choices[0].message.content
        await message.reply_text(reply)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

async def status(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return
    uid = user_id
    today = datetime.utcnow().date()
    used = user_model_usage[uid]["gpt4_used"]
    await update.message.reply_text(f"今日 GPT-4 使用次数：{used} / {GPT4_DAILY_LIMIT}")

async def add_admin(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return
    if context.args:
        admin_ids.add(context.args[0])
        await update.message.reply_text(f"已添加管理员：{context.args[0]}")

async def remove_admin(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return
    if context.args:
        admin_ids.discard(context.args[0])
        await update.message.reply_text(f"已移除管理员：{context.args[0]}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("状态", status))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.run_polling()

if __name__ == "__main__":
    main()
