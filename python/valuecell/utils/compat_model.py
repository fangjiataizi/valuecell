"""
LLM 模型兼容层

为不支持 'developer' 角色的 LLM 提供商（如 Qwen、DeepSeek）提供兼容性支持。
通过消息拦截和角色转换，使其能够与 Agno 框架正常工作。
"""

import os
from typing import Any, Dict, List, Optional
import functools

from agno.models.base import Model
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter

# 全局标志，确保只 monkey patch 一次
_GLOBAL_PATCHED = False


class CompatibleOpenAIChat(OpenAIChat):
    """
    兼容 Qwen 和 DeepSeek 的 OpenAI Chat 模型包装器
    
    主要功能：
    1. 将 'developer' 角色转换为 'system' 角色
    2. 合并连续的 system 消息以符合 API 要求
    """
    
    def __init__(self, *args, role_mapping: Optional[Dict[str, str]] = None, **kwargs):
        """
        初始化兼容的 OpenAI Chat 模型
        
        Args:
            role_mapping: 角色映射字典，例如 {"developer": "system"}
            其他参数传递给父类
        """
        super().__init__(*args, **kwargs)
        self.role_mapping = role_mapping or {"developer": "system"}
        
        # 覆盖 role_map
        # Agno 默认将 'system' 映射为 'developer'，但通义千问不支持 developer
        # 我们需要完整覆盖 role_map，保持 system -> system
        self.role_map = {
            'system': 'system',      # 不要映射为 developer
            'user': 'user',
            'assistant': 'assistant',
            'tool': 'tool',
            'model': 'assistant',
            'developer': 'system',   # 防御性：如果还有 developer 就映射为 system
        }
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("🎁 [CompatModel] 模型初始化完成，role_map 已设置")
        
        # 立即进行全局 monkey patch（只做一次）
        self._apply_global_patch()
    
    def _apply_global_patch(self):
        """在 OpenAI 类级别应用 monkey patch，确保所有实例都被拦截"""
        global _GLOBAL_PATCHED
        
        if _GLOBAL_PATCHED:
            return
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("🔧 [CompatModel] 开始全局 monkey patch OpenAI client")
        
        try:
            from openai import OpenAI
            
            # 保存原始的 __init__ 方法
            original_init = OpenAI.__init__
            
            # 创建包装的 __init__
            def wrapped_init(client_self, *args, **kwargs):
                # 调用原始 __init__
                original_init(client_self, *args, **kwargs)
                
                # 包装 chat.completions.create
                if hasattr(client_self, 'chat') and hasattr(client_self.chat, 'completions'):
                    original_create = client_self.chat.completions.create
                    
                    @functools.wraps(original_create)
                    def create_wrapper(*create_args, **create_kwargs):
                        # 转换消息中的 developer 角色
                        if 'messages' in create_kwargs and create_kwargs['messages']:
                            messages = create_kwargs['messages']
                            for msg in messages:
                                if isinstance(msg, dict) and msg.get('role') == 'developer':
                                    msg['role'] = 'system'
                                    logger.info(f"✅ [GlobalPatch] 角色转换: developer -> system")
                        
                        # 处理通义千问的 response_format 限制
                        # 当使用 json_object 格式时，必须在 messages 中包含 "json" 字样
                        if 'response_format' in create_kwargs:
                            response_format = create_kwargs.get('response_format')
                            logger.info(f"🔍 [GlobalPatch] 检测到 response_format: {response_format}, 类型: {type(response_format)}")
                            
                            # 检查是否为 JSON 相关格式（json_object 或 json_schema）
                            is_json_format = False
                            format_type = None
                            if isinstance(response_format, dict):
                                format_type = response_format.get('type')
                                if format_type in ['json_object', 'json_schema']:
                                    is_json_format = True
                                    logger.info(f"🔍 [GlobalPatch] 识别为 {format_type} (dict)")
                            elif hasattr(response_format, 'type'):
                                format_type = getattr(response_format, 'type', None)
                                if format_type in ['json_object', 'json_schema']:
                                    is_json_format = True
                                    logger.info(f"🔍 [GlobalPatch] 识别为 {format_type} (object)")
                            
                            if is_json_format:
                                messages = create_kwargs.get('messages', [])
                                logger.info(f"🔍 [GlobalPatch] json_object 格式，消息数量: {len(messages)}")
                                
                                if messages:
                                    logger.info(f"🔍 [GlobalPatch] 最后一条消息角色: {messages[-1].get('role') if isinstance(messages[-1], dict) else 'unknown'}")
                                
                                # 检查是否已经包含 "json" 字样（不区分大小写）
                                has_json_keyword = False
                                for i, msg in enumerate(messages):
                                    if isinstance(msg, dict):
                                        content = str(msg.get('content', '')).lower()
                                        if 'json' in content:
                                            has_json_keyword = True
                                            logger.info(f"🔍 [GlobalPatch] 在消息 {i} 中发现 JSON 关键字")
                                            break
                                
                                logger.info(f"🔍 [GlobalPatch] 是否已包含 JSON 关键字: {has_json_keyword}")
                                
                                # 如果没有，在最后一条消息中添加提示
                                if not has_json_keyword and messages:
                                    last_msg = messages[-1]
                                    last_role = last_msg.get('role') if isinstance(last_msg, dict) else None
                                    logger.info(f"🔍 [GlobalPatch] 准备修改最后一条消息，角色: {last_role}")
                                    
                                    if isinstance(last_msg, dict):
                                        original_content = last_msg.get('content', '')
                                        last_msg['content'] = f"{original_content}\n\nPlease respond in JSON format."
                                        logger.info(f"✅ [GlobalPatch] 为 json_object 响应格式添加 JSON 关键字提示 (角色: {last_role})")
                                    else:
                                        logger.warning(f"[GlobalPatch] 最后一条消息不是字典: {type(last_msg)}")
                        
                        return original_create(*create_args, **create_kwargs)
                    
                    client_self.chat.completions.create = create_wrapper
            
            # 替换 __init__
            OpenAI.__init__ = wrapped_init
            _GLOBAL_PATCHED = True
            logger.info("✅ [CompatModel] 全局 monkey patch 完成")
            
        except Exception as e:
            logger.error(f"❌ [CompatModel] 全局 monkey patch 失败: {e}")
    
    def get_client(self):
        """
        获取 client（已经被全局 patch 处理过了）
        """
        return super().get_client()
    
    def _transform_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换消息列表，处理不兼容的角色
        
        Args:
            messages: 原始消息列表
            
        Returns:
            转换后的消息列表
        """
        if not messages:
            return messages
        
        import logging
        logger = logging.getLogger(__name__)
        
        # 记录原始消息的角色
        original_roles = [msg.get("role") if isinstance(msg, dict) else "?" for msg in messages[:3]]
        logger.info(f"🔄 [CompatModel] 开始转换消息，前3个角色: {original_roles}")
        
        transformed = []
        
        for msg in messages:
            if not isinstance(msg, dict):
                transformed.append(msg)
                continue
            
            # 复制消息以避免修改原始数据
            new_msg = dict(msg)
            
            # 应用角色映射
            if "role" in new_msg and new_msg["role"] in self.role_mapping:
                old_role = new_msg["role"]
                new_msg["role"] = self.role_mapping[old_role]
                logger.info(f"✅ [CompatModel] 角色转换: {old_role} -> {new_msg['role']}")
            
            transformed.append(new_msg)
        
        # 合并连续的 system 消息（某些 API 不允许多个连续的 system 消息）
        transformed = self._merge_system_messages(transformed)
        
        # 记录转换后的角色
        final_roles = [msg.get("role") if isinstance(msg, dict) else "?" for msg in transformed[:3]]
        logger.info(f"✅ [CompatModel] 转换完成，前3个角色: {final_roles}")
        
        return transformed
    
    def _merge_system_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并连续的 system 消息
        
        Args:
            messages: 消息列表
            
        Returns:
            合并后的消息列表
        """
        if not messages:
            return messages
        
        merged = []
        system_buffer = []
        
        for msg in messages:
            if not isinstance(msg, dict):
                if system_buffer:
                    merged.append(self._create_merged_system_message(system_buffer))
                    system_buffer = []
                merged.append(msg)
                continue
            
            if msg.get("role") == "system":
                system_buffer.append(msg)
            else:
                if system_buffer:
                    merged.append(self._create_merged_system_message(system_buffer))
                    system_buffer = []
                merged.append(msg)
        
        # 处理末尾的 system 消息
        if system_buffer:
            merged.append(self._create_merged_system_message(system_buffer))
        
        return merged
    
    def _create_merged_system_message(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将多个 system 消息合并为一个
        
        Args:
            messages: system 消息列表
            
        Returns:
            合并后的单个 system 消息
        """
        if len(messages) == 1:
            return messages[0]
        
        # 合并所有 system 消息的内容
        contents = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                contents.append(content)
        
        merged_content = "\n\n".join(contents)
        
        return {
            "role": "system",
            "content": merged_content
        }


def create_qwen_model(model_id: str = "qwen-plus", api_key: Optional[str] = None) -> CompatibleOpenAIChat:
    """
    创建兼容的 Qwen 模型实例
    
    Args:
        model_id: 模型 ID，例如 "qwen-plus", "qwen-turbo", "qwen-max"
        api_key: DashScope API Key，如果不提供则从环境变量读取
        
    Returns:
        兼容的 OpenAI Chat 模型实例
    """
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is required for Qwen models")
    
    model = CompatibleOpenAIChat(
        id=model_id,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        role_mapping={"developer": "system"},  # Qwen 不支持 developer 角色
    )
    
    # 确保在当前进程中应用全局 patch（因为可能是新进程）
    model._apply_global_patch()
    
    return model


def create_deepseek_model(model_id: str = "deepseek-chat", api_key: Optional[str] = None) -> CompatibleOpenAIChat:
    """
    创建兼容的 DeepSeek 模型实例
    
    Args:
        model_id: 模型 ID，例如 "deepseek-chat", "deepseek-coder"
        api_key: DeepSeek API Key，如果不提供则从环境变量读取
        
    Returns:
        兼容的 OpenAI Chat 模型实例
    """
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek models")
    
    return CompatibleOpenAIChat(
        id=model_id,
        api_key=api_key,
        base_url="https://api.deepseek.com",
        role_mapping={"developer": "system"},  # DeepSeek 不支持 developer 角色
    )

