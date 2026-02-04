import streamlit as st
import os
import platform
import sys
# --- 🔥 【核弹级】环境与代理配置 (必须放在最开头) ---
# 这一步必须在 import 任何网络库之前执行
system_name = platform.system()
if system_name == "Windows":
    # 本地开发环境：开启代理
    print(f"🖥️ [App] 检测到 {system_name}，开启代理...")
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
else:
    # 云端/Linux 环境：强力清除所有代理
    print(f"☁️ [App] 检测到 {system_name}，执行去代理操作...")
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if key in os.environ:
            del os.environ[key]
# ------------------------------------------------
import time
from PIL import Image

# --- 强制代理 ---
#os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
#os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

from clients.gemini_client import GeminiClient
from clients.feishu_client import FeishuClient

st.set_page_config(page_title="AI 全能助手", layout="wide", initial_sidebar_state="expanded")
# ... 你的 st.set_page_config(...) 代码 ...

# --- 隐藏 Streamlit 默认的汉堡菜单、页脚和顶部栏 ---
# --- 隐藏 Streamlit 默认样式 (加强版) ---
# --- 隐藏 Streamlit 默认样式 (最终清爽版) ---
# --- 最终终结版 CSS ---
hide_streamlit_style = """
<style>
    /* 1. 全局隐藏 footer 容器 */
    footer {visibility: hidden !important; display: none !important;}
    
    /* 2. 隐藏右上角菜单和顶部 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 3. 专门针对 "Hosted with Streamlit" (它是 footer 里的一个链接) */
    footer a {display: none !important;}
    
    /* 4. 暴力隐藏所有指向 streamlit.io 的链接 (防止它改头换面) */
    a[href*="streamlit.io"] {display: none !important;}
    
    /* 5. 隐藏部署按钮 */
    .stDeployButton {display:none;}
    
    /* 6. 补充：针对新版界面的浮动按钮容器 */
    [data-testid="stStatusWidget"] {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)




# ... 后面接着写你的其余代码 ...

# --- 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = GeminiClient()
    except Exception as e:
        st.error(f"无法连接 AI 服务: {e}")

# ================= 侧边栏：控制与保存 =================
with st.sidebar:
    st.title("🎛️ 控制面板")
    
    st.info("当前模型: Gemini 2.0 Flash (自动锁定)")
    
    # 1. 图片上传
    st.subheader("1. 视觉分析")
    uploaded_file = st.file_uploader("上传图片 (分析完记得点 X 删除)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()

    # 2. 飞书存档 (功能升级)
    st.subheader("2. 飞书存档")
    
    col_save_1, col_save_2 = st.columns(2)
    
    # --- 按钮 A: 存最近一轮 ---
    with col_save_1:
        if st.button("💾 存最近一轮"):
            # 寻找最近的一对 User/Assistant 对话
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
                    records = feishu.format_chat_record(last_user, last_ai, "Gemini-2.0-Flash")
                    res = feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                    if res["success"]:
                        st.toast("✅ 最近一轮已保存", icon="🎉")
                    else:
                        st.error(f"保存失败: {res['error']}")
                except Exception as e:
                    st.error(f"系统错误: {e}")
            else:
                st.warning("没有可保存的对话")

    # --- 按钮 B: 存全部历史 (新开发功能) ---
    with col_save_2:
        if st.button("📚 存全部历史"):
            msgs = st.session_state.messages
            if not msgs:
                st.warning("记录为空")
            else:
                try:
                    feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                    
                    # 进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 逻辑：遍历历史，找到成对的 User -> Assistant
                    # 假设对话顺序通常是 User, Assistant, User, Assistant...
                    count = 0
                    total_pairs = len(msgs) // 2
                    
                    # 使用 while 循环来匹配问答对
                    i = 0
                    saved_count = 0
                    
                    while i < len(msgs) - 1:
                        current_msg = msgs[i]
                        next_msg = msgs[i+1]
                        
                        # 只有当这是 "User 提问" 且下一条是 "Assistant 回答" 时才保存
                        if current_msg['role'] == 'user' and next_msg['role'] == 'assistant':
                            
                            # 准备内容
                            u_text = current_msg['content']
                            a_text = next_msg['content']
                            
                            status_text.text(f"正在保存第 {saved_count + 1} 组对话...")
                            
                            # 发送保存请求
                            records = feishu.format_chat_record(u_text, a_text, "Gemini-2.0-Flash[History]")
                            feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], records)
                            
                            saved_count += 1
                            # 更新进度条
                            if total_pairs > 0:
                                progress_bar.progress(min(saved_count / total_pairs, 1.0))
                            
                            # 跳过这两条，继续找下一对
                            i += 2 
                        else:
                            # 如果顺序不对（比如连续两条 User），就跳过这一条
                            i += 1
                    
                    progress_bar.empty()
                    status_text.empty()
                    st.toast(f"🎉 全部保存完成！共保存 {saved_count} 组对话", icon="✅")
                    
                except Exception as e:
                    st.error(f"批量保存出错: {e}")

    st.divider()
    if st.button("🗑️ 清空所有对话", type="primary"):
        st.session_state.messages = []
        st.rerun()

# ================= 主界面 =================

st.header("🤖 AI 助手 (Gemini 2.0 Flash)")

# 显示历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=250)
        st.markdown(message["content"])

# 输入框
if prompt := st.chat_input("输入你的问题..."):
    if "gemini_client" not in st.session_state:
        st.error("请刷新页面重试")
    else:
        # 用户消息
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

        # AI 回复
        with st.chat_message("assistant"):
            msg_box = st.empty()
            msg_box.markdown("Thinking...")
            
            try:
                if uploaded_file:
                    # 图片模式
                    response = st.session_state.gemini_client.analyze_image(uploaded_file, prompt)
                else:
                    # 文本模式 (过滤掉图片，防止历史记录报错)
                    text_history = [m for m in st.session_state.messages if "image" not in m][:-1]
                    response = st.session_state.gemini_client.generate_content(prompt, chat_history=text_history)
                
                msg_box.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.toast("回复完成，可点击左侧保存", icon="✅")

            except Exception as e:
                msg_box.error(f"Error: {e}")

