# 🚀 Qwen + Binance 虚拟交易快速开始

## ✅ 配置完成情况

已完成以下配置：

### 1. Qwen API 配置 ✅
- ✅ 已添加 DashScope API Key
- ✅ 已修改 `python/valuecell/utils/model.py` 支持 Qwen
- ✅ 已配置模型：
  - `qwen-plus` (研究 Agent 和规划器)
  - `qwen-turbo` (交易解析器)

### 2. 虚拟交易配置 ✅
- ✅ 交易模式设置为 `paper`（模拟交易）
- ✅ 使用 `PaperTrading` 类进行模拟
- ✅ 从 Yahoo Finance 获取实时价格

### 3. 服务状态 ✅
- ✅ 前端运行中
- ✅ 后端运行中

---

## 🎯 立即开始使用

### 方式 1: 通过前端界面（推荐）

1. **访问前端**
   ```
   http://172.26.14.101:1420/
   ```

2. **选择 AutoTradingAgent**
   - 在 Agent 市场找到 "自动交易 Agent"
   - 点击进入对话界面

3. **发送交易指令**

   **简单示例**：
   ```
   用 10000 美元交易比特币
   ```

   **详细示例**：
   ```
   用 10 万美元交易 BTC-USD 和 ETH-USD，
   启用 AI 信号，使用 qwen-plus 模型，
   每 60 秒检查一次
   ```

   **多币种示例**：
   ```
   用 50000 美元交易 BTC, ETH, SOL, DOGE，
   风险 2%，最多 4 个持仓，启用 AI 信号
   ```

4. **实时查看**
   - 📊 技术指标分析（RSI、MACD、均线等）
   - 💹 交易信号（买入/卖出/持有）
   - 💰 当前持仓和盈亏
   - 📈 投资组合价值变化
   - 🤖 AI 分析理由（如果启用）

### 方式 2: 通过 API

```bash
curl -X POST http://172.26.14.101:8001/api/v1/agents/AutoTradingAgent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "用 10000 美元交易 BTC-USD，启用 AI 信号"
  }'
```

---

## 📊 查看交易日志

### 实时监控

```bash
# 查看最新日志目录
ls -lt /opt/valuecell/logs/ | head -5

# 查看 AutoTradingAgent 日志
tail -f /opt/valuecell/logs/[最新时间戳]/AutoTradingAgent.log

# 或者查看最新日志
tail -f $(ls -t /opt/valuecell/logs/*/AutoTradingAgent.log | head -1)
```

### 日志内容示例

```
🔄 **Check #1** - 2025-10-29 11:30:00
Instance: `trading_001`
Model: `qwen-plus`
==================================================

📊 **Phase 1: Analyzing all assets...**

=== Market Analysis for BTC-USD ===
Current Price: $34,250.00
24h Change: +2.5%

Technical Indicators:
- RSI: 45.2 (Neutral)
- MACD: Bullish crossover
- SMA7: $33,800 < SMA25: $34,100 (Bearish)
- Bollinger: Middle band

Technical Signal: HOLD
AI Signal: BUY (Confidence: 75%)
AI Reasoning: MACD 看涨交叉信号强烈，价格接近中轨支撑，
             短期有上涨潜力...

📋 **Phase 2: Portfolio Decision**
Recommended Actions:
- BUY BTC-USD: 0.5 units @ $34,250
- HOLD ETH-USD

✅ Trade Executed: BUY 0.5 BTC @ $34,250
💰 Portfolio Value: $100,000 → $102,500
```

---

## 🎮 交易参数说明

### 支持的加密货币

所有 Yahoo Finance 上的加密货币，格式 `{SYMBOL}-USD`：

```
BTC-USD   # 比特币
ETH-USD   # 以太坊
SOL-USD   # Solana
DOGE-USD  # 狗狗币
ADA-USD   # Cardano
MATIC-USD # Polygon
DOT-USD   # Polkadot
AVAX-USD  # Avalanche
```

### 可配置参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `initial_capital` | 初始资金（美元） | 必填 | 10000, 100000 |
| `crypto_symbols` | 交易标的 | 必填 | BTC-USD, ETH-USD |
| `check_interval` | 检查间隔（秒） | 60 | 30, 300, 600 |
| `risk_per_trade` | 每笔风险（比例） | 0.02 | 0.01, 0.05 |
| `max_positions` | 最大持仓数 | 3 | 1, 5, 10 |
| `use_ai_signals` | 启用 AI 信号 | false | true, false |
| `agent_model` | AI 模型 | qwen-turbo | qwen-plus, qwen-max |

---

## 💡 使用技巧

### 1. 新手建议

**保守策略**：
```
用 5000 美元交易 BTC-USD，
风险 1%，不使用 AI 信号，
每 5 分钟检查一次
```

- ✅ 单一标的，风险低
- ✅ 不使用 AI，节省成本
- ✅ 检查频率低，稳定

### 2. 进阶策略

**平衡策略**：
```
用 5 万美元交易 BTC, ETH, SOL，
风险 2%，启用 AI 信号，
使用 qwen-plus 模型，每分钟检查
```

- ✅ 多元化配置
- ✅ AI 辅助决策
- ✅ 实时监控

### 3. 激进策略

**高频策略**：
```
用 10 万美元交易 BTC, ETH, SOL, DOGE, ADA，
风险 5%，最多 5 个持仓，
使用 qwen-max 模型，每 30 秒检查
```

- ⚠️ 高风险高收益
- ⚠️ 高 API 成本
- ⚠️ 需要持续监控

---

## 🔧 配置调整

### 修改模型

编辑 `/opt/valuecell/.env`：
```bash
# 使用更快的模型
TRADING_PARSER_MODEL_ID=qwen-turbo

# 使用更强的模型
TRADING_PARSER_MODEL_ID=qwen-max
```

重启服务：
```bash
cd /opt/valuecell
./restart.sh restart
```

### 停止交易

前端界面点击"停止"按钮，或：
```bash
cd /opt/valuecell
./restart.sh stop
```

---

## ❓ 常见问题

### Q: 虚拟交易的钱是真的吗？
A: **不是！** 这是模拟交易，不涉及真金白银，完全安全。

### Q: 价格是实时的吗？
A: **是的！** 从 Yahoo Finance 获取实时市场价格。

### Q: 可以切换到真实交易吗？
A: 可以，但需要：
1. Binance API Key
2. 实现 `BinanceExchange` 类（当前为 TODO）
3. 充分测试后再使用

**⚠️ 真实交易有风险，投资需谨慎！**

### Q: 如何重置账户？
A: 重启服务即可重置：
```bash
./restart.sh restart
```

### Q: AI 信号准确吗？
A: AI 信号仅供参考，不构成投资建议。请结合技术指标和自己的判断。

---

## 📚 更多文档

- **详细配置**: `/opt/valuecell/docs/QWEN_BINANCE_SETUP.md`
- **功能说明**: `/opt/valuecell/docs/DETAILED_FUNCTIONAL_SPECIFICATION.md`
- **重启指南**: `/opt/valuecell/RESTART_GUIDE.md`

---

## 🎉 开始您的交易之旅！

```bash
# 访问前端
open http://172.26.14.101:1420/

# 或查看服务状态
cd /opt/valuecell
./restart.sh status
```

**祝交易顺利！** 📈💰

---

**配置日期**: 2025-10-29  
**API**: Qwen (DashScope)  
**交易模式**: Paper Trading (虚拟)
