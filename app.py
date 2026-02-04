import streamlit as st
import os
import platform
import sys
from PIL import Image
from clients.gemini_client import GeminiClient
from clients.feishu_client import FeishuClient

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 全能助手", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS 样式 (纯净版，已去除所有调试红条) ---
hide_streamlit_style = """
<style>
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {display: none !important;}
    a[href*="streamlit"] {display: none !important;}
    div:has(> a[href*="streamlit"]) {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. 环境配置 ---
system_name = platform.system()
if system_name == "Windows":
    print(f"🖥️ [App] Windows 环境: 开启代理")
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
else:
    print(f"☁️ [App] 云端环境: 清除代理")
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if key in os.environ:
            del os.environ[key]

# --- 4. 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 强制重置 Client 以应用新模型
if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = GeminiClient()
    except Exception as e:
        st.error(f"⚠️ AI 服务连接失败: {e}")

# ================= 侧边栏 =================
with st.sidebar:
    st.title("🎛️ 控制面板")
    
    # 明确显示当前使用的硬编码版本号
    st.info("当前模型: Gemini 1.5 Pro-002 (高智商版)")
    
    st.subheader("1. 视觉分析")
    uploaded_file = st.file_uploader("上传图片", type=['png', 'jpg', 'jpeg'])
    
    st.divider()

    st.subheader("2. 飞书存档")
    col_save_1, col_save_2 = st.columns(2)
    
    with col_save_1:
        if st.button("💾 存最近一轮"):
            last_user = ""
            last_ai = ""
            if len(st.session_state.messages) >= 2:
                for m in reversed(st.session_state.messages):
                    if m['role'] == 'user' and not last_user: last_user = m['content']
                    if m['role'] == 'assistant' and not last_ai: last_ai = m['content']
                    if last_user and last_ai: break
            
            if last_user and last_ai:
                try:
                    feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                    records = feishu.format_chat_record(last_user, last_ai, "Gemini-1.5-Pro-002")
                    res = feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                    if res["success"]:
                        st.toast("✅ 保存成功", icon="🎉")
                    else:
                        st.error(f"保存失败: {res['error']}")
                except Exception as e:
                    st.error(f"系统错误: {e}")
            else:
                st.warning("无内容")

    with col_save_2:
        if st.button("📚 存全部历史"):
            msgs = st.session_state.messages
            if not msgs:
                st.warning("无记录")
            else:
                try:
                    feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                    progress_bar = st.progress(0)
                    total_pairs = len(msgs) // 2
                    i = 0
                    saved_count = 0
                    while i < len(msgs) - 1:
                        if msgs[i]['role'] == 'user' and msgs[i+1]['role'] == 'assistant':
                            records = feishu.format_chat_record(msgs[i]['content'], msgs[i+1]['content'], "Gemini-1.5-Pro-002[History]")
                            feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                            saved_count += 1
                            if total_pairs > 0: progress_bar.progress(min(saved_count / total_pairs, 1.0))
                            i += 2 
                        else:
                            i += 1
                    progress_bar.empty()
                    st.toast(f"✅ 已保存 {saved_count} 条", icon="🎉")
                except Exception as e:
                    st.error(f"出错: {e}")

    st.divider()
    if st.button("🗑️ 清空并重置", type="primary"):
        st.session_state.messages = []
        if "gemini_client" in st.session_state:
            del st.session_state.gemini_client
        st.rerun()

# ================= 主界面 =================
st.header("🤖 AI 助手 (Gemini 1.5 Pro-002)")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=250)
        st.markdown(message["content"])

if prompt := st.chat_input("输入问题 (已切换至 1.5 Pro-002)..."):
    if "gemini_client" not in st.session_state:
        st.error("请点击左下角重置按钮")
    else:
        user_msg = {"role": "user", "content": prompt}
        if uploaded_file:
            uploaded_file.seek(0)
            img_show = Image.open(uploaded_file)
            user_msg["image"] = img_show
            with st.chat_message("user"):
                st.image(img_show, width=250)
                st.markdown(prompt)
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        st.session_state.messages.append(user_msg)

        with st.chat_message("assistant"):
            msg_box = st.empty()
            msg_box.markdown("Thinking (1.5 Pro-002)...")
            try:
                if uploaded_file:
                    response = st.session_state.gemini_client.analyze_image(uploaded_file, prompt)
                else:
                    text_history = [m for m in st.session_state.messages if "image" not in m][:-1]
                    response = st.session_state.gemini_client.generate_content(prompt, chat_history=text_history)
                
                msg_box.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                msg_box.error(f"Error: {e}")

