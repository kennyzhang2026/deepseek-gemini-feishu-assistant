"""
DeepSeek & Gemini 聊天助手 + 飞书知识库 Streamlit 应用
主程序文件 - 修复版：自动读取 Secrets + 图片上传 + 飞书集成
"""

import streamlit as st
import logging
from typing import List, Dict, Any
from PIL import Image
import io
import os

# 导入自定义模块
from clients.deepseek_client import DeepSeekClient
from clients.gemini_client import GeminiClient
from clients.feishu_client import FeishuClient
from utils.router import Router

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="DeepSeek & Gemini 助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Session State 初始化 ====================
# 这里不仅初始化 Session，还会优先尝试从 Secrets 获取默认值
def init_session_state(key, secret_name, default_value=""):
    if key not in st.session_state:
        # 尝试从 secrets 读取，读取不到则使用默认值
        st.session_state[key] = st.secrets.get(secret_name, default_value)

# 初始化所有关键变量
init_session_state("deepseek_api_key", "DEEPSEEK_API_KEY")
init_session_state("gemini_api_key", "GEMINI_API_KEY")
init_session_state("feishu_app_id", "FEISHU_APP_ID")
init_session_state("feishu_app_secret", "FEISHU_APP_SECRET")
init_session_state("feishu_table_id", "FEISHU_TABLE_ID")
# 飞书 Token 可能有两个名字，做一个兼容
base_token = st.secrets.get("FEISHU_BASE_ID", st.secrets.get("FEISHU_APP_TOKEN", ""))
init_session_state("feishu_app_token", "FEISHU_APP_TOKEN", base_token)

if "proxy_url" not in st.session_state:
    st.session_state.proxy_url = ""

if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = "gemini-1.5-flash"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "router" not in st.session_state:
    st.session_state.router = Router()

if "ai_clients_initialized" not in st.session_state:
    st.session_state.ai_clients_initialized = False

# ==================== 辅助函数 ====================
def initialize_proxy_settings():
    """初始化代理设置"""
    proxy_url = st.session_state.get('proxy_url', '').strip()
    if proxy_url:
        os.environ['http_proxy'] = proxy_url
        os.environ['https_proxy'] = proxy_url
    else:
        # 🟢 关键修改：如果为空，必须显式删除环境变量！
        # 否则之前设置的 127.0.0.1 还会一直残留，导致连接错误
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)

initialize_proxy_settings()

def get_config_status():
    """检查配置是否完整"""
    ds_status = bool(st.session_state.deepseek_api_key.strip())
    gemini_status = bool(st.session_state.gemini_api_key.strip())
    feishu_status = bool(
        st.session_state.feishu_app_id.strip() and
        st.session_state.feishu_app_secret.strip() and
        st.session_state.feishu_app_token.strip() and
        st.session_state.feishu_table_id.strip()
    )
    return {"deepseek": ds_status, "gemini": gemini_status, "feishu": feishu_status}

def get_status_emoji(status):
    return "🟢" if status else "🔴"

def initialize_ai_clients():
    if st.session_state.ai_clients_initialized:
        return True
    try:
        # 应用代理
        initialize_proxy_settings()
        
        if st.session_state.deepseek_api_key:
            deepseek_client = DeepSeekClient(st.session_state.deepseek_api_key)
            st.session_state.router.register_client('deepseek', deepseek_client)
        
        if st.session_state.gemini_api_key:
            gemini_client = GeminiClient(
                api_key=st.session_state.gemini_api_key,
                model_name=st.session_state.gemini_model
            )
            st.session_state.router.register_client('gemini', gemini_client)
        
        st.session_state.ai_clients_initialized = True
        return True
    except Exception as e:
        st.error(f"AI客户端初始化失败: {e}")
        return False

def process_message(message: str, image_data=None):
    status = get_config_status()
    if not status["deepseek"] and not status["gemini"]:
        return {"success": False, "error": "请至少配置一个 AI 服务的 API Key", "content": None}
    
    # 每次处理前确保客户端已初始化
    initialize_ai_clients()
    
    try:
        if image_data:
            image_bytes = image_data.getvalue()
            result = st.session_state.router.route(message=message, image_input=image_bytes)
        else:
            result = st.session_state.router.route(message=message)
        return result
    except Exception as e:
        return {"success": False, "error": f"处理消息时出错: {str(e)}", "content": None}

def clear_chat_history():
    st.session_state.messages = []
    st.session_state.current_image = None
    st.success("聊天历史已清空")

def save_to_feishu():
    status = get_config_status()
    if not status["feishu"]:
        st.error("请先在左侧配置完整的飞书 App ID, Secret, Token 和 Table ID")
        return False
    
    if len(st.session_state.messages) < 2:
        st.warning("对话记录太短，无法保存")
        return False
    
    # 获取最近一轮对话
    user_question = None
    ai_answer = None
    model_used = "unknown"
    
    for i in range(len(st.session_state.messages) - 1, -1, -1):
        msg = st.session_state.messages[i]
        if msg["role"] == "assistant" and ai_answer is None:
            ai_answer = msg["content"]
            model_used = msg.get("model", "unknown")
        elif msg["role"] == "user" and user_question is None:
            user_question = msg["content"]
        
        if user_question is not None and ai_answer is not None:
            break
    
    if not user_question or not ai_answer:
        st.warning("未找到完整的问答对")
        return False
    
    try:
        client = FeishuClient(
            app_id=st.session_state.feishu_app_id,
            app_secret=st.session_state.feishu_app_secret,
            app_token=st.session_state.feishu_app_token
        )
        
        with st.spinner("正在保存到飞书多维表格..."):
            records = client.format_chat_record(
                user_question=user_question,
                ai_answer=ai_answer,
                model_used=model_used
            )
            result = client.add_record_to_bitable(
                table_id=st.session_state.feishu_table_id,
                fields=records
            )
        
        if result["success"]:
            st.success(f"✅ 已成功保存到飞书！")
            return True
        else:
            st.error(f"保存失败: {result['error']}")
            return False
            
    except Exception as e:
        st.error(f"保存过程中发生错误: {str(e)}")
        return False

# ==================== 侧边栏配置区域 ====================
with st.sidebar:
    st.title("⚙️ 设置面板")

    # 1. 图片上传 (最上方)
    st.subheader("📷 图片上传")
    uploaded_image = st.file_uploader("上传图片给 Gemini", type=['png', 'jpg', 'jpeg'], key="image_uploader")
    if uploaded_image:
        st.session_state.current_image = uploaded_image
        st.image(uploaded_image, caption="已准备好发送", width=200)
    else:
        st.session_state.current_image = None
    
    st.divider()

    # 2. 网络与模型
    with st.expander("🌐 网络与模型", expanded=False):
        st.text_input("代理地址", key="proxy_url")
        st.selectbox(
            "Gemini 模型",
            options=['gemini-1.5-flash', 'gemini-1.5-pro'],
            key="gemini_model"
        )
    
    # 3. API Key 设置 (使用 Streamlit 原生绑定，自动读取 Secrets)
    with st.expander("🔑 API Key 设置", expanded=True):
        st.text_input("DeepSeek Key", type="password", key="deepseek_api_key")
        st.text_input("Gemini Key", type="password", key="gemini_api_key")

    # 4. 飞书配置 (使用 Streamlit 原生绑定，自动读取 Secrets)
    with st.expander("📚 飞书配置", expanded=True):
        st.text_input("App ID", key="feishu_app_id")
        st.text_input("App Secret", type="password", key="feishu_app_secret")
        st.text_input("Base ID (Token)", key="feishu_app_token")
        st.text_input("Table ID", key="feishu_table_id")
    
    # 状态指示灯
    status = get_config_status()
    st.divider()
    st.subheader("服务状态")
    c1, c2, c3 = st.columns(3)
    c1.metric("DeepSeek", get_status_emoji(status["deepseek"]))
    c2.metric("Gemini", get_status_emoji(status["gemini"]))
    c3.metric("飞书", get_status_emoji(status["feishu"]))
    
    if st.button("🗑️ 清空聊天", use_container_width=True):
        clear_chat_history()

# ==================== 主界面区域 ====================
st.title("🤖 DeepSeek & Gemini 智能助手")

# 聊天记录容器
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.info("👋 你好！我是你的 AI 助手。你可以问我问题，或者上传图片让我分析。")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("image_preview"):
                st.image(message["image_preview"], width=200)
            st.markdown(message["content"])
            if message.get("model"):
                st.caption(f"使用 {message['model']} 生成")

# 输入框和底部按钮
st.divider()
user_input = st.chat_input("输入您的问题...", key="chat_input")

if user_input:
    # 构造用户消息
    user_message = {"role": "user", "content": user_input, "image_preview": None}
    
    # 检查侧边栏是否有图片
    if st.session_state.current_image:
        image = Image.open(st.session_state.current_image)
        user_message["image_preview"] = image
    
    st.session_state.messages.append(user_message)
    
    # 显示用户消息
    with chat_container:
        with st.chat_message("user"):
            if user_message["image_preview"]: st.image(user_message["image_preview"], width=200)
            st.markdown(user_input)
    
    # AI 处理
    with st.spinner("AI 正在思考..."):
        result = process_message(message=user_input, image_data=st.session_state.current_image)
    
    # 处理结果
    if result["success"]:
        ai_message = {"role": "assistant", "content": result["content"], "model": result.get("model", "unknown")}
        st.session_state.messages.append(ai_message)
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(result["content"])
                st.caption(f"使用 {result.get('model', 'unknown')} 生成")
    else:
        st.session_state.messages.append({"role": "assistant", "content": f"❌ {result['error']}", "model": "error"})
        with chat_container:
            with st.chat_message("assistant"): st.error(result["error"])

# 底部功能按钮
col_btn1, col_btn2 = st.columns(2)
with col_btn1: 
    if st.button("💾 保存当前对话到飞书", use_container_width=True): save_to_feishu()
with col_btn2:
    if st.button("🔄 刷新界面", use_container_width=True): st.rerun()
