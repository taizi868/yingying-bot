# 盈盈 AI 客服机器人（V2）

基于 Telegram Bot 和 OpenAI API 的智能客服系统，适用于博彩、推广等垂直领域，支持自定义 FAQ、关键词邀请、权限控制等功能。

## 🚀 快速部署

### 1. 准备环境变量（.env）

请根据 `.env.example` 配置你的 `.env` 文件，并上传到部署平台或本地运行目录。

### 2. 安装依赖（可选）

```bash
pip install -r requirements.txt
```

### 3. 启动机器人（本地或部署平台）

```bash
python main.py
```

## 🧠 功能模块说明

- 📌 群组权限限制
- 🤖 FAQ 智能回答
- 🧠 用户偏好记忆
- 📥 关键词触发私聊邀请
- 🔧 指令系统（/状态, /清空, /日报）
- 🎙️ 支持语音转文字（预留）
- 📊 数据统计、关键词分析
- 📣 @盈盈 或被引用时才触发回复（防止打扰）

## 📦 文件结构

```
yingying-bot/
├── main.py
├── modules/
│   ├── config.py
│   ├── faq.py
│   ├── triggers.py
│   ├── speech.py
│   └── commands.py
├── .env.example
├── README.md
└── requirements.txt
```

## 🤝 合作 & 定制

如需集成更多指令、群控联动、实时看板等功能，请联系开发者或继续拓展模块。
