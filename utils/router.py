"""
路由逻辑模块
根据输入类型决定调用哪个 AI 模型
"""

import logging
from typing import Dict, Any, Optional, Union
from PIL import Image
import io

# 配置日志
logger = logging.getLogger(__name__)


class Router:
    """AI 模型路由器"""
    
    def __init__(self):
        """初始化路由器"""
        self.clients = {}
    
    def register_client(self, client_type: str, client):
        """
        注册客户端
        
        Args:
            client_type: 客户端类型 ('gemini')
            client: 客户端实例
        """
        self.clients[client_type] = client
        logger.info(f"已注册 {client_type} 客户端")
    
    def route(self,
              message: str,
              image_input: Optional[Union[str, bytes, Image.Image]] = None,
              **kwargs) -> Dict[str, Any]:
        """
        路由请求到合适的 AI 模型
        
        Args:
            message: 用户输入的消息
            image_input: 图片输入，可以是文件路径、字节数据或 PIL Image 对象
            **kwargs: 其他参数
            
        Returns:
            Dict 包含响应内容和路由信息
        """
        # 无论是否有图片，都使用 Gemini（因为只有 Gemini 支持图片）
        return self._call_gemini(message, image_input, **kwargs)
    
    def _call_gemini(self,
                    prompt: str, 
                    image_input: Union[str, bytes, Image.Image],
                    **kwargs) -> Dict[str, Any]:
        """
        调用 Gemini 处理图片
        
        Args:
            prompt: 用户输入的提示词
            image_input: 图片输入
            **kwargs: 其他参数
            
        Returns:
            Dict 包含响应内容
        """
        if 'gemini' not in self.clients:
            return {
                "success": False,
                "error": "Gemini 客户端未注册",
                "content": None,
                "model": "gemini",
                "routed": False
            }
        
        try:
            client = self.clients['gemini']
            result = client.get_response(prompt, image_input=image_input, **kwargs)
            result["model"] = "gemini"
            result["routed"] = True
            return result
        except Exception as e:
            logger.error(f"Gemini 调用失败: {e}")
            return {
                "success": False,
                "error": f"Gemini 调用失败: {str(e)}",
                "content": None,
                "model": "gemini",
                "routed": False
            }
    
    def get_route_info(self,
                      message: str,
                      image_input: Optional[Union[str, bytes, Image.Image]] = None) -> Dict[str, Any]:
        """
        获取路由信息（不实际调用）
        
        Args:
            message: 用户输入的消息
            image_input: 图片输入
            
        Returns:
            Dict 包含路由决策信息
        """
        if image_input is not None:
            model = "gemini"
            reason = "检测到图片输入，使用 Gemini 进行图片理解"
        else:
            model = "gemini"
            reason = "纯文本输入，使用 Gemini 进行文本对话"
        
        return {
            "model": model,
            "reason": reason,
            "has_image": image_input is not None,
            "message_length": len(message)
        }


def should_use_gemini(image_input: Optional[Union[str, bytes, Image.Image]] = None) -> bool:
    """
    判断是否应该使用 Gemini
    
    Args:
        image_input: 图片输入
        
    Returns:
        bool: 是否使用 Gemini
    """
    return True


def get_appropriate_model(image_input: Optional[Union[str, bytes, Image.Image]] = None) -> str:
    """
    获取合适的模型名称
    
    Args:
        image_input: 图片输入
        
    Returns:
        str: 模型名称 ('gemini')
    """
    return "gemini"


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试函数
    def test_router():
        """测试路由器"""
        print("=== 路由器测试 ===")
        
        # 创建路由器
        router = Router()
        
        # 测试路由决策
        print("1. 测试路由决策:")
        
        # 纯文本
        route_info = router.get_route_info("你好")
        print(f"   纯文本输入: {route_info}")
        
        # 模拟图片输入
        route_info = router.get_route_info("描述这张图片", image_input="test.jpg")
        print(f"   图片输入: {route_info}")
        
        # 测试工具函数
        print("\n2. 测试工具函数:")
        print(f"   应该使用 Gemini (无图片): {should_use_gemini()}")
        print(f"   应该使用 Gemini (有图片): {should_use_gemini('test.jpg')}")
        print(f"   合适模型 (无图片): {get_appropriate_model()}")
        print(f"   合适模型 (有图片): {get_appropriate_model('test.jpg')}")
        
        print("\n=== 测试完成 ===")
    
    test_router()