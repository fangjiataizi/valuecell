# 🤖 LLM 支持说明

## ✅ 支持的 LLM 提供商

ValueCell 现已支持以下 LLM 提供商：

| 提供商 | 状态 | 配置方式 | 说明 |
|--------|------|----------|------|
| **Qwen (阿里云)** | ✅ 支持 | `DASHSCOPE_API_KEY` | 通过兼容层支持 |
| **DeepSeek** | ✅ 支持 | `DEEPSEEK_API_KEY` | 通过兼容层支持 |
| **Google Gemini** | ✅ 支持 | `GOOGLE_API_KEY` | 原生支持 |
| **OpenRouter** | ✅ 支持 | `OPENROUTER_API_KEY` | 原生支持，有免费模型 |

## 🔧 技术实现

### 兼容层设计

我们创建了 `CompatibleOpenAIChat` 包装器来解决 Agno 框架与某些 LLM 的兼容性问题：

**问题**：
- Agno 框架使用 `developer` 角色发送系统指令
- Qwen 和 DeepSeek 只支持 `system`、`user`、`assistant` 等标准角色

**解决方案**：
1. **消息拦截**：在发送前拦截所有消息
2. **角色转换**：将 `developer` 角色自动转换为 `system` 角色
3. **消息合并**：合并连续的 `system` 消息以符合 API 要求

### 代码位置

- **兼容层实现**：`/opt/valuecell/python/valuecell/utils/compat_model.py`
- **模型获取逻辑**：`/opt/valuecell/python/valuecell/utils/model.py`

## 📝 配置方法

### 1. 使用 Qwen（推荐）

编辑 `/opt/valuecell/.env`：

```bash
# 阿里云 DashScope API Key
DASHSCOPE_API_KEY="your_dashscope_api_key"

# 模型选择
RESEARCH_AGENT_MODEL_ID="qwen-plus"      # 或 qwen-turbo, qwen-max
PLANNER_MODEL_ID="qwen-plus"
TRADING_PARSER_MODEL_ID="qwen-turbo"
```

**可用模型**：
- `qwen-turbo`：快速响应，适合简单任务
- `qwen-plus`：平衡性能，推荐使用 ✅
- `qwen-max`：最强性能
- `qwen-long`：长文本处理

**获取 API Key**：
1. 访问 [阿里云百炼](https://dashscope.console.aliyun.com/)
2. 注册并创建应用
3. 获取 API Key

### 2. 使用 DeepSeek

编辑 `/opt/valuecell/.env`：

```bash
# DeepSeek API Key
DEEPSEEK_API_KEY="your_deepseek_api_key"

# 模型选择
RESEARCH_AGENT_MODEL_ID="deepseek-chat"    # 或 deepseek-coder
PLANNER_MODEL_ID="deepseek-chat"
TRADING_PARSER_MODEL_ID="deepseek-chat"
```

**可用模型**：
- `deepseek-chat`：通用对话模型
- `deepseek-coder`：代码专用模型

**获取 API Key**：
1. 访问 [DeepSeek](https://platform.deepseek.com/)
2. 注册并创建 API Key

### 3. 使用 Google Gemini

```bash
GOOGLE_API_KEY="your_google_api_key"
```

### 4. 使用 OpenRouter（免费）

```bash
# 可选，留空使用免费模型
OPENROUTER_API_KEY="your_openrouter_api_key"
```

## 🚀 启动服务

配置完成后，重启服务：

```bash
cd /opt/valuecell
bash restart.sh restart
```

等待约 20 秒，服务启动完成。

## 🧪 测试

1. 访问前端：http://your-ip:1420/
2. 选择任意 Agent（如 AutoTradingAgent）
3. 发送测试消息：
   ```
   你好
   ```
   或
   ```
   分析一下比特币的价格趋势
   ```

4. 检查后端日志：
   ```bash
   tail -50 /tmp/valuecell/backend.log
   ```

### 成功标志

✅ **正常运行**：
- 没有 `developer is not one of` 错误
- SSE 连接保持稳定
- Agent 能正常回复消息

❌ **有问题**：
- 查看日志中的 ERROR 信息
- 检查 API Key 是否正确
- 确认网络可以访问 API 服务

## 🔍 优先级说明

系统会按以下顺序选择 LLM：

1. **Qwen**（如果设置了 `DASHSCOPE_API_KEY`）
2. **DeepSeek**（如果设置了 `DEEPSEEK_API_KEY`）
3. **Google Gemini**（如果设置了 `GOOGLE_API_KEY`）
4. **OpenRouter**（默认，可以免费使用）

如果想使用特定的 LLM，只需要设置对应的 API Key，其他的可以注释掉。

## 💡 性能对比

| 提供商 | 速度 | 成本 | 中文能力 | 推荐场景 |
|--------|------|------|----------|----------|
| **Qwen** | ⚡⚡⚡ 快 | 💰 低 | 🇨🇳 优秀 | 中文场景，性价比高 |
| **DeepSeek** | ⚡⚡ 中 | 💰 低 | 🇨🇳 良好 | 代码相关任务 |
| **Gemini** | ⚡⚡⚡ 快 | 💰💰 中 | 🇨🇳 良好 | 多语言场景 |
| **OpenRouter** | ⚡⚡ 中 | 💰 免费 | 🇨🇳 一般 | 测试和开发 |

## 🐛 故障排查

### 问题 1：角色错误

```
Error: developer is not one of ['system', 'assistant', 'user']
```

**原因**：兼容层未生效

**解决**：
1. 确认 `compat_model.py` 文件存在
2. 重启服务：`bash restart.sh restart`
3. 检查日志确认使用了兼容层

### 问题 2：API Key 错误

```
Error: Invalid API key
```

**解决**：
1. 检查 `.env` 文件中的 API Key 是否正确
2. 确认 API Key 有效且有足够额度
3. 检查网络是否可以访问 API 服务

### 问题 3：连接超时

```
Error: Connection timeout
```

**解决**：
1. 检查网络连接
2. 如果在国内，某些服务可能需要代理
3. 尝试切换到其他 LLM 提供商

## 📚 相关文档

- **重启指南**：`/opt/valuecell/RESTART_GUIDE.md`
- **快速开始**：`/opt/valuecell/QUICK_START_QWEN_BINANCE.md`
- **错误修复**：`/opt/valuecell/FIXED_ERRORS.md`

## 🎉 总结

通过兼容层技术，ValueCell 现在可以：
- ✅ 支持 Qwen 和 DeepSeek
- ✅ 自动处理角色转换
- ✅ 无需修改 Agno 框架源码
- ✅ 保持代码简洁和可维护

---

**最后更新**：2025-10-29
**版本**：v2.0 - 支持 Qwen 和 DeepSeek

