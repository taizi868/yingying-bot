import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# FAQ 示例数据库（关键词匹配）
FAQ_DB = {
    "返水": "返水比例为每日最高55%，自动发放至中心钱包。",
    "注册": "点击注册链接：https://s-ty.com 立即开户。",
    "代理": "我们支持代理返点+彩金扶持，详询客服。"
}

# 老板的 Telegram 用户 ID
BOSS_USER_ID = 119168660

# 群聊 ID 限制（允许多个群）
AUTHORIZED_CHATS = {
    -4566157499,
    -1002608816836
}

# 消息处理函数
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    # 群聊限制校验
    if chat_id not in AUTHORIZED_CHATS:
        return

    # FAQ 匹配优先
    for keyword, answer in FAQ_DB.items():
        if keyword in user_input:
            await update.message.reply_text(f"📌 {answer}")
            return

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": (
                    "你是一个专业的博彩行业客服助手，名叫盈盈。"
                    "如果提问者的 ID 是老板（119168660），请优先认真回答；"
                    "如果是其他群成员，也要礼貌专业地回答问题。"
                )},
                {"role": "user", "content": user_input}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"出错了：{e}")

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

# 启动应用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_health_server).start()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
