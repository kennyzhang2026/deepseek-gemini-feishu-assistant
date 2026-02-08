import streamlit as st
import os
import platform
from PIL import Image
from clients.gemini_client import GeminiClient
from clients.feishu_client import FeishuClient

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 全能助手", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS ---
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
    
    /* 确保侧边栏在手机端也显示 */
    @media (max-width: 640px) {
        [data-testid="stSidebar"] {
            display: block !important;
            position: relative !important;
            width: 100% !important;
        }
        [data-testid="stSidebarContent"] {
            display: block !important;
            width: 100% !important;
        }
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. 环境 ---
system_name = platform.system()
if system_name == "Windows":
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
else:
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if key in os.environ: del os.environ[key]

# --- 4. 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 强制初始化
if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = GeminiClient()
    except Exception as e:
        st.error(f"⚠️ 服务连接失败: {e}")

# ================= 侧边栏 =================
with st.sidebar:
    st.title("🎛️ 控制面板")
    
    # --- 🔥 动态显示当前自动选中的模型 ---
    if "gemini_client" in st.session_state:
        current_model = st.session_state.gemini_client.model_name
        # 去掉 'models/' 前缀为了好看点
        display_name = current_model.replace("models/", "") if current_model else "未知"
        
        st.success(f"✅ 已连接: {display_name}")
        
        # 调试信息：如果觉得模型不对，点开这个看详情
        with st.expander("🔍 为什么是这个模型？"):
            st.caption("系统自动检测了你的 API Key 支持的列表，并选择了其中最强的。")
            st.text(f"实际调用 ID: {current_model}")
    else:
        st.warning("正在连接...")

    st.subheader("1. 视觉分析")
    uploaded_file = st.file_uploader("上传图片", type=['png', 'jpg', 'jpeg'])
    st.divider()

    st.subheader("2. 飞书存档")
    if st.button("💾 存最近一轮", use_container_width=True):
        last_u, last_a = "", ""
        if len(st.session_state.messages) >= 2:
            for m in reversed(st.session_state.messages):
                if m['role'] == 'user' and not last_u: last_u = m['content']
                if m['role'] == 'assistant' and not last_a: last_a = m['content']
                if last_u and last_a: break
        if last_u and last_a:
            try:
                feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                # 记录里带上真实模型名
                m_name = st.session_state.gemini_client.model_name.replace("models/", "")
                feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], feishu.format_chat_record(last_u, last_a, m_name))
                st.toast("✅ 保存成功")
            except Exception as e: st.error(f"失败: {e}")
        else: st.warning("无内容")

    if st.button("📚 存全部历史", use_container_width=True):
        msgs = st.session_state.messages
        if msgs:
            try:
                feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                progress = st.progress(0)
                cnt = 0
                m_name = st.session_state.gemini_client.model_name.replace("models/", "")
                total = len(msgs)//2
                i=0
                while i < len(msgs)-1:
                    if msgs[i]['role']=='user' and msgs[i+1]['role']=='assistant':
                        feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], feishu.format_chat_record(msgs[i]['content'], msgs[i+1]['content'], f"{m_name}[Hist]"))
                        cnt+=1
                        if total>0: progress.progress(min(cnt/total, 1.0))
                        i+=2
                    else: i+=1
                progress.empty()
                st.toast(f"✅ 已存 {cnt} 条")
            except Exception as e: st.error(f"出错: {e}")
        else: st.warning("无记录")

    st.divider()
    if st.button("🗑️ 刷新并重置连接", type="primary"):
        st.session_state.messages = []
        if "gemini_client" in st.session_state:
            del st.session_state.gemini_client
        st.rerun()

# ================= 主界面 =================
# 动态标题
model_display = "正在连接..."
if "gemini_client" in st.session_state:
    model_display = st.session_state.gemini_client.model_name.replace("models/", "")

st.header(f"🤖 AI 助手 ({model_display})")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=250)
        st.markdown(message["content"])

if prompt := st.chat_input("输入问题..."):
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
            msg_box.markdown("Thinking...")
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

# ================= 底部工具栏（为手机端用户显示飞书保存功能）=================
st.divider()
st.markdown("### 💾 飞书存档")

save_col1, save_col2 = st.columns(2)

with save_col1:
    if st.button("📌 存最近一轮", use_container_width=True, key="save_recent"):
        last_u, last_a = "", ""
        if len(st.session_state.messages) >= 2:
            for m in reversed(st.session_state.messages):
                if m['role'] == 'user' and not last_u: last_u = m['content']
                if m['role'] == 'assistant' and not last_a: last_a = m['content']
                if last_u and last_a: break
        if last_u and last_a:
            try:
                feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                m_name = st.session_state.gemini_client.model_name.replace("models/", "")
                feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], feishu.format_chat_record(last_u, last_a, m_name))
                st.toast("✅ 保存成功")
            except Exception as e: st.error(f"失败: {e}")
        else: st.warning("无内容")

with save_col2:
    if st.button("📚 存全部历史", use_container_width=True, key="save_all"):
        msgs = st.session_state.messages
        if msgs:
            try:
                feishu = FeishuClient(st.secrets["FEISHU_APP_ID"], st.secrets["FEISHU_APP_SECRET"], st.secrets["FEISHU_APP_TOKEN"])
                progress = st.progress(0)
                cnt = 0
                m_name = st.session_state.gemini_client.model_name.replace("models/", "")
                total = len(msgs)//2
                i=0
                while i < len(msgs)-1:
                    if msgs[i]['role']=='user' and msgs[i+1]['role']=='assistant':
                        feishu.add_record_to_bitable(st.secrets["FEISHU_TABLE_ID"], feishu.format_chat_record(msgs[i]['content'], msgs[i+1]['content'], f"{m_name}[Hist]"))
                        cnt+=1
                        if total>0: progress.progress(min(cnt/total, 1.0))
                        i+=2
                    else: i+=1
                progress.empty()
                st.toast(f"✅ 已存 {cnt} 条")
            except Exception as e: st.error(f"出错: {e}")
        else: st.warning("无记录")


