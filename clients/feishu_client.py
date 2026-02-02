"""
飞书多维表格 API 客户端模块
用于将对话记录保存到飞书多维表格
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

# 配置日志
logger = logging.getLogger(__name__)


class FeishuClient:
    """飞书多维表格 API 客户端"""
    
    # 飞书API端点
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    BITABLE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    
    def __init__(self, app_id: str, app_secret: str, app_token: str):
        """
        初始化飞书客户端
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        
        # Token缓存
        self._access_token = None
        self._token_expiry = 0  # Token过期时间戳
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        
        logger.info("飞书客户端初始化完成")
    
    def _get_tenant_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        获取租户访问令牌（带缓存机制，有效期2小时）
        """
        # 检查缓存是否有效（有效期2小时，提前5分钟刷新）
        current_time = time.time()
        if (not force_refresh and 
            self._access_token and 
            current_time < self._token_expiry - 300):  # 提前5分钟刷新
            logger.debug("使用缓存的访问令牌")
            return self._access_token
        
        logger.info("获取新的访问令牌")
        
        # 请求获取令牌
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    self._access_token = data.get("tenant_access_token")
                    # 设置过期时间（2小时 = 7200秒）
                    self._token_expiry = current_time + 7200
                    logger.info("访问令牌获取成功")
                    return self._access_token
                else:
                    logger.error(f"获取令牌失败: {data.get('msg')}")
                    return None
            else:
                logger.error(f"获取令牌HTTP错误: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取令牌网络错误: {e}")
            return None
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        带重试机制的HTTP请求
        """
        for attempt in range(self.max_retries):
            try:
                # 确保有有效的访问令牌
                token = self._get_tenant_access_token()
                if not token:
                    logger.error("无法获取有效的访问令牌")
                    return None
                
                # 添加认证头
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f'Bearer {token}'
                kwargs['headers'] = headers
                
                # 发送请求
                response = requests.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0:
                        return data
                    else:
                        logger.warning(f"API返回错误: {data.get('msg')}")
                        # 如果是令牌过期，强制刷新并重试
                        if data.get("code") == 99991663 and attempt < self.max_retries - 1:
                            logger.info("令牌过期，强制刷新并重试")
                            self._get_tenant_access_token(force_refresh=True)
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        return None
                else:
                    logger.warning(f"HTTP错误 {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                return None
        
        logger.error(f"所有 {self.max_retries} 次重试均失败")
        return None
    
    def add_record_to_bitable(self, table_id: str, fields: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        添加记录到飞书多维表格
        """
        # 统一处理：将单个字段转换为列表
        if isinstance(fields, dict):
            fields_list = [fields]
        else:
            fields_list = fields
        
        # 验证必填字段
        required_fields = ['sectionID', '时间', 'role', 'user_question', 'AI_answer', 'tags']
        record_ids = []
        
        for field_data in fields_list:
            for field in required_fields:
                if field not in field_data:
                    return {
                        "success": False,
                        "error": f"缺少必填字段: {field}",
                        "record_ids": []
                    }
        
        # 构建URL
        url = self.BITABLE_URL.format(
            app_token=self.app_token,
            table_id=table_id
        )
        
        logger.info(f"添加 {len(fields_list)} 条记录到表格 {table_id}")
        
        # 批量添加记录（飞书API支持批量添加）
        payload = {
            "records": [
                {"fields": field_data}
                for field_data in fields_list
            ]
        }
        
        # 发送请求
        response_data = self._make_request_with_retry(
            method="POST",
            url=url + "/batch_create",  # 使用批量创建接口
            headers={"Content-Type": "application/json; charset=utf-8"},
            json=payload,
            timeout=30
        )
        
        if response_data:
            records = response_data.get("data", {}).get("records", [])
            record_ids = [record.get("record_id") for record in records if record.get("record_id")]
            
            if record_ids:
                return {
                    "success": True,
                    "error": None,
                    "record_ids": record_ids
                }
            else:
                return {
                    "success": False,
                    "error": "添加记录成功但未返回记录ID",
                    "record_ids": []
                }
        else:
            return {
                "success": False,
                "error": "添加记录失败，请检查网络连接和权限",
                "record_ids": []
            }
    
    def format_chat_record(self, user_question: str, ai_answer: str,
                          model_used: str = "unknown") -> List[Dict[str, Any]]:
        """
        格式化聊天记录为飞书多维表格字段
        """
        # 生成唯一的会话ID（两条记录共享）
        session_id = str(uuid.uuid4())
        
        # === 关键修正 ===
        # 使用 13位 毫秒级时间戳 (Integer) 替代字符串，解决 DatetimeFieldConvFail 问题
        current_time = int(time.time() * 1000)
        
        # 用户消息记录
        user_record = {
            "sectionID": session_id,
            "时间": current_time,
            "role": "user",
            "user_question": user_question,
            "AI_answer": "",  # 用户消息时AI回答留空
            "tags": ["AI助手存档"]
        }
        
        # AI消息记录
        ai_record = {
            "sectionID": session_id,
            "时间": current_time,
            "role": "assistant",
            "user_question": "",  # AI消息时用户问题留空
            "AI_answer": f"{ai_answer}\n\n---\n*使用模型: {model_used}*",
            "tags": [model_used]  # 使用模型作为标签
        }
        
        return [user_record, ai_record]
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试飞书API连接
        """
        logger.info("测试飞书API连接")
        
        # 测试获取令牌
        token = self._get_tenant_access_token()
        if not token:
            return {
                "success": False,
                "error": "无法获取访问令牌，请检查App ID和App Secret",
                "details": None
            }
        
        # 测试简单的API调用（获取应用信息）
        test_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}"
        
        response_data = self._make_request_with_retry(
            method="GET",
            url=test_url,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=10
        )
        
        if response_data:
            return {
                "success": True,
                "error": None,
                "details": {
                    "app_token": self.app_token,
                    "token_valid": True,
                    "app_info": response_data.get("data", {})
                }
            }
        else:
            return {
                "success": False,
                "error": "无法访问飞书应用，请检查App Token和权限",
                "details": None
            }
