"""Trading dashboard API endpoints - Alpha Arena style monitoring"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading", tags=["trading"])


def get_all_trading_instances() -> List[Dict[str, Any]]:
    """
    Get all active trading instances from persisted data file
    This reads the data saved by AutoTradingAgent
    """
    try:
        file_path = "/tmp/valuecell_trading_data.json"
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.debug(f"Trading data file not found: {file_path}")
            return []
        
        # Read the file
        with open(file_path, "r") as f:
            data = json.load(f)
        
        instances_data = []
        for instance in data.get("instances", []):
            instances_data.append({
                "instance_id": instance["instance_id"],
                "session_id": instance["session_id"],
                "data": instance,
            })
        
        return instances_data
    except FileNotFoundError:
        logger.debug("Trading data file not found")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse trading data JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get trading instances: {e}")
        return []


def calculate_sharpe_ratio(instance_data: Dict[str, Any]) -> float:
    """Calculate Sharpe ratio from portfolio history"""
    try:
        portfolio_history = instance_data.get("portfolio_history", [])
        if len(portfolio_history) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(portfolio_history)):
            prev_value = portfolio_history[i-1].get("total_value", 0)
            curr_value = portfolio_history[i].get("total_value", 0)
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)
        
        if not returns:
            return 0.0
        
        # Simple Sharpe ratio (assuming risk-free rate = 0)
        import statistics
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.001
        
        # Annualize (assuming each check is 1 minute)
        sharpe = (mean_return / std_return) * (252 * 24 * 60) ** 0.5 if std_return > 0 else 0
        return round(sharpe, 2)
    except Exception as e:
        logger.error(f"Failed to calculate Sharpe ratio: {e}")
        return 0.0


def calculate_win_rate(instance_data: Dict[str, Any]) -> float:
    """Calculate win rate from trade history"""
    try:
        trade_history = instance_data.get("trade_history", [])
        closed_trades = [t for t in trade_history if t.get("action") == "closed" and t.get("pnl") is not None]
        
        if not closed_trades:
            return 0.0
        
        winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
        win_rate = (winning_trades / len(closed_trades)) * 100
        return round(win_rate, 2)
    except Exception as e:
        logger.error(f"Failed to calculate win rate: {e}")
        return 0.0


def calculate_max_drawdown(instance_data: Dict[str, Any]) -> float:
    """Calculate maximum drawdown from portfolio history"""
    try:
        portfolio_history = instance_data.get("portfolio_history", [])
        if len(portfolio_history) < 2:
            return 0.0
        
        values = [p.get("total_value", 0) for p in portfolio_history]
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return round(max_dd * 100, 2)
    except Exception as e:
        logger.error(f"Failed to calculate max drawdown: {e}")
        return 0.0


@router.get("/dashboard")
async def get_trading_dashboard() -> Dict[str, Any]:
    """
    Get trading dashboard overview
    
    Returns summary statistics for all active trading instances
    """
    try:
        instances = get_all_trading_instances()
        
        if not instances:
            return {
                "total_instances": 0,
                "total_value": 0.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "active_positions": 0,
                "total_trades": 0,
            }
        
        total_value = 0.0
        total_initial = 0.0
        active_positions = 0
        total_trades = 0
        
        for inst in instances:
            data = inst["data"]
            config = data.get("config", {})
            
            # Get latest portfolio value
            portfolio_history = data.get("portfolio_history", [])
            if portfolio_history:
                total_value += portfolio_history[-1].get("total_value", 0)
            
            total_initial += config.get("initial_capital", 0)
            
            # Count positions
            position_history = data.get("position_history", [])
            if position_history:
                active_positions += len(position_history[-1:])  # Latest snapshot
            
            # Count trades
            total_trades += len(data.get("trade_history", []))
        
        total_pnl = total_value - total_initial
        total_pnl_pct = (total_pnl / total_initial * 100) if total_initial > 0 else 0
        
        return {
            "total_instances": len(instances),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "active_positions": active_positions,
            "total_trades": total_trades,
        }
    except Exception as e:
        logger.error(f"Failed to get trading dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_leaderboard() -> List[Dict[str, Any]]:
    """
    Get model leaderboard sorted by performance
    
    Returns ranked list of all trading instances with key metrics
    """
    try:
        instances = get_all_trading_instances()
        
        if not instances:
            return []
        
        leaderboard = []
        
        for inst in instances:
            data = inst["data"]
            config = data.get("config", {})
            
            # Calculate metrics
            initial_capital = config.get("initial_capital", 0)
            portfolio_history = data.get("portfolio_history", [])
            
            if not portfolio_history:
                continue
            
            current_value = portfolio_history[-1].get("total_value", 0)
            pnl = current_value - initial_capital
            pnl_pct = (pnl / initial_capital * 100) if initial_capital > 0 else 0
            
            sharpe_ratio = calculate_sharpe_ratio(data)
            win_rate = calculate_win_rate(data)
            max_drawdown = calculate_max_drawdown(data)
            
            trade_history = data.get("trade_history", [])
            total_trades = len([t for t in trade_history if t.get("action") == "closed"])
            
            leaderboard.append({
                "instance_id": inst["instance_id"],
                "model": config.get("agent_model", "unknown"),
                "symbols": config.get("crypto_symbols", []),
                "initial_capital": round(initial_capital, 2),
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "sharpe_ratio": sharpe_ratio,
                "win_rate": win_rate,
                "max_drawdown": max_drawdown,
                "total_trades": total_trades,
                "created_at": data.get("created_at", ""),
                "active": data.get("active", False),
            })
        
        # Sort by PnL percentage (descending)
        leaderboard.sort(key=lambda x: x["pnl_pct"], reverse=True)
        
        # Add rank
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instance/{instance_id}/chart")
async def get_instance_chart(instance_id: str) -> Dict[str, Any]:
    """
    Get portfolio value chart data for a specific instance
    
    Returns data in the format compatible with frontend mock data
    """
    try:
        instances = get_all_trading_instances()
        
        # Find the instance
        target_instance = None
        for inst in instances:
            if inst["instance_id"] == instance_id:
                target_instance = inst
                break
        
        if not target_instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        data = target_instance["data"]
        config = data.get("config", {})
        portfolio_history = data.get("portfolio_history", [])
        
        # Build chart data in format: [["Time", "Model"], [timestamp, value], ...]
        chart_data = [
            ["Time", config.get("agent_model", "unknown")]
        ]
        
        for snapshot in portfolio_history:
            timestamp = snapshot.get("timestamp", "")
            total_value = snapshot.get("total_value", 0)
            
            # Format timestamp
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp_str = str(timestamp)
            else:
                timestamp_str = ""
            
            chart_data.append([timestamp_str, total_value])
        
        return {
            "title": f"Portfolio Value History - {instance_id[:20]}",
            "data": json.dumps(chart_data),
            "create_time": data.get("created_at", ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get instance chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def get_multi_model_comparison() -> Dict[str, Any]:
    """
    Get multi-model comparison chart data
    
    Returns aligned portfolio values for all active instances
    """
    try:
        instances = get_all_trading_instances()
        
        if not instances:
            return {
                "title": "Portfolio Value History - No Active Instances",
                "data": json.dumps([["Time"]]),
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        
        # Collect all timestamps and values
        model_data = {}
        all_timestamps = set()
        
        for inst in instances:
            data = inst["data"]
            config = data.get("config", {})
            model_name = config.get("agent_model", "unknown")
            
            model_data[model_name] = {}
            
            for snapshot in data.get("portfolio_history", []):
                timestamp = snapshot.get("timestamp", "")
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            dt = timestamp
                        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        timestamp_str = str(timestamp)
                    
                    model_data[model_name][timestamp_str] = snapshot.get("total_value", 0)
                    all_timestamps.add(timestamp_str)
        
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # Build chart data
        model_names = list(model_data.keys())
        chart_data = [["Time"] + model_names]
        
        for timestamp in sorted_timestamps:
            row = [timestamp]
            for model_name in model_names:
                value = model_data[model_name].get(timestamp, None)
                row.append(value)
            chart_data.append(row)
        
        return {
            "title": "Portfolio Value History - Multi Models Comparison",
            "data": json.dumps(chart_data),
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        logger.error(f"Failed to get comparison data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instance/{instance_id}/trades")
async def get_instance_trades(instance_id: str) -> Dict[str, Any]:
    """
    Get trade history for a specific instance
    
    Returns formatted trade data compatible with frontend
    """
    try:
        instances = get_all_trading_instances()
        
        # Find the instance
        target_instance = None
        for inst in instances:
            if inst["instance_id"] == instance_id:
                target_instance = inst
                break
        
        if not target_instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        data = target_instance["data"]
        config = data.get("config", {})
        trade_history = data.get("trade_history", [])
        
        # Build markdown table
        model_name = config.get("agent_model", "unknown")
        trades_md = f"# Trade History - {model_name}\n\n"
        trades_md += f"**Instance ID:** `{instance_id}`\n\n"
        trades_md += "---\n\n"
        
        # Group trades by closed positions
        closed_trades = [t for t in trade_history if t.get("action") == "closed"]
        
        for trade in closed_trades[-20:]:  # Last 20 trades
            symbol = trade.get("symbol", "")
            trade_type = trade.get("trade_type", "long").upper()
            pnl = trade.get("pnl", 0)
            price = trade.get("price", 0)
            quantity = trade.get("quantity", 0)
            timestamp = trade.get("timestamp", "")
            
            # Format timestamp
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamp_str = dt.strftime("%m/%d, %I:%M %p")
                except:
                    timestamp_str = str(timestamp)
            else:
                timestamp_str = ""
            
            # PnL color
            pnl_color = "#16A34A" if pnl > 0 else "#DC2626"
            pnl_sign = "+" if pnl >= 0 else ""
            
            trades_md += f"## 🔷 {model_name} completed a **{trade_type.lower()}** trade on {symbol}!\n"
            trades_md += f"*{timestamp_str}*\n\n"
            trades_md += f"**Price:** ${price:,.2f}  \n"
            trades_md += f"**Quantity:** {quantity:.4f}  \n"
            trades_md += f"**NET P&L:** <span style=\"color: {pnl_color}; font-weight: 600;\">{pnl_sign}${pnl:.2f}</span>\n\n"
            trades_md += "---\n\n"
        
        return {
            "title": f"Trade History - {instance_id[:20]}",
            "data": trades_md,
            "filters": [model_name],
            "table_title": "Completed Trades",
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get instance trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instance/{instance_id}/positions")
async def get_instance_positions(instance_id: str) -> Dict[str, Any]:
    """
    Get current positions for a specific instance
    """
    try:
        instances = get_all_trading_instances()
        
        # Find the instance
        target_instance = None
        for inst in instances:
            if inst["instance_id"] == instance_id:
                target_instance = inst
                break
        
        if not target_instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        data = target_instance["data"]
        config = data.get("config", {})
        position_history = data.get("position_history", [])
        
        # Get latest positions
        current_positions = position_history[-1:] if position_history else []
        
        # Build markdown table
        model_name = config.get("agent_model", "unknown")
        positions_md = f"# Open Positions - {model_name}\n\n"
        positions_md += f"**Instance ID:** `{instance_id}`\n\n"
        
        if not current_positions:
            positions_md += "*No open positions*\n"
        else:
            positions_md += "---\n\n"
            
            for pos in current_positions:
                symbol = pos.get("symbol", "")
                trade_type = pos.get("trade_type", "long").upper()
                entry_price = pos.get("entry_price", 0)
                current_price = pos.get("current_price", 0)
                quantity = pos.get("quantity", 0)
                unrealized_pnl = pos.get("unrealized_pnl", 0)
                timestamp = pos.get("timestamp", "")
                
                # Format timestamp
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            dt = timestamp
                        timestamp_str = dt.strftime("%m/%d, %I:%M %p")
                    except:
                        timestamp_str = str(timestamp)
                else:
                    timestamp_str = ""
                
                # PnL color
                pnl_color = "#16A34A" if unrealized_pnl > 0 else "#DC2626"
                pnl_sign = "+" if unrealized_pnl >= 0 else ""
                
                positions_md += f"## Open Position - {symbol}\n"
                positions_md += f"*Opened: {timestamp_str}*\n\n"
                positions_md += f"**Type:** {trade_type}  \n"
                positions_md += f"**Entry Price:** ${entry_price:,.2f}  \n"
                positions_md += f"**Current Price:** ${current_price:,.2f}  \n"
                positions_md += f"**Quantity:** {quantity:.4f}  \n"
                positions_md += f"**Unrealized P&L:** <span style=\"color: {pnl_color}; font-weight: 600;\">{pnl_sign}${unrealized_pnl:.2f}</span>\n\n"
                positions_md += "---\n\n"
        
        return {
            "title": f"Open Positions - {instance_id[:20]}",
            "data": positions_md,
            "filters": [model_name],
            "table_title": "Open Positions",
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get instance positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instance/{instance_id}/decisions")
async def get_instance_decisions(instance_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    获取实例的 AI 决策历史
    
    Args:
        instance_id: 交易实例 ID
        limit: 返回的决策数量（默认50）
    
    Returns:
        决策历史数据
    """
    try:
        instances = get_all_trading_instances()
        
        # Find the instance
        instance_data = None
        for inst in instances:
            if inst["instance_id"] == instance_id:
                instance_data = inst["data"]
                break
        
        if not instance_data:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
        
        # Get decision history
        decision_history = instance_data.get("decision_history", [])
        
        # Apply limit and reverse to show latest first
        limited_history = decision_history[-limit:][::-1] if limit > 0 else decision_history[::-1]
        
        return {
            "instance_id": instance_id,
            "total_decisions": len(decision_history),
            "returned_decisions": len(limited_history),
            "decisions": limited_history,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get instance decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instance/{instance_id}/decision/{check_number}")
async def get_decision_detail(instance_id: str, check_number: int) -> Dict[str, Any]:
    """
    获取特定检查的详细决策数据
    
    Args:
        instance_id: 交易实例 ID
        check_number: 检查编号
    
    Returns:
        详细决策数据
    """
    try:
        instances = get_all_trading_instances()
        
        # Find the instance
        instance_data = None
        for inst in instances:
            if inst["instance_id"] == instance_id:
                instance_data = inst["data"]
                break
        
        if not instance_data:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
        
        # Find the specific decision
        decision_history = instance_data.get("decision_history", [])
        decision = None
        for d in decision_history:
            if d.get("check_number") == check_number:
                decision = d
                break
        
        if not decision:
            raise HTTPException(
                status_code=404, 
                detail=f"Decision with check_number {check_number} not found for instance {instance_id}"
            )
        
        return {
            "instance_id": instance_id,
            "decision": decision,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decision detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-prices")
async def get_market_prices() -> Dict[str, Any]:
    """
    获取实时加密货币价格（参考 nof1.ai）
    支持的币种：BTC, ETH, SOL, BNB, DOGE, XRP
    使用 Binance API，失败时降级到 yfinance
    """
    try:
        from valuecell.agents.auto_trading_agent.binance_data import BinanceMarketDataProvider
        
        symbols = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]
        prices = {}
        binance_provider = BinanceMarketDataProvider()
        
        for base_symbol in symbols:
            symbol = f"{base_symbol}-USD"  # Convert to standard format
            try:
                # Try Binance first
                ticker_data = binance_provider.get_24h_ticker(symbol)
                if ticker_data:
                    prices[base_symbol] = {
                        "price": ticker_data["price"],
                        "change_pct": ticker_data["price_change_percent"],
                        "symbol": base_symbol,
                    }
                    continue
            except Exception as e:
                logger.debug(f"Binance failed for {base_symbol}, trying yfinance: {e}")
            
            # Fallback to yfinance
            try:
                import yfinance as yf
                yf_symbol = f"{base_symbol}-USD"
                ticker = yf.Ticker(yf_symbol)
                data = ticker.history(period="1d", interval="1m")
                if not data.empty:
                    price = float(data["Close"].iloc[-1])
                    # Get 24h change
                    if len(data) >= 2:
                        prev_price = float(data["Close"].iloc[-2])
                        change_pct = ((price - prev_price) / prev_price) * 100
                    else:
                        change_pct = 0.0
                    
                    prices[base_symbol] = {
                        "price": price,
                        "change_pct": change_pct,
                        "symbol": base_symbol,
                    }
                else:
                    prices[base_symbol] = {
                        "price": 0,
                        "change_pct": 0,
                        "symbol": base_symbol,
                    }
            except Exception as e:
                logger.warning(f"Failed to get price for {base_symbol}: {e}")
                prices[base_symbol] = {
                    "price": 0,
                    "change_pct": 0,
                    "symbol": base_symbol,
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "prices": prices,
        }
    except Exception as e:
        logger.error(f"Failed to get market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

