from google import genai
from google.genai import types
import streamlit as st
import PIL.Image
import io

class GeminiClient:
    def __init__(self, api_key=None):
        # 优先从传入参数获取，否则从 secrets 获取
        self.api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 Gemini API Key")
        
        try:
            # 初始化客户端
            self.client = genai.Client(api_key=self.api_key)
            
            # --- 🔥 关键修改：切换为 Gemini 1.5 Pro (最强逻辑版) ---
            self.model_name = "gemini-1.5-pro" 
            
            print(f"DEBUG: 客户端初始化成功，锁定模型: {self.model_name}")
        except Exception as e:
            print(f"ERROR: 客户端初始化失败: {e}")
            raise e

    def _compress_image(self, image_file):
        """保留你的压缩逻辑"""
        try:
            # 如果是 BytesIO 对象，重置指针
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            img = PIL.Image.open(image_file).convert('RGB')
            max_size = 800
            
            # 如果图片本来就小，就不动
            if max(img.size) <= max_size:
                return img
                
            img.thumbnail((max_size, max_size))
            print(f"DEBUG: 图片已压缩至 {img.size}")
            return img
        except Exception as e:
            print(f"WARN: 图片压缩失败，使用原图: {e}")
            # 如果出错，重新打开并返回
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            return PIL.Image.open(image_file)

    def _build_history(self, chat_history):
        """保留你的历史记录构建逻辑"""
        contents = []
        for msg in chat_history:
            # 跳过包含图片的旧消息，避免混淆文本历史
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

            print(f"DEBUG: 发送文本请求 (Model: {self.model_name})...")
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
            
            print(f"DEBUG: 发送图片请求 (Model: {self.model_name})...")
            # 2. 发送请求
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img]
            )
            return response.text
        except Exception as e:
            return f"图片分析失败: {str(e)}"
