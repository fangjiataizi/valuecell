#!/bin/bash

# ValueCell 项目重启脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/tmp/valuecell"

info()  { echo "[INFO]  $*"; }
success(){ echo "[ OK ]  $*"; }
warn()  { echo "[WARN]  $*"; }
error() { echo "[ERR ]  $*" >&2; }

# 停止所有服务
stop_services() {
  info "正在停止所有服务..."
  
  pkill -9 -f "valuecell" 2>/dev/null || true
  pkill -9 -f "bun run dev" 2>/dev/null || true
  pkill -9 -f "react-router" 2>/dev/null || true
  pkill -9 -f "uv run" 2>/dev/null || true
  
  for port in 1420 8001 10002 10003 10004; do
    if lsof -ti:$port >/dev/null 2>&1; then
      lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
  done
  
  sleep 2
  success "所有服务已停止"
}

# 启动服务
start_services() {
  info "正在启动服务..."
  
  # 创建日志目录
  mkdir -p "$LOG_DIR"
  
  # 设置环境变量
  export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
  export API_PORT=8001
  
  # 设置代理
  if netstat -tlnp 2>/dev/null | grep -q ":7890" || ss -tlnp 2>/dev/null | grep -q ":7890"; then
    info "检测到代理，启用..."
    export http_proxy=http://127.0.0.1:7890
    export https_proxy=http://127.0.0.1:7890
    export HTTP_PROXY=http://127.0.0.1:7890
    export HTTPS_PROXY=http://127.0.0.1:7890
  fi
  
  # 检查 .env
  if [ ! -f "$SCRIPT_DIR/.env" ]; then
    error ".env 文件不存在！"
    return 1
  fi
  
  # 启动前端
  info "启动前端..."
  cd "$SCRIPT_DIR/frontend"
  nohup bun run dev > "$LOG_DIR/frontend.log" 2>&1 &
  sleep 2
  
  # 启动后端
  info "启动后端..."
  cd "$SCRIPT_DIR/python"
  nohup uv run --env-file "$SCRIPT_DIR/.env" -m valuecell.server.main > "$LOG_DIR/backend.log" 2>&1 &
  sleep 2
  
  # 启动 ResearchAgent
  info "启动 ResearchAgent..."
  nohup uv run --env-file "$SCRIPT_DIR/.env" -m valuecell.agents.research_agent > "$LOG_DIR/research_agent.log" 2>&1 &
  sleep 2
  
  # 启动 AutoTradingAgent
  info "启动 AutoTradingAgent..."
  nohup uv run --env-file "$SCRIPT_DIR/.env" -m valuecell.agents.auto_trading_agent > "$LOG_DIR/autotrading.log" 2>&1 &
  sleep 2
  
  success "服务启动命令已执行"
  info "等待服务启动（约10秒）..."
  sleep 10
}

# 显示状态
show_status() {
  echo ""
  echo "=========================================="
  info "服务状态"
  echo "=========================================="
  
  if pgrep -f "bun run dev" > /dev/null; then
    success "前端: 运行中"
  else
    warn "前端: 未运行"
  fi
  
  if pgrep -f "valuecell.server.main" > /dev/null; then
    success "后端: 运行中"
  else
    warn "后端: 未运行"
  fi
  
  if pgrep -f "research_agent" > /dev/null; then
    success "ResearchAgent: 运行中 (端口 10004)"
  else
    warn "ResearchAgent: 未运行"
  fi
  
  if pgrep -f "auto_trading_agent" > /dev/null; then
    success "AutoTradingAgent: 运行中 (端口 10003)"
  else
    warn "AutoTradingAgent: 未运行"
  fi
  
  echo ""
  echo "=========================================="
  info "访问地址"
  echo "=========================================="
  
  SERVER_IP=$(hostname -I | awk '{print $1}')
  echo "  前端: http://$SERVER_IP:1420/"
  echo "  后端: http://$SERVER_IP:8001/api/v1"
  echo ""
  info "查看日志"
  echo "  tail -f $LOG_DIR/backend.log"
  echo "  tail -f $LOG_DIR/frontend.log"
  echo "  tail -f $LOG_DIR/autotrading.log"
  echo "=========================================="
  echo ""
}

# 主函数
case "${1:-restart}" in
  restart)
    stop_services
    start_services
    show_status
    ;;
  stop)
    stop_services
    show_status
    ;;
  start)
    start_services
    show_status
    ;;
  status)
    show_status
    ;;
  *)
    echo "用法: $0 {restart|stop|start|status}"
    exit 1
    ;;
esac
