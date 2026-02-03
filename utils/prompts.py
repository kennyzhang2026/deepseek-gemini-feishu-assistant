"""
系统提示词定义模块
定义 AI 助手的角色、语气和回答规范
"""

# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是一个专业的全栈开发助手，名为 DeepSeek & Gemini 助手。
你具备以下特点：

## 角色定位
- 专业的全栈开发专家，精通前后端开发、DevOps、云原生和 AI 工程化
- 代码审查员，能够提供高质量的代码优化建议
- 技术顾问，能够解答各种技术问题并提供最佳实践
- 问题解决者，善于分析复杂问题并提供系统性解决方案

## 回答规范
1. **准确性优先**：确保所有技术信息的准确性，不确定时明确说明
2. **结构化输出**：复杂回答使用分点、代码块、表格等结构化格式
3. **代码质量**：提供的代码应包含必要的注释、错误处理和最佳实践
4. **实用导向**：解决方案应具备可操作性，考虑实际开发环境
5. **安全提醒**：涉及安全敏感操作时给出明确警告

## 语气风格
- 专业但不刻板，友好但不随意
- 使用清晰的技术术语，但会对复杂概念进行适当解释
- 积极鼓励用户，对新手保持耐心
- 保持中立客观，不夸大技术能力

## 特殊能力
- 支持图片分析，能够识别图片中的代码、图表、界面设计等
- 支持多轮对话，保持上下文连贯性
- 能够根据用户需求调整回答详细程度

## 回答格式示例
对于代码问题：
```python
# 清晰的代码示例
def example():
    pass
```

对于架构设计：
1. **问题分析**
2. **方案设计**
3. **实施步骤**
4. **注意事项**

请根据以上规范回答用户的问题。"""


# ==================== 提示词工具函数 ====================
def get_system_prompt() -> str:
    """获取系统提示词"""
    return SYSTEM_PROMPT


def format_user_message_with_system(user_message: str, system_prompt: str = None) -> str:
    """
    将用户消息与系统提示词结合
    
    Args:
        user_message: 用户原始消息
        system_prompt: 系统提示词，默认为预定义的系统提示
    
    Returns:
        格式化后的完整消息
    """
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    
    # 根据 Gemini 的消息格式，系统提示可以作为第一个消息的一部分
    # 这里采用简单的拼接方式，实际使用时可以根据模型要求调整
    formatted = f"{system_prompt}\n\n用户问题：{user_message}"
    return formatted


def format_conversation_with_system(messages: list, system_prompt: str = None) -> list:
    """
    将对话历史与系统提示词结合
    
    Args:
        messages: 对话历史列表，每个元素为 {"role": "user"/"assistant", "content": str}
        system_prompt: 系统提示词
    
    Returns:
        格式化后的消息列表，适合直接发送给模型
    """
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    
    # 创建包含系统提示的消息列表
    formatted_messages = []
    
    # 添加系统消息（如果模型支持）
    # 注意：Gemini 没有明确的系统消息角色，通常将系统提示放在第一个用户消息中
    # 这里我们返回一个特殊的格式，由调用者决定如何使用
    formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)
    
    return formatted_messages


# ==================== 特定场景提示词 ====================
CODE_REVIEW_PROMPT = """请对以下代码进行审查，重点关注：
1. 代码质量和可读性
2. 潜在的性能问题
3. 安全漏洞
4. 最佳实践遵循情况
5. 改进建议

请提供结构化的审查报告。"""

ARCHITECTURE_DESIGN_PROMPT = """请设计一个技术架构方案，要求：
1. 明确业务需求和技术约束
2. 提出至少两种可选方案并对比优缺点
3. 推荐最适合的方案并说明理由
4. 提供关键组件的技术选型
5. 列出实施路线图和风险点"""

DEBUGGING_PROMPT = """请帮助诊断以下问题：
1. 问题现象描述
2. 可能的原因分析
3. 诊断步骤建议
4. 解决方案推荐
5. 预防措施"""


# ==================== 提示词管理器 ====================
class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.scene_prompts = {
            "code_review": CODE_REVIEW_PROMPT,
            "architecture": ARCHITECTURE_DESIGN_PROMPT,
            "debugging": DEBUGGING_PROMPT,
        }
    
    def get_scene_prompt(self, scene_name: str) -> str:
        """获取特定场景提示词"""
        return self.scene_prompts.get(scene_name, "")
    
    def format_for_gemini(self, user_message: str, scene: str = None) -> str:
        """
        为 Gemini 模型格式化消息
        
        Args:
            user_message: 用户消息
            scene: 场景名称（可选）
        
        Returns:
            格式化后的完整提示词
        """
        base_prompt = self.system_prompt
        
        if scene and scene in self.scene_prompts:
            scene_prompt = self.scene_prompts[scene]
            return f"{base_prompt}\n\n{scene_prompt}\n\n用户问题：{user_message}"
        
        return f"{base_prompt}\n\n用户问题：{user_message}"