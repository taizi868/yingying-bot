import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# OpenAI API 配置
openai.api_key = os.getenv("OPENAI_API_KEY")

# 消息处理函数
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": user_input}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"出错了：{e}")

# 启动 Telegram Bot 应用
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# 健康检查服务（用于骗过 Railway 的端口监听要求）
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_health_server).start()
    app.run_polling()
