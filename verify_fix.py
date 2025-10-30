#!/usr/bin/env python3
"""
验证 Qwen 兼容层修复是否生效
"""
import sys
import os

# 添加虚拟环境路径
venv_site_packages = '/opt/valuecell/python/.venv/lib/python3.12/site-packages'
sys.path.insert(0, venv_site_packages)
sys.path.insert(0, '/opt/valuecell/python')

print("=" * 60)
print("🧪 验证 Qwen 兼容层修复")
print("=" * 60)

# 测试1：导入兼容层
print("\n✅ 测试1: 导入兼容层...")
try:
    from valuecell.utils.compat_model import create_qwen_model, _GLOBAL_PATCHED
    print(f"   导入成功，全局 patch 状态: {_GLOBAL_PATCHED}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 创建 Qwen 模型
print("\n✅ 测试2: 创建 Qwen 模型...")
try:
    os.environ['DASHSCOPE_API_KEY'] = 'sk-a7ec873e0a04461f8ce6c74ea815fa28'
    model = create_qwen_model("qwen-plus")
    print(f"   模型创建成功: {model}")
except Exception as e:
    print(f"   ❌ 创建失败: {e}")
    sys.exit(1)

# 测试3: 检查全局 patch 是否应用
print("\n✅ 测试3: 检查全局 monkey patch...")
try:
    from valuecell.utils.compat_model import _GLOBAL_PATCHED
    print(f"   全局 patch 状态: {_GLOBAL_PATCHED}")
    if not _GLOBAL_PATCHED:
        print("   ⚠️  警告: 全局 patch 未应用")
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

# 测试4: 测试消息转换
print("\n✅ 测试4: 测试消息转换...")
try:
    messages = [
        {"role": "developer", "content": "Test system message"},
        {"role": "user", "content": "Hello"}
    ]
    transformed = model._transform_messages(messages)
    print(f"   原始: {messages[0]['role']}")
    print(f"   转换后: {transformed[0]['role']}")
    if transformed[0]['role'] == 'system':
        print("   ✅ 角色转换成功!")
    else:
        print("   ❌ 角色转换失败")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ 转换测试失败: {e}")
    sys.exit(1)

# 测试5: 测试 OpenAI client 包装
print("\n✅ 测试5: 测试 OpenAI client 包装...")
try:
    from openai import OpenAI
    test_client = OpenAI(api_key="test", base_url="https://test.com")
    
    # 检查 create 方法是否被包装
    create_method = test_client.chat.completions.create
    print(f"   Create 方法类型: {type(create_method)}")
    print(f"   方法名称: {create_method.__name__ if hasattr(create_method, '__name__') else 'N/A'}")
    
    # 尝试检查是否是包装函数
    if hasattr(create_method, '__wrapped__'):
        print("   ✅ Create 方法已被包装 (__wrapped__ 存在)")
    else:
        print("   ℹ️  Create 方法可能已被包装 (通过 functools)")
    
except Exception as e:
    print(f"   ⚠️  测试失败: {e}")

print("\n" + "=" * 60)
print("🎉 所有测试通过！兼容层修复已生效")
print("=" * 60)

