#!/bin/bash
set -e

echo "🧹 第1步：彻底清理所有进程和端口"
pkill -9 -f "valuecell" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "bun run dev" 2>/dev/null || true
sleep 2

for port in 8001 1420 10002 10003; do
  fuser -k ${port}/tcp 2>/dev/null || true
  lsof -ti:${port} 2>/dev/null | xargs -r kill -9 2>/dev/null || true
done
sleep 2

echo "✅ 清理完成"

echo ""
echo "🚀 第2步：启动后端服务"
cd /opt/valuecell/python
export PATH="$HOME/.local/bin:$PATH"
export API_PORT=8001

rm -f /tmp/qwen_backend_final.log
nohup uv run --env-file /opt/valuecell/.env -m valuecell.server.main > /tmp/qwen_backend_final.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

echo "⏳ 等待后端启动（20秒）..."
sleep 20

echo ""
echo "🔍 第3步：检查服务状态"
if ps -p $BACKEND_PID > /dev/null; then
  echo "✅ 后端进程运行中 (PID: $BACKEND_PID)"
else
  echo "❌ 后端进程已退出"
  tail -30 /tmp/qwen_backend_final.log
  exit 1
fi

if lsof -ti:8001 > /dev/null 2>&1; then
  echo "✅ 端口 8001 正在监听"
else
  echo "❌ 端口 8001 未监听"
  exit 1
fi

echo ""
echo "📤 第4步：发送测试请求"
curl -X POST http://localhost:8001/api/v1/agents/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "你好", "conversation_id": "test-final", "agent_name": "ResearchAgent"}' \
  --max-time 30 --no-buffer 2>&1 | head -30 &

CURL_PID=$!
sleep 10
kill $CURL_PID 2>/dev/null || true

echo ""
echo "📋 第5步：分析日志"
echo "==================== 兼容层和请求相关日志 ===================="
grep -E "CompatModel|wrapped_create|developer|你好|ERROR" /tmp/qwen_backend_final.log | tail -20 || echo "没有找到相关日志"

echo ""
echo "==================== 最后20行日志 ===================="
tail -20 /tmp/qwen_backend_final.log

echo ""
echo "✅ 测试完成！"
echo "后端日志文件: /tmp/qwen_backend_final.log"
echo "后端 PID: $BACKEND_PID (可用 kill $BACKEND_PID 停止)"

