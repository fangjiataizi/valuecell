# Qwen API 和 Binance 虚拟交易配置指南

## 📋 目录

1. [Qwen API 配置](#1-qwen-api-配置)
2. [Binance 虚拟交易配置](#2-binance-虚拟交易配置)
3. [测试配置](#3-测试配置)
4. [常见问题](#4-常见问题)

---

## 1. Qwen API 配置

### 1.1 什么是 Qwen？

Qwen（通义千问）是阿里云提供的大语言模型服务，通过 DashScope API 访问。

**优势**：
- ✅ 中文支持优秀
- ✅ 价格相对便宜
- ✅ 响应速度快
- ✅ 支持多种模型规格

### 1.2 配置步骤

#### 步骤 1: 确认 API Key

您的 API Key：`sk-a7ec873e0a04461f8ce6c74ea815fa28`

已经配置在 `/opt/valuecell/.env` 文件中：
```bash
DASHSCOPE_API_KEY=sk-a7ec873e0a04461f8ce6c74ea815fa28
```

#### 步骤 2: 选择模型

ValueCell 支持以下 Qwen 模型：

| 模型 | 用途 | 特点 |
|------|------|------|
| `qwen-turbo` | 快速响应任务 | 速度快、成本低 |
| `qwen-plus` | 通用任务（推荐）| 性能均衡 |
| `qwen-max` | 复杂任务 | 最强性能 |
| `qwen-long` | 长文本处理 | 支持超长上下文 |

**当前配置**：
```bash
RESEARCH_AGENT_MODEL_ID=qwen-plus      # 研究 Agent
PLANNER_MODEL_ID=qwen-plus             # 规划器
TRADING_PARSER_MODEL_ID=qwen-turbo     # 交易解析器
```

#### 步骤 3: 代码适配说明

已修改 `python/valuecell/utils/model.py`，支持 DashScope：

```python
def get_model(env_key: str):
    # 优先使用 DashScope (Qwen)
    if os.getenv("DASHSCOPE_API_KEY"):
        return OpenAI(
            id=model_id or "qwen-plus",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    # ... 其他提供商
```

**关键点**：
- 使用 OpenAI 兼容接口
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- API Key 从环境变量读取

### 1.3 验证配置

启动服务后，检查日志：

```bash
# 启动服务
cd /opt/valuecell
./restart.sh restart

# 查看日志（等待几秒后）
tail -f /tmp/valuecell_startup.log
```

成功的标志：
- ✅ Agent 成功启动
- ✅ 没有 API key 错误
- ✅ 可以正常对话

---

## 2. Binance 虚拟交易配置

### 2.1 什么是虚拟交易？

**虚拟交易（Paper Trading）**：
- ✅ 不使用真实资金
- ✅ 模拟真实市场价格
- ✅ 完整的交易逻辑
- ✅ 用于策略测试和学习

### 2.2 配置步骤

#### 步骤 1: 设置交易模式

在 `.env` 文件中设置：
```bash
TRADING_MODE=paper
```

**说明**：
- `paper`: 模拟交易（默认）
- `live`: 真实交易（需要 Binance API Key）

#### 步骤 2: 虚拟交易实现

ValueCell 使用 `PaperTrading` 类进行模拟：

**位置**: `python/valuecell/agents/auto_trading_agent/exchanges/paper_trading.py`

**特点**：
1. **真实价格**：从 Yahoo Finance 获取实时价格
2. **账户模拟**：模拟余额和持仓
3. **无手续费**：方便测试
4. **完整功能**：支持买卖、持仓管理等

### 2.3 使用虚拟交易

#### 方式 1: 通过前端界面

1. 访问前端：`http://your-server-ip:1420/`
2. 选择 `AutoTradingAgent`
3. 输入交易指令，例如：

```
开始交易比特币和以太坊，初始资金10万美元
```

或更详细的：

```
用 10 万美元交易 BTC, ETH, SOL，使用 AI 信号
```

#### 方式 2: 通过 API

```bash
curl -X POST http://localhost:8001/api/v1/agents/AutoTradingAgent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "用 10 万美元交易 BTC-USD 和 ETH-USD，启用 AI 信号"
  }'
```

### 2.4 交易参数说明

AutoTradingAgent 支持的参数：

```python
{
    "initial_capital": 100000,        # 初始资金（美元）
    "crypto_symbols": [               # 交易标的
        "BTC-USD",                   # 比特币
        "ETH-USD",                   # 以太坊
        "SOL-USD"                    # Solana
    ],
    "check_interval": 60,            # 检查间隔（秒）
    "risk_per_trade": 0.02,          # 每笔交易风险（2%）
    "max_positions": 3,              # 最大持仓数
    "use_ai_signals": true,          # 是否使用 AI 信号
    "agent_model": "qwen-plus"       # AI 模型
}
```

### 2.5 查看交易结果

#### 实时监控

交易日志位置：
```bash
ls -lt /opt/valuecell/logs/ | head -5
tail -f /opt/valuecell/logs/[最新时间戳]/AutoTradingAgent.log
```

#### 前端界面

前端会实时显示：
- 📊 技术指标分析
- 💹 交易信号
- 💰 当前持仓
- 📈 盈亏情况
- 📋 交易历史

---

## 3. 测试配置

### 3.1 快速测试

#### 测试 1: 验证 Qwen API

```bash
cd /opt/valuecell/python

# 测试 ResearchAgent（使用 Qwen）
uv run -m valuecell.agents.research_agent
```

然后访问前端并与 ResearchAgent 对话：
```
帮我分析特斯拉的股票
```

#### 测试 2: 验证虚拟交易

```bash
# 启动 AutoTradingAgent
cd /opt/valuecell
./restart.sh restart
```

访问前端并输入：
```
用 1000 美元买入比特币进行测试
```

### 3.2 检查点

✅ **Qwen API 工作正常**：
- Agent 能正常响应
- 回复质量好
- 没有 API 错误

✅ **虚拟交易工作正常**：
- 能获取实时价格
- 能执行买卖操作
- 能查看持仓和余额

---

## 4. 常见问题

### 4.1 Qwen API 相关

**Q: 提示 API Key 无效？**

A: 检查：
1. API Key 是否正确复制
2. API Key 是否有余额
3. 重启服务：`./restart.sh restart`

**Q: 如何查看 API 使用情况？**

A: 访问阿里云 DashScope 控制台：
https://dashscope.console.aliyun.com/

**Q: 如何切换模型？**

A: 修改 `.env` 文件中的模型 ID：
```bash
RESEARCH_AGENT_MODEL_ID=qwen-max  # 改为 qwen-max
```

然后重启服务。

### 4.2 虚拟交易相关

**Q: 虚拟交易的价格是真实的吗？**

A: 是的，使用 Yahoo Finance 实时价格。

**Q: 如何重置虚拟交易账户？**

A: 停止 Agent 并重新启动：
```bash
./restart.sh restart
```

**Q: 虚拟交易支持哪些币种？**

A: 支持所有在 Yahoo Finance 上的加密货币，格式为 `{SYMBOL}-USD`：
- `BTC-USD` (比特币)
- `ETH-USD` (以太坊)
- `SOL-USD` (Solana)
- `DOGE-USD` (狗狗币)
- `ADA-USD` (Cardano)
- 等等...

**Q: 如何切换到真实交易？**

A: **注意：真实交易涉及真金白银，请谨慎！**

步骤：
1. 在 Binance 创建 API Key
2. 在 `.env` 中配置：
   ```bash
   TRADING_MODE=live
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   BINANCE_TESTNET=true  # 先用测试网
   ```
3. **实现 BinanceExchange** （目前为 TODO）
4. 重启服务

**注意**：当前 `BinanceExchange` 类只是框架，需要实现真实 API 调用。

### 4.3 性能优化

**Q: 如何提高响应速度？**

A: 
1. 使用 `qwen-turbo` 模型（更快）
2. 增加 `check_interval` 减少检查频率
3. 减少 `max_positions` 降低计算量

**Q: 如何节省 API 成本？**

A: 
1. 使用 `qwen-turbo`（更便宜）
2. 关闭 AI 信号：`use_ai_signals: false`
3. 增加检查间隔

---

## 5. 示例配置

### 5.1 保守策略

```bash
# .env
TRADING_PARSER_MODEL_ID=qwen-turbo
```

交易指令：
```
用 5000 美元交易 BTC-USD，风险 1%，不使用 AI 信号
```

### 5.2 激进策略

```bash
# .env
TRADING_PARSER_MODEL_ID=qwen-max
```

交易指令：
```
用 10 万美元交易 BTC, ETH, SOL, DOGE, ADA，
风险 5%，使用 qwen-max 模型的 AI 信号，
每 30 秒检查一次
```

### 5.3 学习测试

```bash
# .env
TRADING_MODE=paper
TRADING_PARSER_MODEL_ID=qwen-turbo
```

交易指令：
```
用 1000 美元测试交易 BTC-USD，
每 5 分钟检查一次，使用 AI 信号
```

---

## 6. 进阶配置

### 6.1 自定义风险参数

编辑交易请求：
```python
{
    "initial_capital": 100000,
    "crypto_symbols": ["BTC-USD", "ETH-USD"],
    "risk_per_trade": 0.05,      # 5% 风险
    "max_positions": 5,           # 最多 5 个持仓
    "check_interval": 300,        # 5 分钟检查一次
    "use_ai_signals": true,
    "agent_model": "qwen-max"
}
```

### 6.2 监控脚本

创建监控脚本 `monitor.sh`：
```bash
#!/bin/bash
while true; do
    clear
    echo "=== AutoTradingAgent 状态 ==="
    tail -50 /opt/valuecell/logs/$(ls -t /opt/valuecell/logs/ | head -1)/AutoTradingAgent.log
    sleep 10
done
```

运行：
```bash
chmod +x monitor.sh
./monitor.sh
```

---

## 📞 获取帮助

- **文档**: `/opt/valuecell/docs/`
- **日志**: `/opt/valuecell/logs/`
- **GitHub**: https://github.com/ValueCell-ai/valuecell

---

**最后更新**: 2025-10-29  
**版本**: v1.0
