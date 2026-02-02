# Streamlit Cloud 部署指南

本指南详细说明如何将 DeepSeek & Gemini Assistant with Feishu Knowledge Base 应用部署到 Streamlit Cloud。

## 📋 前置要求

在开始部署之前，请确保：
1. 项目代码已准备就绪（`app.py`, `requirements.txt`, 所有客户端模块）
2. 拥有有效的 API 密钥（DeepSeek、Gemini、飞书）
3. 拥有 GitHub 账号
4. 拥有 Streamlit Cloud 账号（免费版即可）

## 🚀 部署步骤

### 步骤 1：准备 GitHub 仓库

1. **初始化 Git 仓库**（如果尚未初始化）
   ```bash
   cd deepseek-gemini-feishu-assistant
   git init
   ```

2. **添加所有文件并提交**
   ```bash
   git add .
   git commit -m "Initial commit: DeepSeek & Gemini Assistant with Feishu Integration"
   ```

3. **创建 GitHub 仓库**
   - 访问 [GitHub](https://github.com)
   - 点击右上角 "+" → "New repository"
   - 输入仓库名称（如 `deepseek-gemini-feishu-assistant`）
   - 选择公开（Public）或私有（Private）
   - **不要**添加 README、.gitignore 或 license（我们已经有了）

4. **推送代码到 GitHub**
   ```bash
   git remote add origin https://github.com/你的用户名/仓库名称.git
   git branch -M main
   git push -u origin main
   ```

### 步骤 2：Streamlit Cloud 设置

1. **登录 Streamlit Cloud**
   - 访问 [Streamlit Cloud](https://streamlit.io/cloud)
   - 使用 GitHub 账号登录

2. **创建新应用**
   - 点击 "New app" 按钮
   - 选择你的 GitHub 仓库
   - 选择分支（通常为 `main`）
   - 设置主文件路径为 `app.py`

3. **配置应用设置**
   - **应用标题**：DeepSeek & Gemini Assistant
   - **Python 版本**：选择 3.9+（推荐 3.10）
   - **高级设置**：保持默认

### 步骤 3：密钥管理（最关键步骤）

**⚠️ 重要安全警告**：`.streamlit/secrets.toml` 文件**绝对不能**提交到 GitHub。我们已经将其添加到 `.gitignore` 中。

#### 在 Streamlit Cloud 中设置密钥：

1. 在 Streamlit Cloud 应用页面，点击 "Advanced settings"（右上角三个点 → Settings）
2. 找到 "Secrets" 部分
3. 将以下内容粘贴到文本框中：

```toml
# 将以下值替换为你的实际 API 密钥
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GEMINI_API_KEY = "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
FEISHU_APP_ID = "cli_xxxxxxxxxxxx"
FEISHU_APP_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
FEISHU_APP_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
FEISHU_TABLE_ID = "tblxxxxxxxxxxxxxxxx"
```

#### 密钥说明：

| 密钥名称 | 说明 | 获取方式 |
|---------|------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | [DeepSeek 控制台](https://platform.deepseek.com/) |
| `GEMINI_API_KEY` | Gemini API 密钥 | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `FEISHU_APP_ID` | 飞书应用 ID | [飞书开放平台](https://open.feishu.cn/) |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 同上 |
| `FEISHU_APP_TOKEN` | 飞书应用 Token（多维表格所在应用） | 飞书多维表格页面 URL 中获取 |
| `FEISHU_TABLE_ID` | 飞书多维表格 ID | 同上 |

### 步骤 4：部署应用

1. **保存设置并部署**
   - 点击 "Save" 保存密钥设置
   - 返回应用页面，点击 "Deploy" 或等待自动部署

2. **监控部署过程**
   - Streamlit Cloud 会自动安装 `requirements.txt` 中的依赖
   - 部署过程通常需要 1-3 分钟
   - 查看日志以确认部署成功

3. **验证部署**
   - 部署完成后，应用将有一个公开 URL（如 `https://app-name.streamlit.app`）
   - 访问该 URL 测试应用功能

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 部署失败：依赖安装错误
- **症状**：部署日志显示 `ModuleNotFoundError` 或 `pip install` 失败
- **解决方案**：
  - 检查 `requirements.txt` 格式是否正确
  - 确保所有依赖都有正确的版本号
  - 尝试简化依赖版本（如移除版本限制）

#### 2. 应用启动失败：密钥未设置
- **症状**：应用显示 "API Key not configured" 或类似错误
- **解决方案**：
  - 确认已在 Streamlit Cloud Secrets 中正确设置所有密钥
  - 检查密钥名称是否完全匹配（大小写敏感）
  - 重新部署应用

#### 3. API 调用失败：网络问题
- **症状**：AI 回复超时或飞书写入失败
- **解决方案**：
  - 检查 API 密钥是否有效
  - 确认飞书应用有正确的权限（需要访问多维表格）
  - 在侧边栏启用代理设置（如果需要）

#### 4. 内存不足错误
- **症状**：应用崩溃，日志显示内存不足
- **解决方案**：
  - Streamlit Cloud 免费版有内存限制
  - 优化代码，减少内存使用
  - 考虑升级到付费计划

## 📊 部署后验证

部署完成后，请执行以下验证：

1. **访问应用 URL**，确认应用正常加载
2. **检查侧边栏配置**，确认密钥已从 Secrets 加载
3. **测试文本聊天**，验证 DeepSeek 正常工作
4. **测试图片上传**，验证 Gemini 正常工作
5. **测试飞书写入**，验证数据能保存到飞书多维表格

## 🔐 安全最佳实践

1. **密钥保护**
   - 永远不要在代码中硬编码 API 密钥
   - 使用 Streamlit Cloud Secrets 管理密钥
   - 定期轮换 API 密钥

2. **访问控制**
   - 考虑将 GitHub 仓库设为私有
   - 限制 Streamlit 应用的访问权限（如果需要）
   - 监控 API 使用情况，防止滥用

3. **数据隐私**
   - 应用使用 BYOK（Bring Your Own Keys）模式
   - 对话记录仅保存在用户自己的飞书多维表格中
   - 应用本身不存储任何用户数据

## 🌐 自定义域名（可选）

如果需要使用自定义域名：

1. 在 Streamlit Cloud 设置中配置自定义域名
2. 在域名服务商处添加 CNAME 记录
3. 等待 DNS 传播（最多 24 小时）

## 📞 支持与帮助

- **Streamlit Cloud 文档**：[https://docs.streamlit.io/cloud](https://docs.streamlit.io/cloud)
- **GitHub 问题**：在项目仓库中创建 Issue
- **社区支持**：[Streamlit 论坛](https://discuss.streamlit.io/)

---

**部署状态检查表**：
- [ ] GitHub 仓库已创建并推送代码
- [ ] Streamlit Cloud 账号已登录
- [ ] 应用已创建并连接到 GitHub 仓库
- [ ] 所有 API 密钥已正确设置到 Streamlit Cloud Secrets
- [ ] 应用部署成功并可访问
- [ ] 基本功能测试通过

**最后更新**：2026-02-02