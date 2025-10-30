"""Main entry point for auto trading agent"""

import asyncio

# ⚠️ 重要：在导入任何其他模块之前先应用 Qwen/DeepSeek 兼容层
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# 必须先导入 OpenAI，确保类已经加载，然后才能 patch
import openai  # noqa
from valuecell.utils.compat_model import CompatibleOpenAIChat
# 立即应用全局 patch
_temp_model = CompatibleOpenAIChat(
    id="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY", "dummy"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
_temp_model._apply_global_patch()
print(f"✅ [AutoTradingAgent] 全局 patch 已应用")
del _temp_model

from valuecell.core.agent.decorator import create_wrapped_agent

from .agent import AutoTradingAgent

if __name__ == "__main__":
    agent = create_wrapped_agent(AutoTradingAgent)
    asyncio.run(agent.serve())
