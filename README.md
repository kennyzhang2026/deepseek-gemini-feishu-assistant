<MARKDOWN>
# 🤖 AI Assistant (Gemini 2.0 Flash) with Feishu
> **v2.0 Stable**: 专注稳定性的多模态智能助手，集成飞书知识库自动存档。
## 📖 项目简介
这是一个基于 Streamlit 构建的生产力级 AI 助手。
经历了 v1.0 MVP 的探索，**v2.0 版本** 确立了“稳定性优先”的原则。我们移除了复杂的模型路由和不稳定的 DeepSeek 接口，全面采用 **Google Gemini 2.0 Flash**，实现了毫秒级的图文响应速度。同时，重构了飞书集成模块，支持将对话历史批量同步至个人知识库。
## ✨ 核心功能 (v2.0)
### ⚡️ 极速多模态体验
- **Gemini 2.0 Flash 驱动**：单一模型解决所有问题，无论是纯文本对话还是复杂的图片分析，均能秒级响应。
- **视觉稳定性增强**：内置图片自动压缩算法（Max 800px），彻底解决了上传大图导致连接中断（Server disconnected）的问题。
- **沉浸式 UI**：移除了侧边栏繁杂的 Key 输入框，界面更加干净专注于内容。
### 📚 飞书知识库闭环
- **存最近一轮**：一键保存当前最有价值的一组问答（User + AI）。
- **存全部历史 (New)**：
    - **智能遍历**：算法自动识别 Session State 中的所有历史消息。
    - **成对匹配**：自动将 User 和 Assistant 的消息组合成问答对。
    - **可视化进度**：提供实时进度条反馈，批量写入过程一目了然。
### 🛡 安全与配置
- **Secrets 管理**：放弃前端输入 Key 的方式，改用后台 `secrets.toml` 统一管理，避免密钥泄露风险。
- **隐私保护**：对话数据仅在内存中流转或存入你私人的飞书表格，不保存本地日志。
## 🚀 快速开始
### 1. 安装依赖
```bash
pip install -r requirements.txt
2. 配置密钥 (必须)
在项目根目录创建 .streamlit/secrets.toml 文件（注意：v2.0 不再支持前端输入 Key）：

<TOML>
# .streamlit/secrets.toml
# AI 模型配置
GEMINI_API_KEY = "你的_Gemini_API_Key"
# 飞书多维表格配置
FEISHU_APP_ID = "你的_App_ID"
FEISHU_APP_SECRET = "你的_App_Secret"
FEISHU_APP_TOKEN = "你的_多维表格_App_Token"
FEISHU_TABLE_ID = "你的_数据表_ID"
3. 运行应用
<BASH>
streamlit run app.py
📁 项目结构 (v2.0)
<TEXT>
.
├── app.py                    # 主程序入口 (包含 UI 和 业务逻辑)
├── requirements.txt          # 依赖列表
├── clients/                  # 核心功能模块
│   ├── gemini_client.py      # Gemini 2.0 Flash 调用封装 (含图片处理)
│   └── feishu_client.py      # 飞书多维表格读写封装
├── utils/                    # 工具包
│   └── ...
└── .streamlit/
    └── secrets.toml          # 配置文件 (不要提交到 Git)
🔧 部署指南 (Streamlit Cloud)
如果你要将此版本部署到 Streamlit Cloud，请注意以下几点：

分支选择：部署时 Branch 务必选择 v2.0-stable。
配置 Secrets：在 Streamlit Cloud 后台的 "Advanced settings" -> "Secrets" 中填入上述配置。
网络设置：云端部署不需要代理，请确保代码中没有强制开启 os.environ['HTTPS_PROXY']。
📜 版本历史
v2.0-stable (Current):
移除 DeepSeek，锁定 Gemini 2.0 Flash。
新增“保存全部历史”功能。
修复大图上传崩溃 bug。
移除前端 Key 输入，统一使用 Secrets。
v1.0 (MVP):
集成 DeepSeek 和 Gemini 双模型。
支持前端手动输入 Key。
🤝 致谢
Google Gemini - 提供强大的多模态 AI 能力
Feishu Open Platform - 提供稳定的多维表格 API
Streamlit - 让 AI 应用开发变得简单
最后更新：2026-02-03