import asyncio

# ⚠️ 重要：在导入任何其他模块之前先应用 Qwen/DeepSeek 兼容层
# 这确保所有 OpenAI client 实例都会自动转换 developer 角色
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# 必须先导入 OpenAI，确保类已经加载，然后才能 patch
import openai  # noqa
from valuecell.utils.compat_model import CompatibleOpenAIChat
# 立即应用全局 patch（在任何 Agent 初始化之前）
_temp_model = CompatibleOpenAIChat(
    id="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY", "dummy"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
_temp_model._apply_global_patch()
print(f"✅ [ResearchAgent] 全局 patch 已应用")
del _temp_model  # 清理临时对象

from valuecell.core.agent.decorator import create_wrapped_agent

from .core import ResearchAgent

if __name__ == "__main__":
    agent = create_wrapped_agent(ResearchAgent)
    asyncio.run(agent.serve())
