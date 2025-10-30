#!/usr/bin/env python3
"""测试 developer 角色修复"""

import requests
import time
import uuid

def test_research_agent():
    """测试 ResearchAgent 是否还有 developer 错误"""
    
    print("=" * 60)
    print("测试 ResearchAgent developer 角色修复")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    conversation_id = f"conv-{uuid.uuid4().hex}"
    
    print(f"\n发送测试查询到 ResearchAgent...")
    print(f"  会话 ID: {conversation_id}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/agents/stream",
            json={
                "query": "你好",
                "conversation_id": conversation_id,
                "agent_name": "ResearchAgent"
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            print(f"✓ 请求成功 (HTTP 200)")
            
            # 读取响应
            count = 0
            has_error = False
            for line in response.iter_lines():
                if line:
                    count += 1
                    line_str = line.decode('utf-8')
                    if 'error' in line_str.lower() or 'failed' in line_str.lower():
                        has_error = True
                        print(f"  ⚠ 发现错误: {line_str[:100]}...")
            
            if not has_error:
                print(f"✓ 收到 {count} 行响应，没有错误")
        else:
            print(f"✗ 请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return False
    
    # 等待处理完成
    print(f"\n等待 5 秒，检查日志...")
    time.sleep(5)
    
    # 检查 ResearchAgent 日志
    import subprocess
    
    try:
        result = subprocess.run(
            ["tail", "-100", "/tmp/valuecell/research_agent.log"],
            capture_output=True,
            text=True
        )
        
        log_content = result.stdout
        
        # 查找 developer 错误
        developer_errors = []
        for line in log_content.split('\n'):
            if 'developer is not one of' in line:
                developer_errors.append(line)
        
        print(f"\n分析结果:")
        print(f"  找到 developer 角色错误: {len(developer_errors)} 个")
        
        if developer_errors:
            print(f"\n❌ 仍然存在 developer 角色错误:")
            for err in developer_errors[-2:]:
                print(f"     {err[:120]}")
            return False
        else:
            print(f"\n✅ 没有发现 developer 角色错误！")
            
        # 检查是否有其他错误
        error_lines = [line for line in log_content.split('\n') if 'ERROR' in line]
        if error_lines:
            print(f"\n⚠️  发现其他错误 ({len(error_lines)} 个):")
            for err in error_lines[-3:]:
                print(f"     {err[:120]}")
    
    except Exception as e:
        print(f"⚠ 无法分析日志: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    import sys
    success = test_research_agent()
    sys.exit(0 if success else 1)

