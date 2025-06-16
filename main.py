
import os
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
import openai

# 初始化日志
logging.basicConfig(level=logging.INFO)

# 读取环境变量
openai.api_key = os.getenv("OPENAI_API_KEY")
GPT4_MODEL = os.getenv("GPT4_MODEL_NAME", "gpt-4o")
GPT35_MODEL = os.getenv("FALLBACK_MODEL_NAME", "gpt-3.5-turbo")
DAILY_LIMIT = int(os.getenv("GPT4_DAILY_LIMIT", "30"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "1859265885"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

# 加载 FAQ 数据
FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

# 用户使用记录
USAGE_FILE = "user_usage.json"
user_usage = {}
if os.path.exists(USAGE_FILE):
    with open(USAGE_FILE, "r", encoding="utf-8") as f:
        try:
            user_usage = json.load(f)
        except Exception:
            user_usage = {}

def save_usage():
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(user_usage, f)

def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def check_limit(user_id):
    today = get_today()
    uid = str(user_id)
    if uid not in user_usage:
        user_usage[uid] = {"date": today, "count": 0}
    elif user_usage[uid]["date"] != today:
        user_usage[uid] = {"date": today, "count": 0}

    if user_usage[uid]["count"] < DAILY_LIMIT:
        user_usage[uid]["count"] += 1
        save_usage()
        return GPT4_MODEL, None
    else:
        return GPT35_MODEL, f"你今天的 GPT-4o 使用次数已达上限（{DAILY_LIMIT}次），已为你切换为 GPT-3.5 模型。"

async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_authorized(chat_id):
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    model, tip = check_limit(user_id if user_id != ADMIN_USER_ID else "admin")

    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion["choices"][0]["message"]["content"]
        if tip:
            reply = f"{tip}

{reply}"
        await message.reply_text(reply)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

async def status_command(update: Update, context: CallbackContext):
    if update.effective_user.id == ADMIN_USER_ID:
        uid = str(ADMIN_USER_ID)
        usage = user_usage.get(uid, {})
        count = usage.get("count", 0)
        date = usage.get("date", get_today())
        await update.message.reply_text(f"今日 GPT-4o 使用次数：{count}/{DAILY_LIMIT}（日期：{date}）")
    else:
        await update.message.reply_text("无权限查看状态。")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("状态", status_command))
    app.run_polling()

if __name__ == "__main__":
    main()
