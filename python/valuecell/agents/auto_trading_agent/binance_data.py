"""Binance API market data provider - for real-time cryptocurrency prices and historical data"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import TechnicalIndicators

logger = logging.getLogger(__name__)

# Binance API 速率限制
# 公开 API: 每分钟 1200 次请求，每秒 10 次请求
BINANCE_RATE_LIMIT = {
    "requests_per_minute": 1200,
    "requests_per_second": 10,
}

# Binance API Base URL
BINANCE_API_BASE = "https://api.binance.com"


class BinanceMarketDataProvider:
    """
    Binance API market data provider
    
    Features:
    - Real-time price fetching
    - Historical klines (candlestick) data
    - 24h ticker statistics
    - Automatic rate limiting
    - Symbol normalization
    """

    def __init__(self, api_base: str = BINANCE_API_BASE):
        """
        Initialize Binance market data provider
        
        Args:
            api_base: Binance API base URL (default: production API)
        """
        self.api_base = api_base.rstrip("/")
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rate limiting tracking (simple in-memory counter)
        self._request_times: List[float] = []
        
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Binance format
        
        Args:
            symbol: Original symbol (e.g., "BTC-USD", "BTCUSDT")
            
        Returns:
            Binance format (e.g., "BTCUSDT")
        """
        # Remove common suffixes
        symbol = symbol.replace("-USD", "").replace("-USDT", "").replace("USDT", "")
        # Add USDT suffix for Binance
        return f"{symbol}USDT"
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        import time
        now = time.time()
        
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        # Check per-minute limit
        if len(self._request_times) >= BINANCE_RATE_LIMIT["requests_per_minute"]:
            sleep_time = 60 - (now - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        # Check per-second limit (last second)
        recent_requests = [t for t in self._request_times if now - t < 1]
        if len(recent_requests) >= BINANCE_RATE_LIMIT["requests_per_second"]:
            sleep_time = 1.1 - (now - recent_requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Record this request
        self._request_times.append(now)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Binance API
        
        Args:
            endpoint: API endpoint (e.g., "/api/v3/ticker/price")
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        self._check_rate_limit()
        
        url = f"{self.api_base}{endpoint}"
        if params:
            url += "?" + urlencode(params)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error(f"Binance rate limit exceeded: {e}")
                raise Exception("Binance API rate limit exceeded")
            raise
        except Exception as e:
            logger.error(f"Binance API request failed: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            
        Returns:
            Current price or None if failed
        """
        try:
            binance_symbol = self.normalize_symbol(symbol)
            endpoint = "/api/v3/ticker/price"
            params = {"symbol": binance_symbol}
            
            data = self._make_request(endpoint, params)
            return float(data["price"])
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Get historical klines (candlestick) data
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 15m, 1h, 1d, etc.)
            limit: Number of klines to return (max 1000)
            start_time: Start time in milliseconds (optional)
            end_time: End time in milliseconds (optional)
            
        Returns:
            DataFrame with columns: [open, high, low, close, volume, ...]
            or None if failed
        """
        try:
            binance_symbol = self.normalize_symbol(symbol)
            endpoint = "/api/v3/klines"
            
            params = {
                "symbol": binance_symbol,
                "interval": interval,
                "limit": min(limit, 1000),  # Binance max is 1000
            }
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
            
            data = self._make_request(endpoint, params)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                data,
                columns=[
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trades",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignore",
                ],
            )
            
            # Convert to numeric
            numeric_cols = ["open", "high", "low", "close", "volume"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Set index to datetime
            df.index = pd.to_datetime(df["open_time"], unit="ms")
            df = df[numeric_cols]  # Keep only price/volume columns
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            return None
    
    def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get 24-hour ticker statistics
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with 24h stats or None if failed
        """
        try:
            binance_symbol = self.normalize_symbol(symbol)
            endpoint = "/api/v3/ticker/24hr"
            params = {"symbol": binance_symbol}
            
            data = self._make_request(endpoint, params)
            
            return {
                "symbol": binance_symbol,
                "price": float(data["lastPrice"]),
                "open": float(data["openPrice"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
                "volume": float(data["volume"]),
                "quote_volume": float(data["quoteVolume"]),
                "price_change": float(data["priceChange"]),
                "price_change_percent": float(data["priceChangePercent"]),
            }
        except Exception as e:
            logger.error(f"Failed to get 24h ticker for {symbol}: {e}")
            return None

