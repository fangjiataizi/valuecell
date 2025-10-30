"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";

interface MarketPrice {
  price: number;
  change_pct: number;
  symbol: string;
}

interface MarketPricesData {
  timestamp: string;
  prices: Record<string, MarketPrice>;
}

export default function MarketPrices() {
  const [marketData, setMarketData] = useState<MarketPricesData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const response = await fetch("http://localhost:8001/api/v1/trading/market-prices");
        const data = await response.json();
        setMarketData(data);
      } catch (error) {
        console.error("Failed to fetch market prices:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(price);
    } else if (price >= 1) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(price);
    } else {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 4,
        maximumFractionDigits: 4,
      }).format(price);
    }
  };

  const symbols = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"];

  if (loading) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
            <span className="text-sm">Loading prices...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-4 overflow-x-auto">
          {symbols.map((symbol) => {
            const priceData = marketData?.prices[symbol];
            if (!priceData) return null;

            const isPositive = priceData.change_pct >= 0;
            const ChangeIcon = isPositive ? TrendingUp : TrendingDown;

            return (
              <div
                key={symbol}
                className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-lg min-w-[140px]"
              >
                <div className="flex-shrink-0">
                  <span className="font-bold text-sm">{symbol}</span>
                </div>
                <div className="flex-1 text-right">
                  <div className="font-mono text-sm font-medium">
                    {formatPrice(priceData.price)}
                  </div>
                  <div
                    className={`flex items-center gap-1 text-xs ${
                      isPositive ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    <ChangeIcon className="h-3 w-3" />
                    <span>
                      {isPositive ? "+" : ""}
                      {priceData.change_pct.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

