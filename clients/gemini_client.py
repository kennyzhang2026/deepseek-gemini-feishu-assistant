from google import genai
from PIL import Image
import io

class GeminiClient:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        # === 使用 Google 最新版 SDK (google-genai) ===
        try:
            self.client = genai.Client(api_key=api_key)
            
            # 强制修正：如果用户传的是旧的 1.5，我们强制改成 2.0，因为你的账号只支持 2.0
            if "1.5" in model_name:
                print(f"WARNING: 检测到旧模型 {model_name}，自动升级为 gemini-2.0-flash")
                self.model_name = "gemini-2.0-flash"
            else:
                self.model_name = model_name.replace("models/", "")
            
            print(f"DEBUG: 客户端启动成功 - 当前使用模型: {self.model_name}")
            
        except Exception as e:
            print(f"ERROR: 客户端初始化失败: {e}")

    def get_response(self, message, image_input=None, image_data=None, **kwargs):
        """
        使用新版 google-genai SDK 发送请求
        """
        # 兼容参数
        img_bytes = image_input if image_input is not None else image_data
        
        try:
            contents = [message]

            if img_bytes:
                print("DEBUG: 正在处理图片...")
                image = Image.open(io.BytesIO(img_bytes))
                contents.append(image)

            print(f"DEBUG: 正在发送请求给 {self.model_name}...")

            # === 发送请求 ===
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            
            return {
                "success": True,
                "content": response.text,
                "model": self.model_name
            }

        except Exception as e:
            err_msg = str(e)
            print(f"ERROR: API 调用出错: {err_msg}")
            
            if "404" in err_msg:
                return {"success": False, "error": f"模型 {self.model_name} 不存在，请尝试在代码中将 model_name 改为 'gemini-flash-latest'"}
            
            return {"success": False, "error": f"Gemini 报错: {err_msg}"}

