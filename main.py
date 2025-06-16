import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from collections import defaultdict
from datetime import datetime, timedelta

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 设置
BOSS_USER_ID = 119168660
AUTHORIZED_CHATS = {-4566157499, -1002608816836}
INVITE_KEYWORDS = {"代理", "加盟", "合作"}
INVITE_MESSAGE = "欢迎加入盛盈体育代理计划，点击这里注册 👉 https://s-ty.com"
FAQ_DB = {
    "返水": "返水比例为每日最高55%，自动发放至中心钱包。",
    "注册": "点击注册链接：https://s-ty.com 立即开户。",
    "代理": "我们支持代理返点+彩金扶持，详询客服。"
}
VIP_USERS = {119168660}  # 可动态管理

# 数据缓存结构
user_activity = defaultdict(list)  # {user_id: [(time, text)]}
keyword_counter = defaultdict(int)

# 指令：/状态（仅老板可用）
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOSS_USER_ID:
        return
    active_users = len(user_activity)
    top_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    top_kw_text = "\n".join([f"{k}: {v}" for k, v in top_keywords]) or "无"
    await update.message.reply_text(f"📊 盈盈统计：\n- 活跃用户数：{active_users}\n- 关键词排名：\n{top_kw_text}")

# 指令：/设为VIP [user_id]
async def setvip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOSS_USER_ID:
        return
    try:
        uid = int(context.args[0])
        VIP_USERS.add(uid)
        await update.message.reply_text(f"✅ 已将 {uid} 添加为 VIP。")
    except:
        await update.message.reply_text("❌ 命令格式错误，应为：/设为VIP 用户ID")

# 消息主逻辑
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = message.text.strip()

    # 限定群组
    if chat_id not in AUTHORIZED_CHATS:
        return

    # 必须被@或引用
    if not (
        (message.entities and any(e.type == "mention" and "@YingYingHelperBot" in message.text for e in message.entities))
        or message.reply_to_message and message.reply_to_message.from_user.username == "YingYingHelperBot"
    ):
        return

    # 活跃记录
    user_activity[user_id].append((datetime.utcnow(), text))

    # 关键词统计
    for word in FAQ_DB.keys() | INVITE_KEYWORDS:
        if word in text:
            keyword_counter[word] += 1

    # 关键词触发私聊邀请
    if any(word in text for word in INVITE_KEYWORDS):
        try:
            await context.bot.send_message(chat_id=user_id, text=INVITE_MESSAGE)
        except:
            pass

    # FAQ 优先
    for word, answer in FAQ_DB.items():
        if word in text:
            await message.reply_text(f"📌 {answer}")
            return

    # AI 回复
    try:
        role = "你是盛盈体育的智能客服盈盈，请专业回答博彩用户的问题。"
        if user_id == BOSS_USER_ID:
            role += "你面对的是老板，请优先认真回复。"
        elif user_id in VIP_USERS:
            role += "你面对的是 VIP 代理，请使用尊敬语气。"
        else:
            role += "你面对的是普通用户，请礼貌专业。"

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": text}
            ]
        )
        await message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await message.reply_text(f"出错了：{e}")

# 健康检查服务
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# 启动
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_health_server).start()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("状态", status_command))
    app.add_handler(CommandHandler("设为VIP", setvip_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
