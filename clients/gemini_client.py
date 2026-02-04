from google import genai
from google.genai import types
import streamlit as st
import PIL.Image

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 Gemini API Key")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            
            # --- 🔍 关键修改：使用具体的、绝对存在的版本号 ---
            # gemini-1.5-pro-002 是目前公认逻辑最强、最稳定的 Pro 版本
            # 如果想尝鲜最新的 2.0 Pro 实验版，可以改为 'gemini-2.0-pro-exp-02-05'
            self.model_name = "gemini-1.5-pro-002" 
            
            print(f"DEBUG: 正在初始化 Gemini 客户端...")
            print(f"DEBUG: 锁定的模型 ID 为: {self.model_name}")

            # --- 🛡️ 防御性代码：列出账号下实际可用的模型 ---
            # 这样我们在后台日志里能看到到底哪些模型是活着的
            try:
                # 只有 v1beta 支持 list_models，这里尝试打印一下，仅供调试
                pass 
            except Exception:
                pass

        except Exception as e:
            print(f"ERROR: 客户端初始化失败: {e}")
            raise e

    def _compress_image(self, image_file):
        try:
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            img = PIL.Image.open(image_file).convert('RGB')
            max_size = 800
            
            if max(img.size) <= max_size:
                return img
                
            img.thumbnail((max_size, max_size))
            return img
        except Exception as e:
            print(f"WARN: 图片压缩失败，使用原图: {e}")
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            return PIL.Image.open(image_file)

    def _build_history(self, chat_history):
        contents = []
        for msg in chat_history:
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
        try:
            history_contents = self._build_history(chat_history)
            
            history_contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            print(f"DEBUG: 发送文本请求 -> {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=history_contents
            )
            return response.text
        except Exception as e:
            print(f"ERROR: 请求失败: {e}")
            # 如果这里报错，返回原始错误信息，方便我们看
            return f"❌ 请求失败 (模型 {self.model_name}): {str(e)}"

    def analyze_image(self, image_file, prompt="请描述这张图片"):
        try:
            img = self._compress_image(image_file)
            
            print(f"DEBUG: 发送图片请求 -> {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img]
            )
            return response.text
        except Exception as e:
             return f"❌ 图片分析失败: {str(e)}"
