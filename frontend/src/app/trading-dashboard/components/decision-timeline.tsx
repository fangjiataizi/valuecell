"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Brain, Activity } from "lucide-react";

interface Decision {
  timestamp: string;
  check_number: number;
  symbol_decisions: Array<{
    symbol: string;
    market_data: {
      price: number;
      volume: number;
    };
    technical_signal: {
      action: string;
      trade_type: string;
    };
    ai_analysis?: {
      action: string;
      trade_type: string;
      reasoning: string;
      confidence: number;
      exit_plan?: {
        profit_target_pct?: number;
        stop_loss_pct?: number;
        invalidation_condition?: string;
      };
    };
    current_position?: {
      entry_price: number;
      quantity: number;
      trade_type: string;
      unrealized_pnl: number;
    };
  }>;
  portfolio_decision: {
    reasoning: string;
    trades_to_execute: Array<{
      symbol: string;
      action: string;
      trade_type: string;
    }>;
    trades_executed: Array<{
      symbol: string;
      action: string;
      trade_type: string;
      executed: boolean;
      execution_price?: number;
    }>;
  };
  portfolio_state: {
    total_value: number;
    available_cash: number;
    positions_count: number;
    total_pnl: number;
  };
}

interface DecisionTimelineProps {
  instanceId: string;
}

export default function DecisionTimeline({ instanceId }: DecisionTimelineProps) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const response = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/decisions?limit=50`
        );
        const data = await response.json();
        setDecisions(data.decisions || []);
        
        // Select first decision by default
        if (data.decisions && data.decisions.length > 0 && !selectedDecision) {
          setSelectedDecision(data.decisions[0]);
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

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getActionIcon = (action: string) => {
    switch (action?.toLowerCase()) {
      case "buy":
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case "sell":
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action?.toLowerCase()) {
      case "buy":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      case "sell":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Activity className="h-8 w-8 mx-auto mb-4 animate-spin" />
        <p>加载决策历史...</p>
      </div>
    );
  }

  if (decisions.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">暂无决策历史</p>
        <p className="text-sm mt-2">等待 AI 开始决策...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Timeline List */}
      <div className="lg:col-span-1">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">决策时间线</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {decisions.map((decision, idx) => (
                <div
                  key={decision.check_number}
                  onClick={() => setSelectedDecision(decision)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDecision?.check_number === decision.check_number
                      ? "bg-primary/10 border-primary"
                      : "hover:bg-muted/50 border-border"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        #{decision.check_number}
                      </span>
                      {decision.portfolio_decision.trades_executed.length > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {decision.portfolio_decision.trades_executed.length} 交易
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(decision.timestamp)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {decision.portfolio_decision.trades_to_execute.map((trade, i) => (
                      <div
                        key={i}
                        className={`flex items-center gap-1 px-2 py-1 rounded text-xs border ${getActionColor(
                          trade.action
                        )}`}
                      >
                        {getActionIcon(trade.action)}
                        <span className="font-medium">{trade.symbol}</span>
                      </div>
                    ))}
                    {decision.portfolio_decision.trades_to_execute.length === 0 && (
                      <span className="text-xs text-muted-foreground">HOLD</span>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    P&L:{" "}
                    <span
                      className={
                        decision.portfolio_state.total_pnl >= 0
                          ? "text-green-500"
                          : "text-red-500"
                      }
                    >
                      {decision.portfolio_state.total_pnl >= 0 ? "+" : ""}
                      ${decision.portfolio_state.total_pnl.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Decision Detail */}
      <div className="lg:col-span-2">
        {selectedDecision ? (
          <DecisionDetail decision={selectedDecision} />
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <p>选择一个决策查看详情</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function DecisionDetail({ decision }: { decision: Decision }) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className="space-y-4">
      {/* Portfolio Decision */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="h-5 w-5" />
            组合决策 #{decision.check_number}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {formatTime(decision.timestamp)}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Portfolio State */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">总价值</p>
              <p className="text-lg font-bold">
                ${decision.portfolio_state.total_value.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">可用资金</p>
              <p className="text-lg font-bold">
                ${decision.portfolio_state.available_cash.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">持仓数</p>
              <p className="text-lg font-bold">{decision.portfolio_state.positions_count}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">总 P&L</p>
              <p
                className={`text-lg font-bold ${
                  decision.portfolio_state.total_pnl >= 0
                    ? "text-green-500"
                    : "text-red-500"
                }`}
              >
                {decision.portfolio_state.total_pnl >= 0 ? "+" : ""}
                ${decision.portfolio_state.total_pnl.toFixed(2)}
              </p>
            </div>
          </div>

          {/* AI Reasoning */}
          <div>
            <p className="text-sm font-medium mb-2">🤖 AI 推理过程</p>
            <div className="bg-muted/50 p-4 rounded-lg">
              <p className="text-sm whitespace-pre-wrap">
                {decision.portfolio_decision.reasoning}
              </p>
            </div>
          </div>

          {/* Executed Trades */}
          {decision.portfolio_decision.trades_executed.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">✅ 执行的交易</p>
              <div className="space-y-2">
                {decision.portfolio_decision.trades_executed.map((trade, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          trade.action.toLowerCase() === "buy"
                            ? "bg-green-500"
                            : "bg-red-500"
                        }
                      >
                        {trade.action.toUpperCase()}
                      </Badge>
                      <span className="font-medium">{trade.symbol}</span>
                      <span className="text-xs text-muted-foreground">
                        {trade.trade_type.toUpperCase()}
                      </span>
                    </div>
                    {trade.execution_price && (
                      <span className="font-mono text-sm">
                        @ ${trade.execution_price.toFixed(2)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Symbol Decisions */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">资产分析</h3>
        {decision.symbol_decisions.map((symbolDecision, idx) => (
          <SymbolDecisionCard
            key={idx}
            symbolDecision={symbolDecision}
          />
        ))}
      </div>
    </div>
  );
}

function SymbolDecisionCard({
  symbolDecision,
}: {
  symbolDecision: Decision["symbol_decisions"][0];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          <span>{symbolDecision.symbol}</span>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={
                symbolDecision.technical_signal.action.toLowerCase() === "buy"
                  ? "border-green-500 text-green-500"
                  : symbolDecision.technical_signal.action.toLowerCase() === "sell"
                  ? "border-red-500 text-red-500"
                  : "border-gray-500 text-gray-500"
              }
            >
              技术: {symbolDecision.technical_signal.action.toUpperCase()}
            </Badge>
            {symbolDecision.ai_analysis && (
              <Badge
                className={
                  symbolDecision.ai_analysis.action.toLowerCase() === "buy"
                    ? "bg-green-500"
                    : symbolDecision.ai_analysis.action.toLowerCase() === "sell"
                    ? "bg-red-500"
                    : "bg-gray-500"
                }
              >
                AI: {symbolDecision.ai_analysis.action.toUpperCase()}
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Market Data */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">价格</p>
            <p className="text-lg font-bold">
              ${symbolDecision.market_data.price.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">成交量</p>
            <p className="text-lg font-bold">
              {symbolDecision.market_data.volume.toLocaleString()}
            </p>
          </div>
        </div>

        {/* AI Analysis */}
        {symbolDecision.ai_analysis && (
          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground mb-1">AI 信心度</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${symbolDecision.ai_analysis.confidence}%` }}
                  />
                </div>
                <span className="text-sm font-medium">
                  {symbolDecision.ai_analysis.confidence.toFixed(0)}%
                </span>
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground mb-1">🤖 AI 推理</p>
              <div className="bg-muted/50 p-3 rounded-lg">
                <p className="text-sm whitespace-pre-wrap">
                  {symbolDecision.ai_analysis.reasoning}
                </p>
              </div>
            </div>

            {symbolDecision.ai_analysis.exit_plan && (
              <div>
                <p className="text-xs text-muted-foreground mb-2">📋 退出计划</p>
                <div className="grid grid-cols-3 gap-2">
                  {symbolDecision.ai_analysis.exit_plan.profit_target_pct && (
                    <div className="bg-green-500/10 p-2 rounded">
                      <p className="text-xs text-muted-foreground">止盈</p>
                      <p className="text-sm font-bold text-green-500">
                        +{symbolDecision.ai_analysis.exit_plan.profit_target_pct}%
                      </p>
                    </div>
                  )}
                  {symbolDecision.ai_analysis.exit_plan.stop_loss_pct && (
                    <div className="bg-red-500/10 p-2 rounded">
                      <p className="text-xs text-muted-foreground">止损</p>
                      <p className="text-sm font-bold text-red-500">
                        -{symbolDecision.ai_analysis.exit_plan.stop_loss_pct}%
                      </p>
                    </div>
                  )}
                  {symbolDecision.ai_analysis.exit_plan.invalidation_condition && (
                    <div className="bg-orange-500/10 p-2 rounded col-span-3">
                      <p className="text-xs text-muted-foreground">失效条件</p>
                      <p className="text-sm">
                        {symbolDecision.ai_analysis.exit_plan.invalidation_condition}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Current Position */}
        {symbolDecision.current_position && (
          <div className="bg-blue-500/10 p-3 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">当前持仓</p>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">
                  {symbolDecision.current_position.trade_type.toUpperCase()}{" "}
                  {symbolDecision.current_position.quantity.toFixed(4)}
                </p>
                <p className="text-xs text-muted-foreground">
                  入场: ${symbolDecision.current_position.entry_price.toFixed(2)}
                </p>
              </div>
              <div className="text-right">
                <p
                  className={`font-bold ${
                    symbolDecision.current_position.unrealized_pnl >= 0
                      ? "text-green-500"
                      : "text-red-500"
                  }`}
                >
                  {symbolDecision.current_position.unrealized_pnl >= 0 ? "+" : ""}
                  ${symbolDecision.current_position.unrealized_pnl.toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground">
                  ${symbolDecision.current_position.current_price.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

