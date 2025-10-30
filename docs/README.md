# ValueCell 文档中心

欢迎查阅 ValueCell 项目文档！

## 📚 文档列表

### 核心文档

1. **[详细功能与实现说明](DETAILED_FUNCTIONAL_SPECIFICATION.md)** ⭐ **新增**
   - 完整的系统架构说明
   - 数据获取与存储详解
   - Agent 系统实现
   - 对话与反馈机制
   - 交易与分析流程
   - 前端实现
   - API 接口文档
   - 部署与运维指南

2. **[核心架构](CORE_ARCHITECTURE.md)**
   - 协调器工作原理
   - SuperAgent 机制
   - 规划器与任务执行
   - A2A 协议集成

3. **[配置指南](CONFIGURATION_GUIDE.md)**
   - 环境变量配置
   - Agent 配置
   - 数据源配置

## 🚀 快速开始

### 第一次使用？

1. 阅读 [README.zh.md](../README.zh.md) 了解项目概况
2. 参考 [详细功能与实现说明](DETAILED_FUNCTIONAL_SPECIFICATION.md) 深入理解系统
3. 查看 [RESTART_GUIDE.md](../RESTART_GUIDE.md) 学习如何启动和重启服务

### 需要开发？

1. 先阅读 [详细功能与实现说明](DETAILED_FUNCTIONAL_SPECIFICATION.md) 第 4 章 "Agent 系统"
2. 参考 [核心架构](CORE_ARCHITECTURE.md) 了解内部机制
3. 查看代码示例和实现细节

### 需要部署？

1. 参考 [详细功能与实现说明](DETAILED_FUNCTIONAL_SPECIFICATION.md) 第 9 章 "部署与运维"
2. 使用提供的 `start.sh` 或 `restart.sh` 脚本
3. 查看日志和监控指南

## 📖 按主题查找

### 数据相关
- [数据获取与存储](DETAILED_FUNCTIONAL_SPECIFICATION.md#3-数据获取与存储)
- [数据适配器](DETAILED_FUNCTIONAL_SPECIFICATION.md#31-数据适配器架构)
- [数据库架构](DETAILED_FUNCTIONAL_SPECIFICATION.md#33-数据存储)

### Agent 相关
- [Agent 系统](DETAILED_FUNCTIONAL_SPECIFICATION.md#4-agent-系统)
- [Agent 通信协议](DETAILED_FUNCTIONAL_SPECIFICATION.md#43-agent-通信协议)
- [ResearchAgent 实现](DETAILED_FUNCTIONAL_SPECIFICATION.md#441-researchagent)
- [AutoTradingAgent 实现](DETAILED_FUNCTIONAL_SPECIFICATION.md#442-autotradingagent)

### 对话相关
- [对话流程](DETAILED_FUNCTIONAL_SPECIFICATION.md#51-对话流程)
- [SuperAgent 分流](DETAILED_FUNCTIONAL_SPECIFICATION.md#52-superagent-分流机制)
- [规划器](DETAILED_FUNCTIONAL_SPECIFICATION.md#53-规划器-planner)
- [流式响应](DETAILED_FUNCTIONAL_SPECIFICATION.md#54-任务执行与流式响应)

### 交易相关
- [自动交易流程](DETAILED_FUNCTIONAL_SPECIFICATION.md#61-自动交易完整流程)
- [技术分析](DETAILED_FUNCTIONAL_SPECIFICATION.md#62-技术分析详解)
- [AI 信号生成](DETAILED_FUNCTIONAL_SPECIFICATION.md#63-ai-信号生成)
- [风险管理](DETAILED_FUNCTIONAL_SPECIFICATION.md#642-风险管理)
- [交易执行](DETAILED_FUNCTIONAL_SPECIFICATION.md#65-交易执行)

### 前端相关
- [前端架构](DETAILED_FUNCTIONAL_SPECIFICATION.md#71-前端架构)
- [核心组件](DETAILED_FUNCTIONAL_SPECIFICATION.md#72-核心组件)
- [API 客户端](DETAILED_FUNCTIONAL_SPECIFICATION.md#73-api-客户端)

### API 相关
- [REST API](DETAILED_FUNCTIONAL_SPECIFICATION.md#81-rest-api-端点)
- [SSE 流式接口](DETAILED_FUNCTIONAL_SPECIFICATION.md#82-sse-流式接口)

## 🔍 搜索技巧

使用文档搜索功能快速定位：
- Ctrl+F (Windows/Linux) 或 Cmd+F (Mac)
- 在 [详细功能与实现说明](DETAILED_FUNCTIONAL_SPECIFICATION.md) 中搜索关键词

## 💡 常见问题

查看 [详细功能与实现说明 - 第 10 章](DETAILED_FUNCTIONAL_SPECIFICATION.md#10-常见问题) 获取常见问题解答。

## 📝 贡献文档

欢迎贡献文档！请查看 [CONTRIBUTING.md](../.github/CONTRIBUTING.md)。

---

**最后更新**: 2025-10-29
