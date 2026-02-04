import streamlit as st
import os
import platform
import sys
import time
from PIL import Image
from clients.gemini_client import GeminiClient
from clients.feishu_client import FeishuClient

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="AI 全能助手", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS 样式 (保留最强版，已删除调试红条) ---
hide_streamlit_style = """
<style>
    /* 1. 隐藏顶部 */
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* 2. 隐藏底部 Footer */
    footer {display: none !important;}
    
    /* 3. 隐藏 Streamlit 红框徽章 (强力版) */
    a[href*="streamlit"] {display: none !important;}
    div:has(> a[href*="streamlit"]) {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    
    /* 4. 隐藏右侧部署按钮 */
    .stDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. 环境与代理配置 ---
system_name = platform.system()
if system_name == "Windows":
    # 本地开发环境
    print(f"🖥️ [App] 检测到 {system_name}，开启代理...")
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
else:
    # 云端环境
    print(f"☁️ [App] 检测到 {system_name}，清除代理...")
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if key in os.environ:
            del os.environ[key]

# --- 4. 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = GeminiClient()
    except Exception as e:
        st.error(f"无法连接 AI 服务: {e}")

# ================= 5. 侧边栏：控制与保存 =================
with st.sidebar:
    st.title("🎛️ 控制面板")
    
    # --- 更新：显示当前使用的是 Pro 模型 ---
    st.info("当前模型: Gemini 1.5 Pro (强逻辑版)")
    
    # 1. 图片上传
    st.subheader("1. 视觉分析")
    uploaded_file = st.file_uploader("上传图片 (分析完记得点 X 删除)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()

    # 2. 飞书存档
    st.subheader("2. 飞书存档")
    
    col_save_1, col_save_2 = st.columns(2)
    
    # --- 按钮 A: 存最近一轮 ---
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
                    # --- 更新：标签改为 1.5 Pro ---
                    records = feishu.format_chat_record(last_user, last_ai, "Gemini-1.5-Pro")
                    res = feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                    if res["success"]:
                        st.toast("✅ 最近一轮已保存", icon="🎉")
                    else:
                        st.error(f"保存失败: {res['error']}")
                except Exception as e:
                    st.error(f"系统错误: {e}")
            else:
                st.warning("没有可保存的对话")

    # --- 按钮 B: 存全部历史 ---
    with col_save_2:
        if st.button("📚 存全部历史"):
            msgs = st.session_state.messages
            if not msgs:
                st.warning("记录为空")
            else:
                try:
                    feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total_pairs = len(msgs) // 2
                    i = 0
                    saved_count = 0
                    
                    while i < len(msgs) - 1:
                        current_msg = msgs[i]
                        next_msg = msgs[i+1]
                        
                        if current_msg['role'] == 'user' and next_msg['role'] == 'assistant':
                            u_text = current_msg['content']
                            a_text = next_msg['content']
                            
                            status_text.text(f"正在保存第 {saved_count + 1} 组对话...")
                            # --- 更新：标签改为 1.5 Pro ---
                            records = feishu.format_chat_record(u_text, a_text, "Gemini-1.5-Pro[History]")
                            feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                            
                            saved_count += 1
                            if total_pairs > 0:
                                progress_bar.progress(min(saved_count / total_pairs, 1.0))
                            
                            i += 2 
                        else:
                            i += 1
                    
                    progress_bar.empty()
                    status_text.empty()
                    st.toast(f"🎉 全部保存完成！共保存 {saved_count} 组对话", icon="✅")
                    
                except Exception as e:
                    st.error(f"批量保存出错: {e}")

    st.divider()
    # 点击清空时，删除缓存，确保下次重新加载新模型
    if st.button("🗑️ 清空所有对话", type="primary"):
        st.session_state.messages = []
        if "gemini_client" in st.session_state:
            del st.session_state.gemini_client
        st.rerun()

# ================= 6. 主界面逻辑 =================

# --- 更新：标题 ---
st.header("🤖 AI 助手 (Gemini 1.5 Pro)")

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=250)
        st.markdown(message["content"])

# 输入处理
if prompt := st.chat_input("输入你的问题..."):
    if "gemini_client" not in st.session_state:
        st.error("请刷新页面重试")
    else:
        # 1. 显示用户消息
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

        # 2. 生成 AI 回复
        with st.chat_message("assistant"):
            msg_box = st.empty()
            msg_box.markdown("Thinking (1.5 Pro)...")
            
            try:
                if uploaded_file:
                    # 图片模式
                    response = st.session_state.gemini_client.analyze_image(uploaded_file, prompt)
                else:
                    # 文本模式 (过滤掉图片对象)
                    text_history = [m for m in st.session_state.messages if "image" not in m][:-1]
                    response = st.session_state.gemini_client.generate_content(prompt, chat_history=text_history)
                
                msg_box.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.toast("回复完成", icon="✅")

            except Exception as e:
                msg_box.error(f"Error: {e}")
