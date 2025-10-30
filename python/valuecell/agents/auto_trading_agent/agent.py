"""Main auto trading agent implementation with multi-instance support"""

import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Deque, Dict, List, Optional

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from valuecell.core.agent.responses import streaming
from valuecell.core.types import (
    BaseAgent,
    ComponentType,
    FilteredCardPushNotificationComponentData,
    FilteredLineChartComponentData,
    StreamResponse,
)

from .constants import (
    DEFAULT_AGENT_MODEL,
    DEFAULT_CHECK_INTERVAL,
)
from .formatters import MessageFormatter
from .models import (
    AutoTradingConfig,
    TradingRequest,
)
from .portfolio_decision_manager import (
    AssetAnalysis,
    PortfolioDecisionManager,
)
from .technical_analysis import AISignalGenerator, TechnicalAnalyzer
from .trading_executor import TradingExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum cached notifications per session
MAX_NOTIFICATION_CACHE_SIZE = 5000


class AutoTradingAgent(BaseAgent):
    """
    Automated crypto trading agent with technical analysis and position management.
    Supports multiple trading instances per session with independent configurations.
    """

    def __init__(self):
        super().__init__()

        # Configuration
        self.parser_model_id = os.getenv("TRADING_PARSER_MODEL_ID", DEFAULT_AGENT_MODEL)

        # Multi-instance state management
        # Structure: {session_id: {instance_id: TradingInstanceData}}
        self.trading_instances: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Notification cache for batch sending
        # Structure: {session_id: deque[FilteredCardPushNotificationComponentData]}
        # Using deque with maxlen for automatic FIFO eviction
        self.notification_cache: Dict[
            str, Deque[FilteredCardPushNotificationComponentData]
        ] = {}

        try:
            # Parser agent for natural language query parsing
            # 使用 get_model() 以支持 Qwen/DeepSeek
            from valuecell.utils.model import get_model
            self.parser_agent = Agent(
                model=get_model("TRADING_PARSER_MODEL_ID"),
                output_schema=TradingRequest,
                markdown=True,
                # 添加 instructions 确保包含 "json" 关键字（通义千问要求）
                instructions=["Parse the trading request and respond in JSON format."],
            )
            logger.info("Auto Trading Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Auto Trading Agent: {e}")
            raise

    async def _process_trading_instance(
        self,
        session_id: str,
        instance_id: str,
        semaphore: asyncio.Semaphore,
        unified_timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Process a single trading instance with semaphore control for concurrency limiting.

        Args:
            session_id: Session identifier
            instance_id: Trading instance identifier
            semaphore: Asyncio semaphore to limit concurrent processing
            unified_timestamp: Optional unified timestamp for snapshot alignment across instances
        """
        async with semaphore:
            try:
                # Check if instance still exists and is active
                if instance_id not in self.trading_instances.get(session_id, {}):
                    return

                instance = self.trading_instances[session_id][instance_id]
                if not instance["active"]:
                    return

                # Get instance components
                executor = instance["executor"]
                config = instance["config"]
                ai_signal_generator = instance["ai_signal_generator"]

                # Update check info
                instance["check_count"] += 1
                instance["last_check"] = datetime.now()
                check_count = instance["check_count"]

                logger.info(
                    f"Trading check #{check_count} for instance {instance_id} (model: {config.agent_model})"
                )

                logger.info(
                    f"\n{'=' * 50}\n"
                    f"🔄 **Check #{check_count}** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Instance: `{instance_id}`\n"
                    f"Model: `{config.agent_model}`\n"
                    f"{'=' * 50}\n\n"
                )

                # Phase 1: Collect analysis for all symbols
                logger.info("📊 **Phase 1: Analyzing all assets...**\n\n")

                # Initialize portfolio manager with LLM client for AI-powered decisions
                llm_client = None
                if ai_signal_generator and ai_signal_generator.llm_client:
                    llm_client = ai_signal_generator.llm_client

                portfolio_manager = PortfolioDecisionManager(config, llm_client)
                
                # Store AI exit plans per symbol for decision history
                symbol_ai_exit_plans = {}

                for symbol in config.crypto_symbols:
                    # Calculate indicators
                    indicators = TechnicalAnalyzer.calculate_indicators(symbol)

                    if indicators is None:
                        logger.warning(f"Skipping {symbol} - insufficient data")
                        continue

                    # Generate technical signal
                    technical_action, technical_trade_type = (
                        TechnicalAnalyzer.generate_signal(indicators)
                    )

                    # Generate AI signal if enabled
                    ai_action, ai_trade_type, ai_reasoning, ai_confidence, ai_exit_plan = (
                        None,
                        None,
                        None,
                        None,
                        None,
                    )

                    if ai_signal_generator:
                        ai_signal = await ai_signal_generator.get_signal(indicators)
                        if ai_signal:
                            (
                                ai_action,
                                ai_trade_type,
                                ai_reasoning,
                                ai_confidence,
                                ai_exit_plan,
                            ) = ai_signal
                            # Store exit plan for decision history
                            if ai_exit_plan:
                                symbol_ai_exit_plans[symbol] = ai_exit_plan
                            logger.info(
                                f"AI signal for {symbol}: {ai_action.value} {ai_trade_type.value} "
                                f"(confidence: {ai_confidence}%)"
                            )

                    # Create asset analysis
                    asset_analysis = AssetAnalysis(
                        symbol=symbol,
                        indicators=indicators,
                        technical_action=technical_action,
                        technical_trade_type=technical_trade_type,
                        ai_action=ai_action,
                        ai_trade_type=ai_trade_type,
                        ai_reasoning=ai_reasoning,
                        ai_confidence=ai_confidence,
                    )

                    # Add to portfolio manager
                    portfolio_manager.add_asset_analysis(asset_analysis)

                    # Display individual asset analysis
                    logger.info(
                        MessageFormatter.format_market_analysis_notification(
                            symbol,
                            indicators,
                            asset_analysis.recommended_action,
                            asset_analysis.recommended_trade_type,
                            executor.positions,
                            ai_reasoning,
                        )
                    )

                # Phase 2: Make portfolio-level decision
                logger.info(
                    "\n" + "=" * 50 + "\n"
                    "🎯 **Phase 2: Portfolio Decision Making...**\n" + "=" * 50 + "\n\n"
                )

                # Get portfolio summary
                portfolio_summary = portfolio_manager.get_portfolio_summary()
                logger.info(portfolio_summary + "\n")

                # Make coordinated decision (async call for AI analysis)
                portfolio_decision = await portfolio_manager.make_portfolio_decision(
                    current_positions=executor.positions,
                    available_cash=executor.get_current_capital(),
                    total_portfolio_value=executor.get_portfolio_value(),
                )

                # Display decision reasoning - cache it
                portfolio_decision_msg = FilteredCardPushNotificationComponentData(
                    title=f"{config.agent_model} Analysis",
                    data=f"💰 **Portfolio Decision Reasoning**\n{portfolio_decision.reasoning}\n",
                    filters=[config.agent_model],
                    table_title="Market Analysis",
                    create_time=datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
                # Cache the decision notification
                self._cache_notification(session_id, portfolio_decision_msg)

                # Phase 3: Execute approved trades
                executed_trades_details = {}  # Store trade execution details for decision history
                if portfolio_decision.trades_to_execute:
                    logger.info(
                        "\n" + "=" * 50 + "\n"
                        f"⚡ **Phase 3: Executing {len(portfolio_decision.trades_to_execute)} trade(s)...**\n"
                        + "=" * 50
                        + "\n\n"
                    )

                    for (
                        symbol,
                        action,
                        trade_type,
                    ) in portfolio_decision.trades_to_execute:
                        # Get indicators for this symbol
                        asset_analysis = portfolio_manager.asset_analyses.get(symbol)
                        if not asset_analysis:
                            continue

                        # Execute trade
                        trade_details = executor.execute_trade(
                            symbol, action, trade_type, asset_analysis.indicators
                        )

                        # Store for decision history
                        executed_trades_details[symbol] = {
                            "trade_details": trade_details,
                            "action": action,
                            "trade_type": trade_type,
                        }

                        if trade_details:
                            # Cache trade notification
                            trade_message_text = (
                                MessageFormatter.format_trade_notification(
                                    trade_details, config.agent_model
                                )
                            )
                            trade_message = FilteredCardPushNotificationComponentData(
                                title=f"{config.agent_model} Trade",
                                data=f"💰 **Trade Executed:**\n{trade_message_text}\n",
                                filters=[config.agent_model],
                                table_title="Trade Detail",
                                create_time=datetime.now(timezone.utc).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            )
                            # Cache the trade notification
                            self._cache_notification(session_id, trade_message)
                        else:
                            trade_message = FilteredCardPushNotificationComponentData(
                                title=f"{config.agent_model} Trade",
                                data=f"💰 **Trade Failed:** Could not execute {action.value} "
                                f"{trade_type.value} on {symbol}\n",
                                filters=[config.agent_model],
                                table_title="Trade Detail",
                                create_time=datetime.now(timezone.utc).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            )
                            # Cache the failed trade notification
                            self._cache_notification(session_id, trade_message)

                # Take snapshots with unified timestamp if provided
                timestamp = unified_timestamp if unified_timestamp else datetime.now()
                executor.snapshot_positions(timestamp)
                executor.snapshot_portfolio(timestamp)
                
                # Collect decision history data for visualization
                instance["check_count"] += 1
                check_number = instance["check_count"]
                
                # Build decision history entry
                decision_entry = {
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
                    "check_number": check_number,
                    "symbol_decisions": [],
                    "portfolio_decision": {
                        "reasoning": portfolio_decision.reasoning,
                        "trades_to_execute": [
                            {
                                "symbol": symbol,
                                "action": action.value if hasattr(action, "value") else str(action),
                                "trade_type": trade_type.value if hasattr(trade_type, "value") else str(trade_type),
                            }
                            for symbol, action, trade_type in portfolio_decision.trades_to_execute
                        ],
                        "trades_executed": [],
                    },
                }
                
                # Collect symbol-level decisions
                for symbol, asset_analysis in portfolio_manager.asset_analyses.items():
                    indicators = asset_analysis.indicators
                    
                    # Get current position if exists
                    current_position = None
                    if symbol in executor.positions:
                        pos = executor.positions[symbol]
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(symbol)
                            current_price = float(ticker.history(period="1d", interval="1m")["Close"].iloc[-1])
                            if pos.trade_type.value == "long":
                                unrealized_pnl = (current_price - pos.entry_price) * abs(pos.quantity)
                            else:
                                unrealized_pnl = (pos.entry_price - current_price) * abs(pos.quantity)
                            
                            current_position = {
                                "entry_price": float(pos.entry_price),
                                "quantity": float(pos.quantity),
                                "trade_type": pos.trade_type.value if hasattr(pos.trade_type, "value") else str(pos.trade_type),
                                "unrealized_pnl": float(unrealized_pnl),
                                "current_price": float(current_price),
                            }
                        except Exception:
                            pass
                    
                    symbol_decision = {
                        "symbol": symbol,
                        "market_data": {
                            "price": float(indicators.close_price),
                            "volume": float(indicators.volume),
                            "historical_prices": indicators.historical_prices[-20:] if indicators.historical_prices else None,  # Last 20 prices
                            "historical_volumes": indicators.historical_volumes[-20:] if indicators.historical_volumes else None,  # Last 20 volumes
                        },
                        "technical_indicators": {
                            "macd": float(indicators.macd) if indicators.macd is not None else None,
                            "macd_signal": float(indicators.macd_signal) if indicators.macd_signal is not None else None,
                            "macd_histogram": float(indicators.macd_histogram) if indicators.macd_histogram is not None else None,
                            "rsi": float(indicators.rsi) if indicators.rsi is not None else None,
                            "ema_12": float(indicators.ema_12) if indicators.ema_12 is not None else None,
                            "ema_26": float(indicators.ema_26) if indicators.ema_26 is not None else None,
                            "ema_50": float(indicators.ema_50) if indicators.ema_50 is not None else None,
                            "bb_upper": float(indicators.bb_upper) if indicators.bb_upper is not None else None,
                            "bb_middle": float(indicators.bb_middle) if indicators.bb_middle is not None else None,
                            "bb_lower": float(indicators.bb_lower) if indicators.bb_lower is not None else None,
                        },
                        "technical_signal": {
                            "action": asset_analysis.technical_action.value if hasattr(asset_analysis.technical_action, "value") else str(asset_analysis.technical_action),
                            "trade_type": asset_analysis.technical_trade_type.value if hasattr(asset_analysis.technical_trade_type, "value") else str(asset_analysis.technical_trade_type),
                        },
                        "ai_analysis": None,
                        "current_position": current_position,
                    }
                    
                    # Add AI analysis if available
                    if asset_analysis.ai_action:
                        symbol_decision["ai_analysis"] = {
                            "action": asset_analysis.ai_action.value if hasattr(asset_analysis.ai_action, "value") else str(asset_analysis.ai_action),
                            "trade_type": asset_analysis.ai_trade_type.value if hasattr(asset_analysis.ai_trade_type, "value") else str(asset_analysis.ai_trade_type),
                            "reasoning": asset_analysis.ai_reasoning,
                            "confidence": float(asset_analysis.ai_confidence) if asset_analysis.ai_confidence is not None else None,
                            "exit_plan": symbol_ai_exit_plans.get(symbol),
                        }
                    
                    decision_entry["symbol_decisions"].append(symbol_decision)
                
                # Collect executed trades from execution details
                executed_trades = []
                for symbol, trade_info in executed_trades_details.items():
                    trade_details = trade_info["trade_details"]
                    action = trade_info["action"]
                    trade_type = trade_info["trade_type"]
                    
                    executed_trades.append({
                        "symbol": symbol,
                        "action": action.value if hasattr(action, "value") else str(action),
                        "trade_type": trade_type.value if hasattr(trade_type, "value") else str(trade_type),
                        "executed": trade_details is not None,
                        "execution_price": float(trade_details.price) if trade_details and hasattr(trade_details, "price") else None,
                        "quantity": float(trade_details.quantity) if trade_details and hasattr(trade_details, "quantity") else None,
                        "notional": float(trade_details.notional) if trade_details and hasattr(trade_details, "notional") else None,
                    })
                
                decision_entry["portfolio_decision"]["trades_executed"] = executed_trades
                
                # Add portfolio state
                decision_entry["portfolio_state"] = {
                    "total_value": float(executor.get_portfolio_value()),
                    "available_cash": float(executor.get_current_capital()),
                    "positions_value": sum(
                        float(pos.notional) for pos in executor.positions.values()
                    ),
                    "positions_count": len(executor.positions),
                    "total_pnl": float(executor.get_portfolio_value() - config.initial_capital),
                }
                
                # Save to decision history (keep last 500 entries)
                instance["decision_history"].append(decision_entry)
                if len(instance["decision_history"]) > 500:
                    instance["decision_history"] = instance["decision_history"][-500:]

                # Send portfolio update
                portfolio_value = executor.get_portfolio_value()
                total_pnl = portfolio_value - config.initial_capital

                portfolio_msg = (
                    f"💰 **Portfolio Update**\n"
                    f"Model: {config.agent_model}\n"
                    f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Total Value: ${portfolio_value:,.2f}\n"
                    f"P&L: ${total_pnl:,.2f}\n"
                    f"Open Positions: {len(executor.positions)}\n"
                    f"Available Capital: ${executor.current_capital:,.2f}\n"
                )

                if executor.positions:
                    portfolio_msg += "\n**Open Positions:**\n"
                    for symbol, pos in executor.positions.items():
                        try:
                            import yfinance as yf

                            ticker = yf.Ticker(symbol)
                            current_price = ticker.history(period="1d", interval="1m")[
                                "Close"
                            ].iloc[-1]
                            if pos.trade_type.value == "long":
                                current_pnl = (current_price - pos.entry_price) * abs(
                                    pos.quantity
                                )
                            else:
                                current_pnl = (pos.entry_price - current_price) * abs(
                                    pos.quantity
                                )
                            pnl_emoji = "🟢" if current_pnl >= 0 else "🔴"
                            portfolio_msg += f"- {symbol}: {pos.trade_type.value.upper()} @ ${pos.entry_price:,.2f} {pnl_emoji} P&L: ${current_pnl:,.2f}\n"
                        except Exception as e:
                            logger.warning(f"Failed to calculate P&L for {symbol}: {e}")
                            portfolio_msg += f"- {symbol}: {pos.trade_type.value.upper()} @ ${pos.entry_price:,.2f}\n"

                logger.info(portfolio_msg + "\n")

                # Cache portfolio status notification
                component_data = self._get_instance_status_component_data(
                    session_id, instance_id
                )
                if component_data:
                    self._cache_notification(session_id, component_data)

            except Exception as e:
                logger.error(f"Error processing trading instance {instance_id}: {e}")
                # Don't raise - let other instances continue

    def _generate_instance_id(self, task_id: str, model_id: str) -> str:
        """
        Generate unique instance ID for a specific model

        Args:
            task_id: Task ID from the request
            model_id: Model identifier (e.g., 'deepseek/deepseek-v3.1-terminus')

        Returns:
            Unique instance ID combining timestamp, task, and model
        """
        import hashlib

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )  # Include microseconds for uniqueness
        # Create a short hash from model_id for readability
        model_hash = hashlib.md5(model_id.encode()).hexdigest()[:6]
        # Extract model name (last part after /)
        model_name = model_id.split("/")[-1].replace("-", "_").replace(".", "_")[:15]

        return f"trade_{timestamp}_{model_name}_{model_hash}"

    def _init_notification_cache(self, session_id: str) -> None:
        """Initialize notification cache for a session if not exists"""
        if session_id not in self.notification_cache:
            self.notification_cache[session_id] = deque(
                maxlen=MAX_NOTIFICATION_CACHE_SIZE
            )
            logger.info(f"Initialized notification cache for session {session_id}")

    def _cache_notification(
        self, session_id: str, notification: FilteredCardPushNotificationComponentData
    ) -> None:
        """
        Cache a notification for later batch sending.
        Automatically evicts oldest notifications when cache exceeds MAX_NOTIFICATION_CACHE_SIZE.

        Args:
            session_id: Session ID
            notification: Notification to cache
        """
        self._init_notification_cache(session_id)
        self.notification_cache[session_id].append(notification)
        logger.debug(
            f"Cached notification for session {session_id}. "
            f"Cache size: {len(self.notification_cache[session_id])}"
        )

    def _get_cached_notifications(
        self, session_id: str
    ) -> List[FilteredCardPushNotificationComponentData]:
        """
        Get all cached notifications for a session.

        Args:
            session_id: Session ID

        Returns:
            List of cached notifications (oldest to newest)
        """
        if session_id not in self.notification_cache:
            return []
        return list(self.notification_cache[session_id])

    def _clear_notification_cache(self, session_id: str) -> None:
        """
        Clear notification cache for a session.

        Args:
            session_id: Session ID
        """
        if session_id in self.notification_cache:
            self.notification_cache[session_id].clear()
            logger.info(f"Cleared notification cache for session {session_id}")

    async def _parse_trading_request(self, query: str) -> TradingRequest:
        """
        Parse natural language query to extract trading parameters

        Args:
            query: User's natural language query

        Returns:
            TradingRequest object with parsed parameters
        """
        try:
            parse_prompt = f"""
            Parse the following user query and extract auto trading configuration parameters:
            
            User query: "{query}"
            
            Please identify:
            1. crypto_symbols: List of cryptocurrency symbols to trade (e.g., BTC-USD, ETH-USD, SOL-USD)
               - If user mentions "Bitcoin", extract as "BTC-USD"
               - If user mentions "Ethereum", extract as "ETH-USD"
               - If user mentions "Solana", extract as "SOL-USD"
               - Always use format: SYMBOL-USD
            2. initial_capital: Initial trading capital in USD (default: 100000 if not specified)
            3. use_ai_signals: Whether to use AI-enhanced signals (default: true)
            4. agent_model: Model ID for trading decisions (default: DEFAULT_AGENT_MODEL)
            
            Examples:
            - "Trade Bitcoin and Ethereum with $50000" -> {{"crypto_symbols": ["BTC-USD", "ETH-USD"], "initial_capital": 50000, "use_ai_signals": true}}
            - "Start auto trading BTC-USD" -> {{"crypto_symbols": ["BTC-USD"], "initial_capital": 100000, "use_ai_signals": true}}
            - "Trade BTC with AI signals" -> {{"crypto_symbols": ["BTC-USD"], "initial_capital": 100000, "use_ai_signals": true}}
            - "Trade BTC with AI signals using DeepSeek model" -> {{"crypto_symbols": ["BTC-USD"], "initial_capital": 100000, "use_ai_signals": true, "agent_models": ["deepseek/deepseek-v3.1-terminus"]}}
            - "Trade Bitcoin, SOL, Eth and DOGE with 100000 capital, using x-ai/grok-4, deepseek/deepseek-v3.1-terminus model" -> {{"crypto_symbols": ["BTC-USD", "SOL-USD", "ETH-USD", "DOGE-USD"], "initial_capital": 100000, "use_ai_signals": true, "agent_models": ["x-ai/grok-4", "deepseek/deepseek-v3.1-terminus"]}}
            """

            response = await self.parser_agent.arun(parse_prompt)
            trading_request = response.content

            logger.info(f"Parsed trading request: {trading_request}")
            return trading_request

        except Exception as e:
            logger.error(f"Failed to parse trading request: {e}")
            raise ValueError(
                f"Could not parse trading configuration from query: {query}"
            )

    def _initialize_ai_signal_generator(
        self, config: AutoTradingConfig
    ) -> Optional[AISignalGenerator]:
        """Initialize AI signal generator if configured"""
        if not config.use_ai_signals:
            return None

        try:
            from valuecell.utils.model import get_model
            # 使用 get_model() 以支持 Qwen/DeepSeek
            # 如果配置了特定模型，使用配置的模型；否则使用默认
            if config.agent_model and config.agent_model != DEFAULT_AGENT_MODEL:
                # 检查是否是 Qwen 或 DeepSeek 模型
                if "qwen" in config.agent_model.lower():
                    llm_client = get_model("TRADING_PARSER_MODEL_ID")
                elif "deepseek" in config.agent_model.lower():
                    llm_client = get_model("TRADING_PARSER_MODEL_ID")
                else:
                    # 使用 OpenRouter
                    api_key = config.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
                    if not api_key:
                        logger.warning("OpenRouter API key not provided, AI signals disabled")
                        return None
                    llm_client = OpenRouter(
                        id=config.agent_model,
                        api_key=api_key,
                    )
            else:
                # 使用默认模型（通过 get_model 支持 Qwen/DeepSeek）
                llm_client = get_model("TRADING_PARSER_MODEL_ID")
            
            return AISignalGenerator(llm_client)

        except Exception as e:
            logger.error(f"Failed to initialize AI signal generator: {e}")
            return None

    def _clean_for_json(self, obj):
        """Recursively clean data for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._clean_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._clean_for_json(obj.__dict__)
        else:
            return obj

    def _get_position_history_data(self, executor: "TradingExecutor", positions: Dict[str, "Position"]) -> List[Dict]:
        """Get position history data with current prices and PnL"""
        import yfinance as yf
        
        position_list = []
        for symbol, pos in positions.items():
            try:
                # Get current price
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d", interval="1m")
                if not data.empty:
                    current_price = float(data["Close"].iloc[-1])
                else:
                    current_price = pos.entry_price
            except Exception as e:
                logger.debug(f"Failed to get current price for {symbol}, using entry_price: {e}")
                current_price = pos.entry_price
            
            # Calculate unrealized PnL
            try:
                unrealized_pnl = executor._position_manager.calculate_position_pnl(pos, current_price)
            except Exception:
                unrealized_pnl = 0.0
            
            position_list.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": str(symbol),
                "quantity": float(pos.quantity),
                "entry_price": float(pos.entry_price),
                "current_price": float(current_price),
                "trade_type": pos.trade_type.value if hasattr(pos.trade_type, 'value') else str(pos.trade_type),
                "unrealized_pnl": float(unrealized_pnl),
                "notional": float(pos.notional),
            })
        
        return position_list

    def _save_trading_data_to_file(self):
        """
        Save all trading instances data to file for API access
        This enables the monitoring dashboard to access trading data
        """
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "instances": []
            }
            
            for session_id, instances in self.trading_instances.items():
                for instance_id, instance in instances.items():
                    executor: TradingExecutor = instance["executor"]
                    config: AutoTradingConfig = instance["config"]
                    
                    # Get current portfolio state
                    portfolio_summary = executor.get_portfolio_summary()
                    portfolio_history = executor.get_portfolio_history()
                    trade_history = executor.get_trade_history()
                    positions = executor.positions  # Use property, not method
                    
                    # Calculate current values
                    total_value, positions_value, total_pnl = executor._position_manager.calculate_portfolio_value()
                    
                    instance_data = {
                        "instance_id": instance_id,
                        "session_id": session_id,
                        "active": instance["active"],
                        "created_at": (
                            instance.get("created_at").isoformat() 
                            if instance.get("created_at") and isinstance(instance.get("created_at"), datetime)
                            else (instance.get("created_at") if isinstance(instance.get("created_at"), str) else datetime.now(timezone.utc).isoformat())
                        ),
                        "config": {
                            "initial_capital": config.initial_capital,
                            "crypto_symbols": config.crypto_symbols,
                            "agent_model": config.agent_model,
                            "use_ai_signals": config.use_ai_signals,
                            "check_interval": config.check_interval,
                            "risk_per_trade": config.risk_per_trade,
                            "max_positions": config.max_positions,
                        },
                        "portfolio_history": [
                            {
                                "timestamp": (snapshot.timestamp.isoformat() if hasattr(snapshot.timestamp, "isoformat") and isinstance(snapshot.timestamp, datetime) else str(snapshot.timestamp)),
                                "total_value": float(snapshot.total_value),
                                "cash": float(snapshot.cash),
                                "positions_value": float(snapshot.positions_value),
                                "total_pnl": float(snapshot.total_pnl),
                                "positions_count": int(snapshot.positions_count),
                            }
                            for snapshot in portfolio_history[-100:]  # Last 100 snapshots
                        ],
                        "trade_history": [
                            {
                                "timestamp": (trade.timestamp.isoformat() if hasattr(trade.timestamp, "isoformat") and isinstance(trade.timestamp, datetime) else str(trade.timestamp)),
                                "symbol": str(trade.symbol),
                                "action": trade.action if isinstance(trade.action, str) else str(trade.action),
                                "trade_type": trade.trade_type if isinstance(trade.trade_type, str) else str(trade.trade_type),
                                "price": float(trade.price),
                                "quantity": float(trade.quantity),
                                "notional": float(trade.notional),
                                "pnl": float(trade.pnl) if hasattr(trade, 'pnl') and trade.pnl is not None else None,
                            }
                            for trade in trade_history[-50:]  # Last 50 trades
                        ],
                        "position_history": self._get_position_history_data(executor, positions),
                        "decision_history": self._clean_for_json(instance.get("decision_history", []))[-100:],  # Last 100 decisions
                    }
                    
                    data["instances"].append(instance_data)
            
            # Save to file
            file_path = "/tmp/valuecell_trading_data.json"
            # Clean all datetime objects before JSON serialization
            cleaned_data = self._clean_for_json(data)
            with open(file_path, "w") as f:
                json.dump(cleaned_data, f, indent=2)
            
            logger.debug(f"Saved trading data for {len(data['instances'])} instances to {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to save trading data to file: {e}")

    def _get_instance_status_component_data(
        self, session_id: str, instance_id: str
    ) -> Optional[FilteredCardPushNotificationComponentData]:
        """
        Generate portfolio status report in rich text format

        Returns:
            FilteredCardPushNotificationComponentData object or None if instance not found
        """
        if session_id not in self.trading_instances:
            return None

        if instance_id not in self.trading_instances[session_id]:
            return None

        instance = self.trading_instances[session_id][instance_id]
        executor: TradingExecutor = instance["executor"]
        config: AutoTradingConfig = instance["config"]

        # Get comprehensive portfolio summary
        portfolio_summary = executor.get_portfolio_summary()

        # Calculate overall statistics
        total_pnl = portfolio_summary["portfolio"]["total_pnl"]
        pnl_pct = portfolio_summary["portfolio"]["pnl_percentage"]
        portfolio_value = portfolio_summary["portfolio"]["total_value"]
        available_cash = portfolio_summary["cash"]["available"]

        # Build rich text output
        output = []

        # Header
        output.append(f"📊 **Trading Portfolio Status** - {instance_id}")
        output.append("\n**Instance Configuration**")
        output.append(f"- Model: `{config.agent_model}`")
        output.append(f"- Symbols: {', '.join(config.crypto_symbols)}")
        output.append(
            f"- Status: {'🟢 Active' if instance['active'] else '🔴 Stopped'}"
        )

        # Portfolio Summary Section
        output.append("\n💰 **Portfolio Summary**")
        output.append("\n**Overall Performance**")
        output.append(f"- Initial Capital: `${config.initial_capital:,.2f}`")
        output.append(f"- Current Value: `${portfolio_value:,.2f}`")

        pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
        pnl_sign = "+" if total_pnl >= 0 else ""
        output.append(
            f"- Total P&L: {pnl_emoji} **{pnl_sign}${total_pnl:,.2f}** ({pnl_sign}{pnl_pct:.2f}%)"
        )

        output.append("\n**Cash Position**")
        output.append(f"- Available Cash: `${available_cash:,.2f}`")

        # Current Positions Section
        output.append(f"\n📈 **Current Positions ({len(executor.positions)})**")

        if executor.positions:
            output.append(
                "\n| Symbol | Type | Quantity | Avg Price | Current Price | Position Value | Unrealized P&L |"
            )
            output.append(
                "|--------|------|----------|-----------|---------------|----------------|----------------|"
            )

            for symbol, pos in executor.positions.items():
                try:
                    import yfinance as yf

                    ticker = yf.Ticker(symbol)
                    current_price = ticker.history(period="1d", interval="1m")[
                        "Close"
                    ].iloc[-1]

                    # Calculate unrealized P&L
                    if pos.trade_type.value == "long":
                        unrealized_pnl = (current_price - pos.entry_price) * abs(
                            pos.quantity
                        )
                        position_value = abs(pos.quantity) * current_price
                    else:
                        unrealized_pnl = (pos.entry_price - current_price) * abs(
                            pos.quantity
                        )
                        position_value = pos.notional + unrealized_pnl

                    # Format row
                    pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
                    pnl_sign = "+" if unrealized_pnl >= 0 else ""

                    output.append(
                        f"| **{symbol}** | {pos.trade_type.value.upper()} | "
                        f"{abs(pos.quantity):.4f} | ${pos.entry_price:,.2f} | "
                        f"${current_price:,.2f} | ${position_value:,.2f} | "
                        f"{pnl_emoji} {pnl_sign}${unrealized_pnl:,.2f} |"
                    )

                except Exception as e:
                    logger.warning(f"Failed to get price for {symbol}: {e}")
                    # Fallback display with entry price only
                    output.append(
                        f"| **{symbol}** | {pos.trade_type.value.upper()} | "
                        f"{abs(pos.quantity):.4f} | ${pos.entry_price:,.2f} | "
                        f"N/A | ${pos.notional:,.2f} | N/A |"
                    )
        else:
            output.append("\n*No open positions*")

        component_data = FilteredCardPushNotificationComponentData(
            title=f"{config.agent_model} Portfolio Status",
            data="\n".join(output),
            filters=[config.agent_model],
            table_title="Portfolio Detail",
            create_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        )
        return component_data

    def _get_session_portfolio_chart_data(self, session_id: str) -> str:
        """
        Generate FilteredLineChartComponentData for all instances in a session
        Uses forward-fill strategy to handle missing timestamps

        Data format:
        [
            ['Time', 'model1', 'model2', 'model3'],
            ['2025-10-21 10:00:00', 100000, 50000, 30000],
            ['2025-10-21 10:01:00', 100234, 50123, 30045],
            ...
        ]

        Returns:
            JSON string of FilteredLineChartComponentData
        """
        if session_id not in self.trading_instances:
            return ""

        # Collect portfolio value history from all instances
        # Store as {model_id: {'initial_capital': float, 'history': [(timestamp, value)]}}
        model_data = {}

        for instance_id, instance in self.trading_instances[session_id].items():
            executor: TradingExecutor = instance["executor"]
            config: AutoTradingConfig = instance["config"]
            model_id = config.agent_model

            if model_id not in model_data:
                model_data[model_id] = {
                    "initial_capital": config.initial_capital,
                    "history": [],
                }

            portfolio_history = executor.get_portfolio_history()

            for snapshot in portfolio_history:
                model_data[model_id]["history"].append(
                    (snapshot.timestamp, snapshot.total_value)
                )

        if not model_data:
            return ""

        # Sort each model's history by timestamp
        for model_id in model_data:
            model_data[model_id]["history"].sort(key=lambda x: x[0])

        # Collect all unique timestamps across all models
        all_timestamps = set()
        for model_id, data in model_data.items():
            for timestamp, _ in data["history"]:
                all_timestamps.add(timestamp)

        if not all_timestamps:
            return ""

        sorted_timestamps = sorted(all_timestamps)
        model_ids = list(model_data.keys())

        # Build data array with forward-fill strategy
        # First row: ['Time', 'model1', 'model2', ...]
        data_array = [["Time"] + model_ids]

        # Track last known value for each model (for forward-fill)
        last_known_values = {
            model_id: data["initial_capital"] for model_id, data in model_data.items()
        }

        # Data rows: ['timestamp', value1, value2, ...]
        for timestamp in sorted_timestamps:
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp_str]

            for model_id in model_ids:
                # Find value at this timestamp for this model
                value_at_timestamp = None
                for ts, val in model_data[model_id]["history"]:
                    if ts == timestamp:
                        value_at_timestamp = val
                        break

                # Update logic: use new value if found, otherwise forward-fill
                if value_at_timestamp is not None:
                    last_known_values[model_id] = value_at_timestamp
                    row.append(value_at_timestamp)
                else:
                    # Use last known value (forward-fill)
                    row.append(last_known_values[model_id])

            data_array.append(row)

        component_data = FilteredLineChartComponentData(
            title=f"Portfolio Value History - Session {session_id[:8]}",
            data=json.dumps(data_array),
            create_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        )

        return component_data.model_dump_json()

    async def _handle_stop_command(
        self, session_id: str, query: str
    ) -> AsyncGenerator[StreamResponse, None]:
        """Handle stop command for trading instances"""
        query_lower = query.lower().strip()

        # Check if specific instance_id is provided
        instance_id = None
        if "instance_id:" in query_lower or "instance:" in query_lower:
            # Extract instance_id
            parts = query.split(":")
            if len(parts) >= 2:
                instance_id = parts[1].strip()

        if session_id not in self.trading_instances:
            yield streaming.message_chunk(
                "⚠️ No active trading instances found in this session.\n"
            )
            return

        if instance_id:
            # Stop specific instance
            if instance_id in self.trading_instances[session_id]:
                self.trading_instances[session_id][instance_id]["active"] = False
                executor = self.trading_instances[session_id][instance_id]["executor"]
                portfolio_value = executor.get_portfolio_value()

                yield streaming.message_chunk(
                    f"🛑 **Trading Instance Stopped**\n\n"
                    f"Instance ID: `{instance_id}`\n"
                    f"Final Portfolio Value: ${portfolio_value:,.2f}\n"
                    f"Open Positions: {len(executor.positions)}\n\n"
                )
            else:
                yield streaming.message_chunk(
                    f"⚠️ Instance ID '{instance_id}' not found.\n"
                )
        else:
            # Stop all instances in this session
            count = 0
            for inst_id in self.trading_instances[session_id]:
                self.trading_instances[session_id][inst_id]["active"] = False
                count += 1

            yield streaming.message_chunk(
                f"🛑 **All Trading Instances Stopped**\n\n"
                f"Stopped {count} instance(s) in session: {session_id[:8]}\n\n"
            )

    async def _handle_status_command(
        self, session_id: str
    ) -> AsyncGenerator[StreamResponse, None]:
        """Handle status query command"""
        if (
            session_id not in self.trading_instances
            or not self.trading_instances[session_id]
        ):
            yield streaming.message_chunk(
                "⚠️ No trading instances found in this session.\n"
            )
            return

        status_message = f"📊 **Session Status** - {session_id[:8]}\n\n"
        status_message += (
            f"**Total Instances:** {len(self.trading_instances[session_id])}\n\n"
        )

        for instance_id, instance in self.trading_instances[session_id].items():
            executor: TradingExecutor = instance["executor"]
            config: AutoTradingConfig = instance["config"]

            status = "🟢 Active" if instance["active"] else "🔴 Stopped"
            portfolio_value = executor.get_portfolio_value()
            total_pnl = portfolio_value - config.initial_capital

            status_message += (
                f"**Instance:** `{instance_id}`  {status}\n"
                f"- Model: {config.agent_model}\n"
                f"- Symbols: {', '.join(config.crypto_symbols)}\n"
                f"- Portfolio Value: ${portfolio_value:,.2f}\n"
                f"- P&L: ${total_pnl:,.2f}\n"
                f"- Open Positions: {len(executor.positions)}\n"
                f"- Total Trades: {len(executor.get_trade_history())}\n"
                f"- Checks: {instance['check_count']}\n\n"
            )

        logger.info(f"Status message: {status_message}")

    async def stream(
        self,
        query: str,
        session_id: str,
        task_id: str,
        dependencies: Optional[Dict] = None,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Process trading requests and manage multiple trading instances per session.

        Args:
            query: User's natural language query
            session_id: Session ID
            task_id: Task ID
            dependencies: Optional dependencies

        Yields:
            StreamResponse: Trading setup, execution updates, and data visualizations
        """
        # Track created instances for cleanup
        created_instances = []

        try:
            logger.info(
                f"Processing auto trading request - session: {session_id}, task: {task_id}"
            )

            query_lower = query.lower().strip()

            # Handle stop commands
            if any(
                cmd in query_lower.split()
                for cmd in ["stop", "pause", "halt", "停止", "暂停"]
            ):
                async for response in self._handle_stop_command(session_id, query):
                    yield response
                return

            # Handle status query commands
            if any(
                cmd in query_lower.split()
                for cmd in ["status", "summary", "状态", "摘要"]
            ):
                async for response in self._handle_status_command(session_id):
                    yield response
                return

            # Parse natural language query to extract trading configuration
            yield streaming.message_chunk("🔍 **Parsing trading request...**\n\n")

            try:
                trading_request = await self._parse_trading_request(query)
                logger.info(f"Parsed request: {trading_request}")
            except Exception as e:
                logger.error(f"Failed to parse trading request: {e}")
                yield streaming.failed(
                    "**Parse Error**: Could not parse trading configuration from your query. "
                    "Please specify cryptocurrency symbols (e.g., 'Trade Bitcoin and Ethereum')."
                )
                return

            # Initialize session structure if needed
            if session_id not in self.trading_instances:
                self.trading_instances[session_id] = {}

            # Initialize notification cache for this session
            self._init_notification_cache(session_id)

            # Get list of models to create instances for
            agent_models = trading_request.agent_models or [DEFAULT_AGENT_MODEL]

            # Create one trading instance per model
            yield streaming.message_chunk(
                f"🚀 **Creating {len(agent_models)} trading instance(s)...**\n\n"
            )

            for model_id in agent_models:
                # Generate unique instance ID for this model
                instance_id = self._generate_instance_id(task_id, model_id)

                # Create configuration for this specific model
                config = AutoTradingConfig(
                    initial_capital=trading_request.initial_capital or 100000,
                    crypto_symbols=trading_request.crypto_symbols,
                    use_ai_signals=trading_request.use_ai_signals or False,
                    agent_model=model_id,
                )

                # Initialize executor
                executor = TradingExecutor(config)

                # Initialize AI signal generator if enabled
                ai_signal_generator = self._initialize_ai_signal_generator(config)

                # Store instance
                self.trading_instances[session_id][instance_id] = {
                    "instance_id": instance_id,
                    "config": config,
                    "executor": executor,
                    "ai_signal_generator": ai_signal_generator,
                    "active": True,
                    "created_at": datetime.now(),
                    "check_count": 0,
                    "last_check": None,
                    "decision_history": [],  # Store AI decision history for visualization
                }

                created_instances.append(instance_id)

                # Display configuration for this instance
                ai_status = "✅ Enabled" if config.use_ai_signals else "❌ Disabled"
                config_message = (
                    f"✅ **Trading Instance Created**\n\n"
                    f"**Instance ID:** `{instance_id}`\n"
                    f"**Model:** `{model_id}`\n\n"
                    f"**Configuration:**\n"
                    f"- Trading Symbols: {', '.join(config.crypto_symbols)}\n"
                    f"- Initial Capital: ${config.initial_capital:,.2f}\n"
                    f"- Check Interval: {config.check_interval}s (1 minute)\n"
                    f"- Risk Per Trade: {config.risk_per_trade * 100:.1f}%\n"
                    f"- Max Positions: {config.max_positions}\n"
                    f"- AI Signals: {ai_status}\n\n"
                )

                yield streaming.message_chunk(config_message)

            # Summary message
            yield streaming.message_chunk(
                f"**Session ID:** `{session_id[:8]}`\n"
                f"**Total Active Instances in Session:** {len(self.trading_instances[session_id])}\n\n"
                f"🚀 **Starting continuous trading for all instances...**\n"
                f"All instances will run continuously until stopped.\n\n"
            )

            # Initialize all instances with portfolio snapshots
            # Use unified timestamp for initial snapshots to align chart data
            unified_initial_timestamp = datetime.now()
            for instance_id in created_instances:
                instance = self.trading_instances[session_id][instance_id]
                executor = instance["executor"]
                config = instance["config"]

                # Send initial portfolio snapshot - cache it
                portfolio_value = executor.get_portfolio_value()
                executor.snapshot_portfolio(unified_initial_timestamp)

                initial_portfolio_msg = FilteredCardPushNotificationComponentData(
                    title=f"{config.agent_model} Portfolio",
                    data=f"💰 **Initial Portfolio**\nTotal Value: ${portfolio_value:,.2f}\nAvailable Capital: ${executor.current_capital:,.2f}\n",
                    filters=[config.agent_model],
                    table_title="Portfolio Detail",
                    create_time=datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
                # Cache the initial notification
                self._cache_notification(session_id, initial_portfolio_msg)

            # Save initial trading data to file
            self._save_trading_data_to_file()
            
            # Set check interval
            check_interval = DEFAULT_CHECK_INTERVAL

            # Create semaphore to limit concurrent instance processing (max 10)
            semaphore = asyncio.Semaphore(10)

            # Main trading loop - monitor all instances in parallel
            yield streaming.message_chunk(
                "📈 **Starting monitoring loop for all instances...**\n\n"
            )

            # Check if any instance is still active
            while any(
                self.trading_instances[session_id][inst_id]["active"]
                for inst_id in created_instances
                if inst_id in self.trading_instances[session_id]
            ):
                try:
                    # Create unified timestamp for this iteration to align snapshots
                    unified_timestamp = datetime.now()

                    # Process all active instances concurrently using task pool
                    tasks = []
                    for instance_id in created_instances:
                        # Skip if instance was removed or is inactive
                        if instance_id not in self.trading_instances[session_id]:
                            continue

                        instance = self.trading_instances[session_id][instance_id]
                        if not instance["active"]:
                            continue

                        # Create task for this instance with semaphore control and unified timestamp
                        task = asyncio.create_task(
                            self._process_trading_instance(
                                session_id, instance_id, semaphore, unified_timestamp
                            )
                        )
                        tasks.append(task)

                    # Wait for all instance tasks to complete (process concurrently)
                    if tasks:
                        # Gather all tasks and handle any exceptions
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # Log any exceptions that occurred
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                logger.error(
                                    f"Task {i} failed with exception: {result}"
                                )

                    # After processing all instances, send batched notifications
                    cached_notifications = self._get_cached_notifications(session_id)
                    if cached_notifications:
                        logger.info(
                            f"Sending {len(cached_notifications)} cached notifications for session {session_id}"
                        )
                        # Convert all cached notifications to a list of dicts for batch sending
                        batch_data = [
                            notif.model_dump() for notif in cached_notifications
                        ]
                        # Send as a single batch component - frontend will receive all historical data
                        yield streaming.component_generator(
                            json.dumps(batch_data),
                            ComponentType.FILTERED_CARD_PUSH_NOTIFICATION,
                            component_id=f"trading_status_{session_id}",
                        )

                    # Send chart data (not cached, sent separately)
                    chart_data = self._get_session_portfolio_chart_data(session_id)
                    if chart_data:
                        yield streaming.component_generator(
                            content=chart_data,
                            component_type=ComponentType.FILTERED_LINE_CHART,
                            component_id=f"portfolio_chart_{session_id}",
                        )

                    # Save trading data to file for monitoring API
                    self._save_trading_data_to_file()
                    
                    # Wait for next check interval - only sleep once after processing all instances
                    logger.info(f"Waiting {check_interval}s until next check...")
                    await asyncio.sleep(check_interval)

                except Exception as e:
                    logger.error(f"Error during trading cycle: {e}")
                    yield streaming.message_chunk(
                        f"⚠️ **Error during trading cycle**: {str(e)}\n"
                        f"Continuing with next check...\n\n"
                    )
                    await asyncio.sleep(check_interval)

        except Exception as e:
            logger.error(f"Critical error in stream method: {e}")
            yield streaming.failed(f"Critical error: {str(e)}")
        finally:
            # Mark all created instances as inactive but keep data for history
            if session_id in self.trading_instances:
                for instance_id in created_instances:
                    if instance_id in self.trading_instances[session_id]:
                        self.trading_instances[session_id][instance_id]["active"] = (
                            False
                        )
                        logger.info(f"Stopped instance: {instance_id}")
