from google import genai
from google.genai import types
import streamlit as st
import os
import PIL.Image
from datetime import datetime

# --- 强制代理 (保持不变) ---
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 Gemini API Key")
        
        try:
            # 初始化客户端
            self.client = genai.Client(api_key=self.api_key)
            # 强制固定模型，不再动态选择，确保稳定
            self.model_name = "gemini-2.0-flash" 
            print(f"DEBUG: 客户端初始化成功，锁定模型: {self.model_name}")
        except Exception as e:
            print(f"ERROR: 客户端初始化失败: {e}")
            raise e

    def _compress_image(self, image_file):
        """
        压缩图片防止 Server disconnected 或超时。
        将尺寸限制更严格一点 (800px)，提高成功率。
        """
        try:
            image_file.seek(0)
            img = PIL.Image.open(image_file).convert('RGB')
            max_size = 800  # 缩小一点尺寸，防止包体过大断开连接
            
            # 如果图片本来就小，就不动
            if max(img.size) <= max_size:
                return img
                
            img.thumbnail((max_size, max_size))
            print(f"DEBUG: 图片已压缩至 {img.size}")
            return img
        except Exception as e:
            print(f"WARN: 图片压缩失败，使用原图: {e}")
            return PIL.Image.open(image_file)

    def _build_history(self, chat_history):
        """构建纯文本历史上下文"""
        contents = []
        for msg in chat_history:
            # 跳过包含图片的旧消息，避免旧图片导致上下文格式错误
            if "image" in msg and msg["image"]:
                continue
                
            role = "user" if msg["role"] == "user" else "model"
            if isinstance(msg["content"], str):
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                ))
        return contents

    def generate_content(self, prompt, chat_history=[]):
        """纯文本对话"""
        try:
            history_contents = self._build_history(chat_history)
            
            # 加入当前提示词
            history_contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            print(f"DEBUG: 发送文本请求...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=history_contents
            )
            return response.text
        except Exception as e:
            return f"请求失败: {str(e)}"

    def analyze_image(self, image_file, prompt="请描述这张图片"):
        """图片分析"""
        try:
            # 1. 压缩图片
            img = self._compress_image(image_file)
            
            print(f"DEBUG: 发送图片请求...")
            # 2. 发送请求 (Gemini 2.0 Flash 对图片支持很好)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img]
            )
            return response.text
        except Exception as e:
            return f"图片分析失败: {str(e)}"

