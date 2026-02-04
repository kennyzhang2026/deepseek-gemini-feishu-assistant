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
            
            # --- 🔥 核心改变：不再硬编码，而是自动寻找最佳模型 ---
            self.model_name = self._get_best_available_model()
            
            print(f"DEBUG: 最终选定的模型是: {self.model_name}")

        except Exception as e:
            print(f"ERROR: 客户端初始化失败: {e}")
            raise e

    def _get_best_available_model(self):
        """
        自动查询 API Key 支持的所有模型，并按优先级选择最好的。
        """
        try:
            print("DEBUG: 正在向 Google 查询可用模型列表...")
            # 1. 获取所有可用模型
            all_models_iterator = self.client.models.list()
            # 提取支持 generateContent 的模型名称
            available_models = []
            for m in all_models_iterator:
                # 新版 SDK 的 model 对象通常包含 supported_generation_methods
                if hasattr(m, 'supported_generation_methods') and 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
                # 兼容性处理：如果属性名不同，或者默认都支持
                elif hasattr(m, 'name'):
                    available_models.append(m.name)

            print(f"DEBUG: Google 返回了 {len(available_models)} 个可用模型: {available_models}")

            # 2. 定义优先级：我们想要最强的逻辑 (Pro)，其次是 Flash
            # 注意：Google 返回的名字通常是 "models/gemini-1.5-pro-001" 这种全称
            priority_keywords = [
                "gemini-1.5-pro-002", # 最强逻辑
                "gemini-1.5-pro",     # 通用 Pro
                "gemini-1.5-pro-latest",
                "gemini-1.5-pro-001",
                "gemini-2.0-flash",   # 新版 Flash (作为 Pro 的备选)
                "gemini-1.5-flash",   # 旧版 Flash
                "gemini-pro"          # 最老的 Pro
            ]

            # 3. 匹配逻辑
            for keyword in priority_keywords:
                for real_name in available_models:
                    # 如果关键词在真名里（例如 "gemini-1.5-pro" 在 "models/gemini-1.5-pro-001" 里）
                    if keyword in real_name:
                        return real_name # 直接返回这个百分百存在的真名

            # 4. 如果没找到任何心仪的，就拿列表里第一个能用的
            if available_models:
                return available_models[0]
            
            # 5. 绝望兜底（如果 list 失败了，还是得试一个）
            return "gemini-1.5-flash"

        except Exception as e:
            print(f"WARN: 自动侦测模型失败 ({e})，回退到安全模式。")
            return "gemini-1.5-flash"

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
            
            # 使用自动侦测到的 model_name
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=history_contents
            )
            return response.text
        except Exception as e:
            return f"请求失败 (Model: {self.model_name}): {str(e)}"

    def analyze_image(self, image_file, prompt="请描述这张图片"):
        try:
            img = self._compress_image(image_file)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img]
            )
            return response.text
        except Exception as e:
            return f"图片分析失败 (Model: {self.model_name}): {str(e)}"

