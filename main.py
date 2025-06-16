
import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL_GPT4 = "gpt-4o"
OPENAI_MODEL_GPT35 = "gpt-3.5-turbo"
DEFAULT_DAILY_LIMIT = int(os.getenv("DAILY_GPT4_LIMIT", 30))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

user_usage = {}
admin_ids = {ADMIN_USER_ID}
user_preferences = {}

FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    with open("faq_data.json", "r", encoding="utf-8") as f:
        try:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
        except Exception:
            FAQ_DATA = {}

def is_authorized(chat_id):
    return str(chat_id) in ALLOWED_CHAT_IDS

def is_admin(user_id):
    return int(user_id) in admin_ids

async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = str(message.chat_id)
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_authorized(chat_id):
        return

    if text.startswith("/状态") and is_admin(user_id):
        count = user_usage.get(user_id, 0)
        await message.reply_text(f"你今天使用 GPT-4 的次数：{count}/{DEFAULT_DAILY_LIMIT}")
        return

    if text.startswith("/添加管理员") and is_admin(user_id):
        try:
            new_admin_id = int(text.split(" ")[1])
            admin_ids.add(new_admin_id)
            await message.reply_text("已添加管理员。")
        except:
            await message.reply_text("指令格式错误，应为 /添加管理员 用户ID")
        return

    if text.startswith("/移除管理员") and is_admin(user_id):
        try:
            rm_admin_id = int(text.split(" ")[1])
            if rm_admin_id in admin_ids:
                admin_ids.remove(rm_admin_id)
                await message.reply_text("已移除管理员。")
            else:
                await message.reply_text("该用户不是管理员。")
        except:
            await message.reply_text("指令格式错误，应为 /移除管理员 用户ID")
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    model = OPENAI_MODEL_GPT35
    if user_usage.get(user_id, 0) < DEFAULT_DAILY_LIMIT:
        model = OPENAI_MODEL_GPT4
        user_usage[user_id] = user_usage.get(user_id, 0) + 1
    else:
        await message.reply_text("您今日 GPT-4 使用已达上限，已切换为 GPT-3.5。")

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = completion.choices[0].message.content
        await message.reply_text(reply)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("状态", handle_message))
    app.add_handler(CommandHandler("添加管理员", handle_message))
    app.add_handler(CommandHandler("移除管理员", handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
