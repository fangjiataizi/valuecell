# AutoTradingAgent 优化计划

## 📋 问题分析

### 当前问题

1. **价格源问题**
   - ❌ 使用 Yahoo Finance，频繁遇到速率限制
   - ❌ 获取数据不稳定，影响交易决策
   - ✅ Binance API 更适合加密货币交易，数据更实时

2. **配置方式问题**
   - ❌ 通过对话解析配置，容易出错
   - ❌ 用户需要记住特定格式
   - ❌ 不够直观，体验差

3. **默认模型问题**
   - ❌ 硬编码默认模型为 `deepseek/deepseek-v3.1-terminus`
   - ❌ 用户无法灵活选择模型
   - ❌ 不符合多模型对比的需求

---

## 🎯 优化目标

### 1. 价格源优化
- ✅ 集成 Binance API 获取实时价格
- ✅ 支持备用数据源（yfinance 作为 fallback）
- ✅ 实现价格缓存和速率控制

### 2. 配置方式重构
- ✅ 创建专业配置页面
- ✅ 支持保存配置模板
- ✅ 支持快速启动和历史配置

### 3. 模型选择优化
- ✅ 移除硬编码默认模型
- ✅ 支持从可用模型列表选择
- ✅ 支持多模型同时运行对比

---

## 📐 详细实施方案

### 阶段 1: Binance API 集成 (P0 - 2-3天)

#### 1.1 创建 Binance 价格数据源

**文件**: `python/valuecell/agents/auto_trading_agent/market_data.py`

**修改点**:
- 添加 `BinanceMarketDataProvider` 类
- 实现 `get_current_price()` - 获取实时价格
- 实现 `get_klines()` - 获取K线数据（用于技术指标）
- 实现 `get_24h_ticker()` - 获取24h统计数据

**API 端点使用**:
```python
# Binance Public API (无需 API Key)
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=500
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
```

**实现要点**:
- 符号转换：`BTC-USD` → `BTCUSDT`
- 速率限制：每分钟 1200 次请求（Binance 公开 API 限制）
- 错误处理：自动降级到 yfinance（如果需要）
- 缓存策略：60秒 TTL

#### 1.2 修改 MarketDataProvider 使用 Binance

**策略**: 创建数据源选择器，优先使用 Binance，失败时降级到 yfinance

```python
class MarketDataProvider:
    def __init__(self, preferred_source: str = "binance"):
        self.preferred_source = preferred_source
        self.binance_provider = BinanceMarketDataProvider()
        self.yfinance_provider = YFinanceMarketDataProvider()  # 降级备用
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        # 优先 Binance
        try:
            return self.binance_provider.get_current_price(symbol)
        except Exception as e:
            logger.warning(f"Binance failed, using yfinance: {e}")
            return self.yfinance_provider.get_current_price(symbol)
```

#### 1.3 更新 Dashboard 实时价格 API

**文件**: `python/valuecell/server/api/routers/trading.py`

修改 `get_market_prices()` 使用 Binance API

#### 1.4 测试和验证

- ✅ 测试价格获取准确性
- ✅ 测试速率限制处理
- ✅ 测试降级机制
- ✅ 验证技术指标计算准确性

---

### 阶段 2: 配置页面开发 (P0 - 3-4天)

#### 2.1 创建配置管理 API

**新文件**: `python/valuecell/server/api/routers/trading_config.py`

**API 端点**:
```python
POST /api/v1/trading/config/create      # 创建新配置
GET  /api/v1/trading/config/list        # 获取配置列表
GET  /api/v1/trading/config/{id}        # 获取配置详情
PUT  /api/v1/trading/config/{id}         # 更新配置
DELETE /api/v1/trading/config/{id}       # 删除配置
POST /api/v1/trading/config/{id}/start   # 启动交易实例
```

**数据模型**:
```python
class TradingConfigCreate(BaseModel):
    name: str  # 配置名称
    crypto_symbols: List[str]  # 交易符号
    initial_capital: float  # 初始资金
    check_interval: int = 60  # 检查间隔（秒）
    use_ai_signals: bool = True  # 启用AI信号
    agent_models: List[str]  # AI模型列表
    risk_per_trade: float = 0.02  # 单笔风险
    max_positions: int = 3  # 最大持仓数
    
class TradingConfigResponse(TradingConfigCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    active_instances: List[str]  # 活跃实例ID
```

**存储方式**: SQLite 或 JSON 文件（简单场景）

#### 2.2 创建配置页面前端

**新文件**: `frontend/src/app/trading-config/page.tsx`

**功能模块**:

1. **配置列表视图**
   - 显示所有配置
   - 显示每个配置的活跃实例数
   - 快速启动/停止按钮
   - 配置状态（运行中/已停止）

2. **配置创建/编辑表单**
   - 配置名称输入
   - 交易符号选择器（多选）
   - 初始资金输入
   - 检查间隔设置
   - AI模型选择器（多选）
   - 风险参数设置
   - 保存按钮

3. **快速配置模板**
   - "保守策略"模板（低风险）
   - "激进策略"模板（高风险）
   - "平衡策略"模板（默认）

4. **配置详情视图**
   - 显示完整配置
   - 显示运行实例列表
   - 显示历史性能
   - 编辑/删除按钮

**UI 组件结构**:
```tsx
<TradingConfigPage>
  <ConfigList />
  <ConfigForm />
  <ConfigTemplates />
  <ActiveInstances />
</TradingConfigPage>
```

#### 2.3 修改 AutoTradingAgent 接受配置

**文件**: `python/valuecell/agents/auto_trading_agent/agent.py`

**修改点**:
- 添加 `create_instance_from_config()` 方法
- 接受配置 ID，从存储中读取配置
- 直接使用配置对象，不再需要解析自然语言

**新的启动方式**:
```python
# 旧方式（对话）
await agent.stream("用 10000 美元交易 BTC-USD，使用 deepseek")

# 新方式（配置）
POST /api/v1/trading/config/{config_id}/start
# AutoTradingAgent 直接从配置创建实例
```

#### 2.4 配置持久化

**存储方案选择**:
- **SQLite**: 适合生产环境，支持复杂查询
- **JSON 文件**: 简单场景，易于调试

**推荐**: SQLite（使用 SQLAlchemy）

**表结构**:
```sql
CREATE TABLE trading_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    crypto_symbols TEXT,  -- JSON array
    initial_capital REAL,
    check_interval INTEGER,
    use_ai_signals BOOLEAN,
    agent_models TEXT,  -- JSON array
    risk_per_trade REAL,
    max_positions INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE config_instances (
    config_id TEXT,
    instance_id TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES trading_configs(id)
);
```

---

### 阶段 3: 模型选择优化 (P1 - 1-2天)

#### 3.1 移除硬编码默认模型

**文件**: `python/valuecell/agents/auto_trading_agent/constants.py`

**修改**:
```python
# 旧
DEFAULT_AGENT_MODEL = "deepseek/deepseek-v3.1-terminus"

# 新
DEFAULT_AGENT_MODEL = None  # 必须明确指定
```

#### 3.2 创建可用模型列表 API

**新端点**: `GET /api/v1/trading/models/available`

**实现**:
```python
@router.get("/models/available")
async def get_available_models() -> List[Dict[str, Any]]:
    """
    获取可用的 AI 模型列表
    
    从环境变量和配置文件读取
    """
    models = []
    
    # 检查可用的模型
    if os.getenv("OPENAI_API_KEY"):
        models.append({
            "id": "gpt-4o",
            "name": "GPT-4o",
            "provider": "openai",
            "type": "chat"
        })
    
    if os.getenv("DASHSCOPE_API_KEY"):
        models.extend([
            {
                "id": "qwen-plus",
                "name": "Qwen Plus",
                "provider": "qwen",
                "type": "chat"
            },
            {
                "id": "qwen-max",
                "name": "Qwen Max",
                "provider": "qwen",
                "type": "chat"
            }
        ])
    
    if os.getenv("DEEPSEEK_API_KEY"):
        models.extend([
            {
                "id": "deepseek/deepseek-v3.1-terminus",
                "name": "DeepSeek V3.1 Terminus",
                "provider": "deepseek",
                "type": "chat"
            },
            {
                "id": "deepseek/deepseek-chat",
                "name": "DeepSeek Chat",
                "provider": "deepseek",
                "type": "chat"
            }
        ])
    
    return models
```

#### 3.3 配置页面模型选择器

**前端组件**:
```tsx
<ModelSelector
  availableModels={models}
  selectedModels={config.agent_models}
  onChange={setSelectedModels}
  multiple={true}
/>
```

**显示信息**:
- 模型名称
- 提供商
- 类型
- 是否可用（API Key 已配置）

#### 3.4 多模型支持增强

**功能**:
- 支持一个配置启动多个模型实例
- 每个模型独立运行
- 在 Dashboard 中可以对比不同模型的性能

---

## 🔄 迁移策略

### 现有用户迁移

1. **对话式配置保留**（向后兼容）
   - 继续支持自然语言配置
   - 但在配置页面创建新配置

2. **默认模型迁移**
   - 如果用户未指定模型，提示选择
   - 不在代码中硬编码默认值

---

## 📊 实施优先级

### 🔴 P0 - 必须（立即实施）
1. **Binance API 集成** - 解决速率限制问题
2. **配置页面开发** - 提升用户体验
3. **模型选择优化** - 移除硬编码

### 🟡 P1 - 重要（后续优化）
1. 配置模板系统
2. 配置导入/导出
3. 高级参数配置（止损、止盈等）

### 🟢 P2 - 可选（未来增强）
1. 配置版本管理
2. A/B 测试功能
3. 自动优化建议

---

## 📝 实施检查清单

### 阶段 1: Binance API
- [ ] 创建 `BinanceMarketDataProvider` 类
- [ ] 实现价格获取方法
- [ ] 实现 K线数据获取
- [ ] 实现速率限制控制
- [ ] 集成到 `MarketDataProvider`
- [ ] 更新 Dashboard API
- [ ] 测试和验证

### 阶段 2: 配置页面
- [ ] 创建配置管理 API
- [ ] 实现配置 CRUD 操作
- [ ] 创建前端配置页面
- [ ] 实现配置表单
- [ ] 实现配置模板
- [ ] 修改 AutoTradingAgent 接受配置
- [ ] 实现配置持久化（SQLite/JSON）

### 阶段 3: 模型选择
- [ ] 移除硬编码默认模型
- [ ] 创建可用模型列表 API
- [ ] 实现前端模型选择器
- [ ] 更新配置验证逻辑
- [ ] 测试多模型场景

---

## 💡 实施建议

1. **先实施阶段 1**（Binance API），立即解决速率限制问题
2. **然后实施阶段 2**（配置页面），大幅提升用户体验
3. **最后实施阶段 3**（模型选择），完善功能

4. **保持向后兼容**：对话式配置仍然可用，但推荐使用配置页面

5. **测试策略**：
   - 单元测试：每个功能模块
   - 集成测试：完整流程
   - 用户测试：获取反馈

---

## 🎯 预期效果

### 用户体验提升
- ✅ 不再需要记住配置格式
- ✅ 可视化配置界面
- ✅ 配置可保存和复用
- ✅ 快速启动交易

### 稳定性提升
- ✅ Binance API 更稳定，不会频繁限流
- ✅ 配置验证更严格，减少错误
- ✅ 模型选择更灵活

### 功能增强
- ✅ 支持多模型同时运行对比
- ✅ 支持配置模板
- ✅ 支持配置历史管理

---

## 📅 时间估算

- **阶段 1** (Binance API): 2-3 天
- **阶段 2** (配置页面): 3-4 天
- **阶段 3** (模型选择): 1-2 天

**总计**: 6-9 天

---

## 🚀 下一步行动

1. **立即开始阶段 1** - Binance API 集成
2. **准备阶段 2** - 设计配置页面 UI
3. **规划阶段 3** - 模型选择器设计

