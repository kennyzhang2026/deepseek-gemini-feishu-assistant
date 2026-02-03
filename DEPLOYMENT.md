<MARKDOWN>
# ☁️ Streamlit Cloud 部署指南 (v2.0-stable)
本指南详细说明如何将 **Gemini 2.0 Flash (v2.0)** 版本部署到 Streamlit Cloud，并与 v1.0 MVP 版本共存。
## 📋 前置要求
在开始部署之前，请确保：
1. 代码已提交到 GitHub 的 **`v2.0-stable`** 分支。
2. 拥有有效的 **Gemini API Key** 和 **飞书应用配置**。
3. 拥有 Streamlit Cloud 账号。
## ⚠️ 关键代码检查 (部署前必读)
**Streamlit Cloud 服务器位于海外，不需要（也不能）使用本地代理。**
请务必检查 `app.py` 或 `clients/gemini_client.py`，确保以下代码被**注释掉**或**删除**，否则云端应用会无法连接网络：
```python
# ❌ 部署到云端时，必须注释掉这两行！
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
🚀 部署步骤
步骤 1：确认代码已推送到 v2.0 分支
在你的本地终端执行：

<BASH>
# 切换到 v2.0 分支
git checkout v2.0-stable
# 提交所有更改
git add .
git commit -m "Prepare for v2.0 deployment"
# 推送到 GitHub
git push origin v2.0-stable
步骤 2：在 Streamlit Cloud 创建新应用
登录: 访问 Streamlit Cloud。

新建: 点击 "New app"。

配置仓库信息:

Repository: 选择你的仓库 deepseek-gemini-feishu-assistant。
Branch (至关重要): 🚨 必须选择 v2.0-stable (不要选 main)。
Main file path: app.py。
自定义 URL (区分版本):

在 "App URL" 选项中，建议设置一个带版本号的后缀。
例如：yourname-ai-assistant-v2。
这样你的访问地址就是：https://yourname-ai-assistant-v2.streamlit.app。
步骤 3：配置密钥 (Secrets)
v2.0 版本不再需要 DeepSeek Key，且移除了前端输入框，必须在此配置。

点击 "Advanced settings" -> "Secrets"。
粘贴以下内容（替换为你自己的 Key）：
<TOML>
# --- Google Gemini 配置 ---
GEMINI_API_KEY = "你的_Gemini_API_Key"
# --- 飞书多维表格 配置 ---
FEISHU_APP_ID = "cli_xxxxxxxxxx"
FEISHU_APP_SECRET = "xxxxxxxxxxxxxxxxxxxx"
FEISHU_APP_TOKEN = "xxxxxxxxxxxxxxxxxxxx"
FEISHU_TABLE_ID = "tblxxxxxxxxxxxx"
步骤 4：点击部署 (Deploy)
点击 "Deploy" 按钮。系统会自动安装 requirements.txt 中的依赖（google-genai, streamlit 等）。等待 1-2 分钟，看到气球动画即表示成功。

📊 部署后验证
进入你的新 URL (v2.0版)，按以下流程测试：

检查 UI: 确认侧边栏没有 API Key 输入框（说明配置加载成功）。
测试对话: 发送 "你好"，确认 Gemini 2.0 Flash 秒级回复。
测试识图: 上传一张图片，确认没有报错且能正确识别。
测试飞书存档:
进行几轮对话。
点击侧边栏的 "保存全部历史到飞书"。
观察进度条是否走完，并去飞书表格确认数据是否写入。
🔧 常见故障排除
1. 报错 Connection Error 或 Proxy Error
原因：代码里残留了 os.environ['HTTPS_PROXY'] 设置。
解决：回到 VS Code，注释掉代理设置，重新 push 到 v2.0-stable 分支，Streamlit Cloud 会自动检测更新并重启。
2. 报错 ModuleNotFoundError: No module named 'openai'
原因：你可能错误地选择了 main 分支进行部署，或者 requirements.txt 没有更新。
解决：删除这个 App，重新部署，并在 Branch 选项中仔细确认选的是 v2.0-stable。
3. 飞书写入失败 (Code 9999/400)
原因：Secrets 里的 FEISHU_APP_TOKEN 或 TABLE_ID 填错了。
解决：检查 Secrets 配置，确保没有多余的空格或引号错误。
部署状态检查表：

 选择了 v2.0-stable 分支
 设置了区别于 MVP 的自定义 URL (如 ...-v2)
 Secrets 中配置了 Gemini 和 飞书 Key
 代码中已移除/注释 Proxy 代理设置
 看到气球动画 🎈
最后更新：2026-02-03