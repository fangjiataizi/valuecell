# ValueCell 重启脚本使用说明

## 🚀 快速开始

### 基本使用

```bash
# 重启所有服务（默认操作）
./restart.sh

# 或者明确指定 restart
./restart.sh restart
```

### 其他命令

```bash
# 仅停止服务
./restart.sh stop

# 仅启动服务
./restart.sh start

# 查看服务状态
./restart.sh status

# 显示帮助信息
./restart.sh --help
```

## 📋 功能说明

### 1. 自动停止服务
- 停止所有 `start.sh` 相关进程
- 停止前端服务 (bun/react-router)
- 停止后端服务 (uv/launch.py)
- 释放占用的端口 (1420, 8000, 8080, 5000)

### 2. 自动启动服务
- 设置正确的 PATH 环境变量
- 自动检测并启用代理（如果 Clash 在运行）
- 后台启动所有服务
- 记录启动日志到 `/tmp/valuecell_startup.log`

### 3. 显示服务状态
- 前端运行状态 (端口 1420)
- 后端运行状态 (端口 8000)
- 本地和远程访问地址

## 🌐 网络访问配置

### 已配置为支持远程访问

**前端配置** (`frontend/vite.config.ts`)
```typescript
server: {
  port: 1420,
  strictPort: true,
  host: "0.0.0.0",  // ✅ 已配置为 0.0.0.0
}
```

**后端配置** (`python/valuecell/server/config/settings.py`)
```python
self.API_HOST = os.getenv("API_HOST", "0.0.0.0")  # ✅ 默认 0.0.0.0
self.API_PORT = int(os.getenv("API_PORT", "8000"))
```

### 访问地址

假设您的服务器 IP 是 `172.26.14.101`：

- **前端**: 
  - 本地: http://localhost:1420/
  - 远程: http://172.26.14.101:1420/

- **后端 API** (注意：使用 8001 端口，因为 8000 可能被其他服务占用): 
  - 本地: http://localhost:8001/
  - 远程: http://172.26.14.101:8001/
  - 本地 API 文档: http://localhost:8001/docs (开发模式)
  - 远程 API 文档: http://172.26.14.101:8001/docs

## 📝 日志查看

### 启动日志
```bash
tail -f /tmp/valuecell_startup.log
```

### Agent 日志
```bash
# 查看最新的日志目录
ls -lt /opt/valuecell/logs/ | head -5

# 查看特定 agent 的日志
tail -f /opt/valuecell/logs/[timestamp]/ResearchAgent.log
tail -f /opt/valuecell/logs/[timestamp]/AutoTradingAgent.log
tail -f /opt/valuecell/logs/[timestamp]/backend.log
```

## 🔧 故障排查

### 端口被占用
```bash
# 查看端口占用情况
netstat -tlnp | grep -E ':(1420|8000)'
# 或
ss -tlnp | grep -E ':(1420|8000)'

# 手动释放端口
lsof -ti:1420 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### 服务未启动
```bash
# 检查进程
ps aux | grep -E "(bun run dev|scripts/launch.py)"

# 查看启动日志
cat /tmp/valuecell_startup.log
```

### 代理问题
如果您使用 Clash 代理：
```bash
# 检查 Clash 是否运行
netstat -tlnp | grep 7890

# 脚本会自动检测并启用代理
```

## ⚡ 快捷命令

### 创建别名（可选）
在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
alias vc-restart="cd /opt/valuecell && ./restart.sh restart"
alias vc-stop="cd /opt/valuecell && ./restart.sh stop"
alias vc-start="cd /opt/valuecell && ./restart.sh start"
alias vc-status="cd /opt/valuecell && ./restart.sh status"
alias vc-log="tail -f /tmp/valuecell_startup.log"
```

然后运行 `source ~/.bashrc` 使其生效。

之后您可以在任何目录运行：
```bash
vc-restart  # 重启
vc-status   # 查看状态
vc-log      # 查看日志
```

## 📦 与 start.sh 的区别

| 特性 | start.sh | restart.sh |
|-----|----------|------------|
| 依赖安装 | ✅ 自动安装 bun/uv | ❌ 需要已安装 |
| 前台/后台 | 前台运行（阻塞终端） | 后台运行 |
| 停止功能 | ❌ 需手动停止 | ✅ 内置停止功能 |
| 状态查看 | ❌ | ✅ |
| 快速重启 | ❌ | ✅ |
| 适用场景 | 首次启动/完整安装 | 日常开发/测试 |

## 🎯 使用建议

1. **首次启动**: 使用 `./start.sh` 进行完整的环境配置
2. **日常开发**: 使用 `./restart.sh` 快速重启
3. **测试修改**: 修改代码后运行 `./restart.sh restart`
4. **查看状态**: 随时运行 `./restart.sh status`

## 🔒 防火墙配置（如果需要）

如果无法从外部访问，可能需要开放端口：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 1420
sudo ufw allow 8000

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=1420/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# 阿里云/腾讯云
# 需要在控制台的安全组规则中开放 1420 和 8000 端口
```

## 🔧 CORS 跨域问题解决

如果从远程 IP 访问时看到 CORS 错误，项目已经做了以下配置：

### 1. 前端自动适配 API 地址
修改了 `frontend/src/lib/api-client.ts`，前端会自动使用当前访问的主机名来连接后端：
- 从 `http://localhost:1420` 访问 → API: `http://localhost:8000`
- 从 `http://172.26.14.101:1420` 访问 → API: `http://172.26.14.101:8000`

### 2. 后端 CORS 配置
后端默认允许所有来源的跨域请求（`CORS_ORIGINS="*"`），可以通过环境变量自定义：

```bash
# 在 .env 文件中设置
CORS_ORIGINS=http://localhost:1420,http://172.26.14.101:1420
```

### 3. 重启生效
修改配置后需要重启服务：
```bash
./restart.sh restart
```

## ⚠️ 注意事项

1. 脚本需要执行权限：`chmod +x restart.sh`
2. 确保已经运行过一次 `start.sh` 完成环境配置
3. 服务在后台运行，退出终端不会停止服务
4. 使用 `./restart.sh stop` 可以完全停止所有服务
5. 修改前端代码后需要重启前端服务才能生效

