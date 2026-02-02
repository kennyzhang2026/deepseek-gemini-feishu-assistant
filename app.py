"""
DeepSeek & Gemini 聊天助手 + 飞书知识库 Streamlit 应用
主程序文件 - 阶段二：AI集成 + 聊天界面 (布局优化版)
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

# ==================== 代理设置初始化 ====================
def initialize_proxy_settings():
    """初始化代理设置"""
    proxy_url = st.session_state.get('proxy_url', '').strip()
    if proxy_url:
        os.environ['http_proxy'] = proxy_url
        os.environ['https_proxy'] = proxy_url

# ==================== Session State 初始化 ====================
if "deepseek_api_key" not in st.session_state:
    st.session_state.deepseek_api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
    
if "feishu_app_id" not in st.session_state:
    st.session_state.feishu_app_id = st.secrets.get("FEISHU_APP_ID", "")
    
if "feishu_app_secret" not in st.session_state:
    st.session_state.feishu_app_secret = st.secrets.get("FEISHU_APP_SECRET", "")
    
if "feishu_table_id" not in st.session_state:
    st.session_state.feishu_table_id = st.secrets.get("FEISHU_TABLE_ID", "")
    
if "feishu_app_token" not in st.session_state:
    st.session_state.feishu_app_token = st.secrets.get("FEISHU_BASE_ID", st.secrets.get("FEISHU_APP_TOKEN", ""))

if "proxy_url" not in st.session_state:
    st.session_state.proxy_url = "http://127.0.0.1:7890"

if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = "gemini-1.5-flash"

if "config_status" not in st.session_state:
    st.session_state.config_status = {
        "deepseek": False,
        "gemini": False,
        "feishu": False
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "router" not in st.session_state:
    st.session_state.router = Router()

if "ai_clients_initialized" not in st.session_state:
    st.session_state.ai_clients_initialized = False

initialize_proxy_settings()

# ==================== 辅助函数 ====================
def update_config_status():
    st.session_state.config_status["deepseek"] = bool(st.session_state.deepseek_api_key.strip())
    st.session_state.config_status["gemini"] = bool(st.session_state.gemini_api_key.strip())
    st.session_state.config_status["feishu"] = bool(
        st.session_state.feishu_app_id.strip() and
        st.session_state.feishu_app_secret.strip() and
        st.session_state.feishu_app_token.strip() and
        st.session_state.feishu_table_id.strip()
    )

def get_status_emoji(status):
    return "🟢" if status else "🔴"

def initialize_ai_clients():
    if st.session_state.ai_clients_initialized:
        return True
    try:
        if st.session_state.get('proxy_url'):
            os.environ['http_proxy'] = st.session_state.proxy_url
            os.environ['https_proxy'] = st.session_state.proxy_url
        
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
    if not st.session_state.config_status["deepseek"] and not st.session_state.config_status["gemini"]:
        return {"success": False, "error": "请至少配置一个AI服务", "content": None}
    
    if not initialize_ai_clients():
        return {"success": False, "error": "AI客户端初始化失败", "content": None}
    
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
    if not st.session_state.config_status["feishu"]:
        st.error("请先配置完整的飞书信息")
        return False
    
    if len(st.session_state.messages) < 2:
        st.warning("没有完整的对话记录可保存")
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
        st.warning("未找到完整的对话记录")
        return False
    
    try:
        client = FeishuClient(
            app_id=st.session_state.feishu_app_id,
            app_secret=st.session_state.feishu_app_secret,
            app_token=st.session_state.feishu_app_token
        )
        
        with st.spinner("正在保存到飞书..."):
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
    st.title("⚙️ 设置")

    # 🔥🔥 【调整】把上传图片放到最显眼的顶部 🔥🔥
    st.subheader("📷 图片上传")
    uploaded_image = st.file_uploader("上传图片给 Gemini", type=['png', 'jpg', 'jpeg'], key="image_uploader")
    if uploaded_image:
        st.session_state.current_image = uploaded_image
        st.image(uploaded_image, caption="已准备好发送", width=200)
    else:
        st.session_state.current_image = None
    
    st.divider() # 分割线

    # 原有的配置区域
    with st.expander("🌐 网络与模型设置", expanded=False): # 默认收起，节省空间
        proxy_url = st.text_input(
            "代理地址",
            value=st.session_state.proxy_url,
            key="proxy_url_input",
            on_change=lambda: setattr(st.session_state, 'proxy_url', st.session_state.proxy_url_input)
        )
        gemini_model = st.selectbox(
            "Gemini 模型",
            options=['gemini-1.5-flash', 'gemini-1.5-pro'],
            index=0,
            key="gemini_model_input",
            on_change=lambda: setattr(st.session_state, 'gemini_model', st.session_state.gemini_model_input)
        )
    
    with st.expander("🔑 API Key 设置", expanded=False):
        st.text_input(
            "DeepSeek Key",
            value=st.session_state.deepseek_api_key,
            type="password",
            key="deepseek_key_input",
            on_change=lambda: setattr(st.session_state, 'deepseek_api_key', st.session_state.deepseek_key_input)
        )
        st.text_input(
            "Gemini Key",
            value=st.session_state.gemini_api_key,
            type="password",
            key="gemini_key_input",
            on_change=lambda: setattr(st.session_state, 'gemini_api_key', st.session_state.gemini_key_input)
        )

    with st.expander("📚 飞书配置", expanded=True): # 飞书配置默认展开
        st.text_input("App ID", value=st.session_state.feishu_app_id, key="feishu_app_id_input", on_change=lambda: setattr(st.session_state, 'feishu_app_id', st.session_state.feishu_app_id_input))
        st.text_input("App Secret", value=st.session_state.feishu_app_secret, type="password", key="feishu_app_secret_input", on_change=lambda: setattr(st.session_state, 'feishu_app_secret', st.session_state.feishu_app_secret_input))
        st.text_input("Base ID (Token)", value=st.session_state.feishu_app_token, key="feishu_app_token_input", on_change=lambda: setattr(st.session_state, 'feishu_app_token', st.session_state.feishu_app_token_input))
        st.text_input("Table ID", value=st.session_state.feishu_table_id, key="feishu_table_id_input", on_change=lambda: setattr(st.session_state, 'feishu_table_id', st.session_state.feishu_table_id_input))
    
    update_config_status()
    
    st.subheader("状态")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: st.metric("DeepSeek", get_status_emoji(st.session_state.config_status["deepseek"]))
    with sc2: st.metric("Gemini", get_status_emoji(st.session_state.config_status["gemini"]))
    with sc3: st.metric("飞书", get_status_emoji(st.session_state.config_status["feishu"]))
    
    if st.button("🗑️ 清空聊天", use_container_width=True):
        clear_chat_history()

# ==================== 主界面区域 ====================
st.title("🤖 DeepSeek & Gemini 智能助手")

# 聊天记录容器
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("image_preview"):
                st.image(message["image_preview"], width=200)
            st.markdown(message["content"])
            if message.get("model"):
                st.caption(f"使用 {message['model']} 生成")

# 输入框和底部按钮
# 保持输入框在最下方
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
    
    # 注意：这里不自动清除 current_image，以便用户可以针对同一张图继续提问
    # 如果想发完就清，可以在这里把 st.session_state.current_image = None (由于是 file_uploader，重置比较麻烦，通常保留即可)

# 底部功能按钮
col_btn1, col_btn2 = st.columns(2)
with col_btn1: 
    if st.button("💾 保存当前对话到飞书", use_container_width=True): save_to_feishu()
with col_btn2:
    if st.button("🔄 刷新界面", use_container_width=True): st.rerun()
