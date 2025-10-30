import os

from agno.models.google import Gemini
from agno.models.openrouter import OpenRouter

from .compat_model import create_deepseek_model, create_qwen_model


def get_model(env_key: str):
    """
    获取 LLM 模型，支持多种提供商：
    - Qwen (DashScope)：设置 DASHSCOPE_API_KEY ✅ 已支持
    - DeepSeek：设置 DEEPSEEK_API_KEY ✅ 已支持  
    - Google Gemini：设置 GOOGLE_API_KEY
    - OpenRouter：设置 OPENROUTER_API_KEY（默认）
    
    优先级：Qwen > DeepSeek > Google > OpenRouter
    """
    model_id = os.getenv(env_key)
    
    # 1. 尝试使用 Qwen (DashScope)
    if os.getenv("DASHSCOPE_API_KEY"):
        # 使用兼容层支持 Qwen
        qwen_model_id = model_id if model_id and "qwen" in model_id.lower() else "qwen-plus"
        return create_qwen_model(
            model_id=qwen_model_id,
            api_key=os.getenv("DASHSCOPE_API_KEY")
        )
    
    # 2. 尝试使用 DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        # 使用兼容层支持 DeepSeek
        deepseek_model_id = model_id if model_id and "deepseek" in model_id.lower() else "deepseek-chat"
        return create_deepseek_model(
            model_id=deepseek_model_id,
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
    
    # 3. 尝试使用 Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        return Gemini(id=model_id or "gemini-2.0-flash-exp")
    
    # 4. 默认使用 OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    return OpenRouter(
        id=model_id or "google/gemini-2.0-flash-exp:free",
        api_key=openrouter_key,
        max_tokens=None
    )
