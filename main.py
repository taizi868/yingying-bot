
import os
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import openai

logging.basicConfig(level=logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_CHAT_IDS = [int(cid) for cid in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if cid]

user_gpt4_usage = {}
MAX_GPT4_PER_USER_PER_DAY = 30

ADMIN_IDS = {ADMIN_USER_ID}

FAQ_DATA = {}
if os.path.exists("faq_data.json"):
    try:
        with open("faq_data.json", "r", encoding="utf-8") as f:
            FAQ_DATA = {item["q"]: item["a"] for item in json.load(f)}
    except Exception:
        FAQ_DATA = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_authorized(chat_id):
    return chat_id in ALLOWED_CHAT_IDS

def get_user_model(user_id):
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    user_key = f"{user_id}:{today}"
    count = user_gpt4_usage.get(user_key, 0)
    if count < MAX_GPT4_PER_USER_PER_DAY:
        user_gpt4_usage[user_key] = count + 1
        return "gpt-4"
    return "gpt-3.5-turbo"

async def handle_message(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = message.chat_id
    user_id = message.from_user.id
    text = message.text.strip()
    is_group = message.chat.type in ["group", "supergroup"]
    bot_mentioned = context.bot.username in text if is_group else False

    if is_group and not bot_mentioned:
        return
    if not is_authorized(chat_id):
        return

    if text in FAQ_DATA:
        await message.reply_text(FAQ_DATA[text])
        return

    model = get_user_model(user_id)
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        reply = response["choices"][0]["message"]["content"]
        await message.reply_text(reply + ("" if model == "gpt-4" else "

（已切换为GPT-3.5，因今日GPT-4额度已达上限）"))
    except Exception as e:
        logging.exception(e)
        await message.reply_text("出错了，请联系管理员。")

async def status_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("无权限")
        return
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage_today = {k: v for k, v in user_gpt4_usage.items() if k.endswith(today)}
    await update.message.reply_text(f"今日GPT-4调用统计：{json.dumps(usage_today, indent=2)}")

async def add_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("无权限")
        return
    if context.args:
        try:
            new_admin_id = int(context.args[0])
            ADMIN_IDS.add(new_admin_id)
            await update.message.reply_text(f"已添加管理员：{new_admin_id}")
        except:
            await update.message.reply_text("格式错误，请输入正确的数字ID")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("状态", status_command))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
