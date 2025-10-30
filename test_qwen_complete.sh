#!/bin/bash
set -e

echo "============================================"
echo "🧪 Qwen 兼容层完整测试脚本"
echo "============================================"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（40秒）..."
sleep 40

echo ""
echo "============================================"
echo "✅ 第1步：检查服务状态"
echo "============================================"

# 检查进程
if ! pgrep -f "valuecell.server.main" > /dev/null; then
    echo "❌ 后端未运行"
    exit 1
fi
echo "✅ 后端运行中"

if ! pgrep -f "research_agent" > /dev/null; then
    echo "❌ ResearchAgent 未运行"
    exit 1
fi
echo "✅ ResearchAgent 运行中"

# 检查端口
for port in 8001 10004; do
    if ! lsof -ti:$port > /dev/null 2>&1; then
        echo "❌ 端口 $port 未监听"
        exit 1
    fi
    echo "✅ 端口 $port 监听中"
done

echo ""
echo "============================================"
echo "📤 第2步：测试 ResearchAgent"
echo "============================================"

# 发送测试请求
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/agents/stream \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"你好\", \"conversation_id\": \"test-$(date +%s)\", \"agent_name\": \"ResearchAgent\"}" \
  --max-time 30 2>&1 | head -5)

echo "收到响应: ${RESPONSE:0:100}..."

# 等待处理
sleep 8

echo ""
echo "============================================"
echo "📋 第3步：分析后端日志"
echo "============================================"

# 检查是否有 developer 角色错误
if grep -q "developer is not one of" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "❌ 后端仍有 developer 角色错误！"
    echo ""
    echo "错误详情:"
    grep -A5 "developer is not one of" /tmp/valuecell/backend.log | tail -10
    exit 1
fi
echo "✅ 后端无 developer 角色错误"

# 检查 ResearchAgent 日志
if grep -q "developer is not one of" /tmp/valuecell/research_agent.log 2>/dev/null; then
    echo "❌ ResearchAgent 仍有 developer 角色错误！"
    echo ""
    echo "错误详情:"
    grep -A5 "developer is not one of" /tmp/valuecell/research_agent.log | tail -10
    exit 1
fi
echo "✅ ResearchAgent 无 developer 角色错误"

# 检查是否有成功的 Qwen API 调用
if ! grep -q "dashscope.aliyuncs.com.*200 OK" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "⚠️  警告: 未发现成功的 Qwen API 调用"
else
    echo "✅ Qwen API 调用成功"
fi

# 检查角色转换日志
if grep -q "GlobalPatch.*角色转换: developer -> system" /tmp/valuecell/research_agent.log 2>/dev/null; then
    echo "✅ ResearchAgent 角色转换生效"
elif grep -q "CompatModel.*角色转换: developer -> system" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "✅ 后端角色转换生效"
else
    echo "⚠️  警告: 未发现角色转换日志"
fi

echo ""
echo "============================================"
echo "📊 第4步：统计分析"
echo "============================================"

# 统计成功的 API 调用
SUCCESS_COUNT=$(grep -c "dashscope.aliyuncs.com.*200 OK" /tmp/valuecell/backend.log 2>/dev/null || echo "0")
echo "✅ 成功的 Qwen API 调用: $SUCCESS_COUNT 次"

# 统计失败的 API 调用（developer 角色错误）
ERROR_COUNT=$(grep -c "developer is not one of" /tmp/valuecell/backend.log /tmp/valuecell/research_agent.log 2>/dev/null || echo "0")
echo "📊 developer 角色错误: $ERROR_COUNT 次"

# 检查任务状态
if grep -q "TaskState.completed" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "✅ 发现任务成功完成"
elif grep -q "TaskState.failed" /tmp/valuecell/backend.log 2>/dev/null; then
    echo "⚠️  发现任务失败"
    # 显示失败原因
    grep -B10 "TaskState.failed" /tmp/valuecell/backend.log | tail -5
else
    echo "ℹ️  未发现任务完成/失败记录"
fi

echo ""
echo "============================================"
echo "📝 第5步：显示关键日志"
echo "============================================"

echo ""
echo "--- 最近的后端日志（最后20行）---"
tail -20 /tmp/valuecell/backend.log | grep -E "CompatModel|GlobalPatch|你好|ERROR|200 OK" || echo "无相关日志"

echo ""
echo "--- 最近的 ResearchAgent 日志（最后20行）---"
tail -20 /tmp/valuecell/research_agent.log | grep -E "CompatModel|GlobalPatch|ERROR|200 OK" || echo "无相关日志"

echo ""
echo "============================================"
echo "🎯 测试结果汇总"
echo "============================================"

if [ "$ERROR_COUNT" -eq 0 ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo "🎉 测试通过！"
    echo "   - 所有服务正常运行"
    echo "   - Qwen API 调用成功"
    echo "   - 无 developer 角色错误"
    echo ""
    echo "✅ 可以通知用户进行最终测试了！"
    exit 0
elif [ "$ERROR_COUNT" -eq 0 ]; then
    echo "⚠️  部分通过"
    echo "   - 无 developer 角色错误"
    echo "   - 但可能需要更多测试"
    exit 0
else
    echo "❌ 测试失败"
    echo "   - 仍存在 developer 角色错误"
    echo "   - 需要继续修复"
    exit 1
fi

