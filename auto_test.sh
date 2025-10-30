#!/bin/bash
set -e

echo "=========================================="
echo "🔄 重启服务并自动测试"
echo "=========================================="

# 1. 重启所有服务
echo ""
echo "📌 步骤1: 重启所有服务..."
cd /opt/valuecell
bash restart.sh restart > /dev/null 2>&1

# 2. 等待服务启动
echo "⏳ 等待服务启动（30秒）..."
sleep 30

# 3. 检查服务状态
echo ""
echo "📌 步骤2: 检查服务状态..."
if ! pgrep -f "research_agent" > /dev/null; then
    echo "❌ ResearchAgent 未运行！"
    exit 1
fi
echo "✅ ResearchAgent 运行中"

if ! pgrep -f "valuecell.server.main" > /dev/null; then
    echo "❌ Backend 未运行！"
    exit 1
fi
echo "✅ Backend 运行中"

# 4. 发送测试请求
echo ""
echo "📌 步骤3: 发送测试请求到 ResearchAgent..."
curl -s -X POST http://localhost:8001/api/v1/agents/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "测试", "conversation_id": "test-auto", "agent_name": "ResearchAgent"}' \
  --max-time 5 > /dev/null 2>&1 &

# 5. 等待处理
echo "⏳ 等待处理（10秒）..."
sleep 10

# 6. 分析日志
echo ""
echo "=========================================="
echo "📊 日志分析结果"
echo "=========================================="

# 统计 developer 错误
RESEARCH_ERRORS=$(grep -c "developer is not one of" /tmp/valuecell/research_agent.log 2>/dev/null || echo "0")
BACKEND_ERRORS=$(grep -c "developer is not one of" /tmp/valuecell/backend.log 2>/dev/null || echo "0")

echo ""
echo "🔍 developer 角色错误统计:"
echo "   - ResearchAgent: $RESEARCH_ERRORS"
echo "   - Backend: $BACKEND_ERRORS"

# 检查 GlobalPatch 日志
if grep -q "GlobalPatch.*角色转换" /tmp/valuecell/research_agent.log 2>/dev/null; then
    echo "✅ ResearchAgent 角色转换日志存在"
    grep "GlobalPatch.*角色转换" /tmp/valuecell/research_agent.log 2>/dev/null | tail -2
else
    echo "⚠️  ResearchAgent 无角色转换日志"
fi

if grep -q "GlobalPatch.*角色转换" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "✅ Backend 角色转换日志存在"
else
    echo "⚠️  Backend 无角色转换日志"
fi

# 统计 Qwen API 成功调用
QWEN_SUCCESS=$(grep -c "dashscope.aliyuncs.com.*200 OK" /tmp/valuecell/research_agent.log /tmp/valuecell/backend.log 2>/dev/null || echo "0")
echo ""
echo "📈 Qwen API 成功调用: $QWEN_SUCCESS 次"

# 最终判断
echo ""
echo "=========================================="
if [ "$RESEARCH_ERRORS" -eq 0 ] && [ "$BACKEND_ERRORS" -eq 0 ]; then
    echo "🎉 测试通过！无 developer 角色错误"
    echo "=========================================="
    exit 0
else
    echo "❌ 测试失败！仍有 developer 角色错误"
    echo "=========================================="
    echo ""
    echo "最近的错误日志:"
    grep -A3 "developer is not one of" /tmp/valuecell/research_agent.log 2>/dev/null | tail -10
    exit 1
fi

