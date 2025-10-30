"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import TechnicalIndicatorsChart from "./technical-indicators-chart";

interface Decision {
  timestamp: string;
  check_number: number;
  symbol_decisions: Array<{
    symbol: string;
    market_data: {
      price: number;
      volume: number;
      historical_prices?: number[];
      historical_volumes?: number[];
    };
    technical_indicators: {
      macd?: number;
      macd_signal?: number;
      macd_histogram?: number;
      rsi?: number;
      ema_12?: number;
      ema_26?: number;
      ema_50?: number;
      bb_upper?: number;
      bb_middle?: number;
      bb_lower?: number;
    };
  }>;
}

interface TechnicalAnalysisProps {
  instanceId: string;
}

export default function TechnicalAnalysis({ instanceId }: TechnicalAnalysisProps) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const response = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/decisions?limit=10`
        );
        const data = await response.json();
        setDecisions(data.decisions || []);
        
        // Select latest decision and first symbol by default
        if (data.decisions && data.decisions.length > 0) {
          const latest = data.decisions[0];
          setSelectedDecision(latest);
          if (latest.symbol_decisions.length > 0) {
            setSelectedSymbol(latest.symbol_decisions[0].symbol);
          }
        }
      } catch (error) {
        console.error("Failed to fetch decisions:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDecisions();
    const interval = setInterval(fetchDecisions, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [instanceId]);

  const selectedSymbolDecision = selectedDecision?.symbol_decisions.find(
    (sd) => sd.symbol === selectedSymbol
  );

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>加载技术分析数据...</p>
      </div>
    );
  }

  if (!selectedDecision || !selectedSymbolDecision) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">暂无技术分析数据</p>
        <p className="text-sm mt-2">等待 AI 开始分析...</p>
      </div>
    );
  }

  const symbols = selectedDecision.symbol_decisions.map((sd) => sd.symbol);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">技术指标分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">决策选择</p>
              <Select
                value={selectedDecision.check_number.toString()}
                onValueChange={(value) => {
                  const decision = decisions.find(
                    (d) => d.check_number.toString() === value
                  );
                  if (decision) {
                    setSelectedDecision(decision);
                    if (decision.symbol_decisions.length > 0) {
                      setSelectedSymbol(decision.symbol_decisions[0].symbol);
                    }
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {decisions.map((d) => (
                    <SelectItem key={d.check_number} value={d.check_number.toString()}>
                      检查 #{d.check_number} - {new Date(d.timestamp).toLocaleString("zh-CN")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">交易符号</p>
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {symbols.map((symbol) => (
                    <SelectItem key={symbol} value={symbol}>
                      {symbol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Technical Indicators Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {selectedSymbol} - 技术指标
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            检查 #{selectedDecision.check_number} -{" "}
            {new Date(selectedDecision.timestamp).toLocaleString("zh-CN")}
          </p>
        </CardHeader>
        <CardContent>
          <TechnicalIndicatorsChart
            symbol={selectedSymbol}
            price={selectedSymbolDecision.market_data.price}
            indicators={selectedSymbolDecision.technical_indicators}
            historicalPrices={selectedSymbolDecision.market_data.historical_prices}
            historicalVolumes={selectedSymbolDecision.market_data.historical_volumes}
          />
        </CardContent>
      </Card>

      {/* Indicators Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">指标摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">当前价格</p>
              <p className="text-lg font-bold">
                ${selectedSymbolDecision.market_data.price.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">成交量</p>
              <p className="text-lg font-bold">
                {selectedSymbolDecision.market_data.volume.toLocaleString()}
              </p>
            </div>
            {selectedSymbolDecision.technical_indicators.rsi !== undefined && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">RSI</p>
                <p
                  className={`text-lg font-bold ${
                    selectedSymbolDecision.technical_indicators.rsi >= 70
                      ? "text-red-500"
                      : selectedSymbolDecision.technical_indicators.rsi <= 30
                      ? "text-green-500"
                      : "text-yellow-500"
                  }`}
                >
                  {selectedSymbolDecision.technical_indicators.rsi.toFixed(2)}
                </p>
              </div>
            )}
            {selectedSymbolDecision.technical_indicators.macd !== undefined && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">MACD</p>
                <p className="text-lg font-bold">
                  {selectedSymbolDecision.technical_indicators.macd.toFixed(4)}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

