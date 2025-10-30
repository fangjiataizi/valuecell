"""Technical analysis and signal generation (refactored)"""

import json
import logging
from typing import Optional

from agno.agent import Agent

from .market_data import MarketDataProvider, SignalGenerator
from .models import TechnicalIndicators, TradeAction, TradeType

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """
    Static interface for technical analysis (backward compatible).

    Now delegates to MarketDataProvider internally.
    """

    _market_data_provider = MarketDataProvider()

    @staticmethod
    def calculate_indicators(
        symbol: str, period: str = "5d", interval: str = "1m"
    ) -> Optional[TechnicalIndicators]:
        """
        Calculate technical indicators using yfinance data.

        Args:
            symbol: Trading symbol (e.g., BTC-USD)
            period: Data period
            interval: Data interval

        Returns:
            TechnicalIndicators object or None if calculation fails
        """
        return TechnicalAnalyzer._market_data_provider.calculate_indicators(
            symbol, period, interval
        )

    @staticmethod
    def generate_signal(
        indicators: TechnicalIndicators,
    ) -> tuple[TradeAction, TradeType]:
        """
        Generate trading signal based on technical indicators.

        Args:
            indicators: Technical indicators for analysis

        Returns:
            Tuple of (TradeAction, TradeType)
        """
        return SignalGenerator.generate_signal(indicators)


class AISignalGenerator:
    """AI-enhanced signal generation using LLM"""

    def __init__(self, llm_client):
        """
        Initialize AI signal generator

        Args:
            llm_client: OpenRouter client instance
        """
        self.llm_client = llm_client

    async def get_signal(
        self,
        indicators: TechnicalIndicators,
        available_cash: Optional[float] = None,
        current_position: Optional[dict] = None,
        portfolio_value: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
    ) -> Optional[tuple[TradeAction, TradeType, str, float, Optional[dict]]]:
        """
        Get AI-enhanced trading signal with Alpha Arena-style comprehensive analysis

        Args:
            indicators: Technical indicators for analysis
            available_cash: Available cash for new positions
            current_position: Current position info (entry_price, quantity, unrealized_pnl)
            portfolio_value: Total portfolio value
            sharpe_ratio: Risk-adjusted return metric

        Returns:
            Tuple of (TradeAction, TradeType, reasoning, confidence, exit_plan) or None
        """
        if not self.llm_client:
            return None

        try:
            # Build historical price section (Alpha Arena style!)
            hist_prices_str = ""
            if indicators.historical_prices:
                hist_prices_str = "\n📊 Historical Prices (⚠️ ORDERED FROM OLDEST TO NEWEST):\n"
                num_prices = len(indicators.historical_prices)
                for i, price in enumerate(indicators.historical_prices):
                    bars_ago = num_prices - i - 1
                    if bars_ago == 0:
                        hist_prices_str += f"   • Current: ${price:,.2f}\n"
                    else:
                        hist_prices_str += f"   • {bars_ago} bars ago: ${price:,.2f}\n"

            # Build account status section
            account_status_str = ""
            if available_cash is not None or portfolio_value is not None:
                account_status_str = "\n💰 Portfolio Status:\n"
                if portfolio_value:
                    account_status_str += f"   • Portfolio Value: ${portfolio_value:,.2f}\n"
                if available_cash:
                    account_status_str += f"   • Available Cash: ${available_cash:,.2f}\n"
                if current_position:
                    entry = current_position.get('entry_price', 0)
                    qty = current_position.get('quantity', 0)
                    pnl = current_position.get('unrealized_pnl', 0)
                    pnl_pct = (pnl / (entry * qty) * 100) if (entry * qty) > 0 else 0
                    account_status_str += f"   • Current Position: {current_position.get('trade_type', 'LONG').upper()} {qty:.4f} @ ${entry:,.2f} (P&L: ${pnl:,.2f} / {pnl_pct:+.2f}%)\n"
                if sharpe_ratio is not None:
                    account_status_str += f"   • Sharpe Ratio: {sharpe_ratio:.2f}\n"

            # Format indicators
            macd_str = f"{indicators.macd:.4f}" if indicators.macd is not None else "N/A"
            macd_signal_str = f"{indicators.macd_signal:.4f}" if indicators.macd_signal is not None else "N/A"
            macd_histogram_str = f"{indicators.macd_histogram:.4f}" if indicators.macd_histogram is not None else "N/A"
            rsi_str = f"{indicators.rsi:.2f}" if indicators.rsi is not None else "N/A"
            ema_12_str = f"${indicators.ema_12:,.2f}" if indicators.ema_12 is not None else "N/A"
            ema_26_str = f"${indicators.ema_26:,.2f}" if indicators.ema_26 is not None else "N/A"
            ema_50_str = f"${indicators.ema_50:,.2f}" if indicators.ema_50 is not None else "N/A"
            bb_upper_str = f"${indicators.bb_upper:,.2f}" if indicators.bb_upper is not None else "N/A"
            bb_middle_str = f"${indicators.bb_middle:,.2f}" if indicators.bb_middle is not None else "N/A"
            bb_lower_str = f"${indicators.bb_lower:,.2f}" if indicators.bb_lower is not None else "N/A"

            prompt = f"""You are an expert cryptocurrency trading analyst. Analyze the market data and provide a trading decision for {indicators.symbol}.

🔍 Current Market Data:
   • Symbol: {indicators.symbol}
   • Current Price: ${indicators.close_price:,.2f}
   • Volume: {indicators.volume:,.0f}
{hist_prices_str}
📈 Technical Indicators:
   • MACD: {macd_str}
   • MACD Signal: {macd_signal_str}
   • MACD Histogram: {macd_histogram_str}
   • RSI: {rsi_str}
   • EMA 12: {ema_12_str}
   • EMA 26: {ema_26_str}
   • EMA 50: {ema_50_str}
   • Bollinger Upper: {bb_upper_str}
   • Bollinger Middle: {bb_middle_str}
   • Bollinger Lower: {bb_lower_str}
{account_status_str}

📋 YOUR TASK:
Based on the above data, provide a structured trading decision with:
1. **Action**: BUY, SELL, or HOLD
2. **Type**: LONG or SHORT (for BUY actions)
3. **Confidence**: 0-100 (your confidence level)
4. **Reasoning**: Brief explanation (2-3 sentences)
5. **Exit Plan**: Define your take profit, stop loss, and invalidation conditions

⚠️ IMPORTANT NOTES:
   • Historical prices are ordered from OLDEST to NEWEST (last one is current)
   • Consider the trend direction from historical data
   • Set realistic exit targets based on volatility
   • Avoid over-trading - only act on high-confidence setups
   • Consider your current position when making decisions

📤 Response Format (JSON):
{{
  "action": "BUY|SELL|HOLD",
  "type": "LONG|SHORT",
  "confidence": 0-100,
  "reasoning": "Your detailed explanation here",
  "exit_plan": {{
    "profit_target_pct": 2.5,
    "stop_loss_pct": 1.5,
    "invalidation_condition": "RSI drops below 30 or EMA20 breaks down"
  }}
}}"""

            agent = Agent(model=self.llm_client, markdown=False)
            response = await agent.arun(prompt)

            # Parse response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            action = TradeAction(result["action"].lower())
            trade_type = TradeType(result.get("type", "long").lower())
            reasoning = result["reasoning"]
            confidence = float(result.get("confidence", 75.0))
            exit_plan = result.get("exit_plan")

            logger.info(
                f"AI Signal for {indicators.symbol}: {action.value} {trade_type.value} "
                f"(confidence: {confidence}%) - {reasoning[:100]}"
            )
            if exit_plan:
                logger.info(f"Exit Plan: TP={exit_plan.get('profit_target_pct')}% SL={exit_plan.get('stop_loss_pct')}%")

            return (action, trade_type, reasoning, confidence, exit_plan)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"AI signal generation failed: {e}")
            return None
