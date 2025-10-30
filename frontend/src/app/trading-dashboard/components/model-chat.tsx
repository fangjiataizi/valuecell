"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, Brain, Activity } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

interface Decision {
  timestamp: string;
  check_number: number;
  symbol_decisions: Array<{
    symbol: string;
    market_data: {
      price: number;
    };
    ai_analysis?: {
      action: string;
      reasoning: string;
      confidence: number;
    };
  }>;
  portfolio_decision: {
    reasoning: string;
    trades_executed: Array<{
      symbol: string;
      action: string;
      executed: boolean;
    }>;
  };
  portfolio_state: {
    total_value: number;
    total_pnl: number;
  };
}

interface ModelChatProps {
  instanceId: string;
}

export default function ModelChat({ instanceId }: ModelChatProps) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedDecisions, setExpandedDecisions] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const response = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/decisions?limit=30`
        );
        const data = await response.json();
        setDecisions(data.decisions || []);
        
        // Auto-expand latest decision
        if (data.decisions && data.decisions.length > 0 && expandedDecisions.size === 0) {
          setExpandedDecisions(new Set([data.decisions[0].check_number]));
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

  const toggleDecision = (checkNumber: number) => {
    const newExpanded = new Set(expandedDecisions);
    if (newExpanded.has(checkNumber)) {
      newExpanded.delete(checkNumber);
    } else {
      newExpanded.add(checkNumber);
    }
    setExpandedDecisions(newExpanded);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Activity className="h-8 w-8 mx-auto mb-4 animate-spin" />
        <p>加载模型对话...</p>
      </div>
    );
  }

  if (decisions.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">暂无决策记录</p>
        <p className="text-sm mt-2">等待 AI 开始决策...</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {decisions.map((decision) => {
        const isExpanded = expandedDecisions.has(decision.check_number);
        const hasTrades = decision.portfolio_decision.trades_executed.length > 0;
        const pnl = decision.portfolio_state.total_pnl;
        
        return (
          <Collapsible
            key={decision.check_number}
            open={isExpanded}
            onOpenChange={() => toggleDecision(decision.check_number)}
          >
            <Card className="hover:bg-muted/50 transition-colors">
              <CollapsibleTrigger className="w-full">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-primary" />
                        <span className="font-mono text-sm">#{decision.check_number}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatTime(decision.timestamp)}
                        </span>
                      </div>
                      {hasTrades && (
                        <Badge variant="outline" className="text-xs">
                          {decision.portfolio_decision.trades_executed.length} 交易
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground">P&L</div>
                        <div
                          className={`text-sm font-bold ${
                            pnl >= 0 ? "text-green-500" : "text-red-500"
                          }`}
                        >
                          {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
                        </div>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <CardContent className="pt-0 space-y-4">
                  {/* Portfolio Decision Reasoning */}
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">组合决策</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap text-muted-foreground">
                      {decision.portfolio_decision.reasoning}
                    </p>
                  </div>

                  {/* Executed Trades */}
                  {hasTrades && (
                    <div>
                      <div className="text-sm font-medium mb-2">执行的交易</div>
                      <div className="space-y-2">
                        {decision.portfolio_decision.trades_executed.map((trade, i) => (
                          <div
                            key={i}
                            className={`flex items-center gap-2 p-2 rounded ${
                              trade.action.toLowerCase() === "buy"
                                ? "bg-green-500/10"
                                : "bg-red-500/10"
                            }`}
                          >
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
                            <span className="text-xs text-muted-foreground ml-auto">
                              {trade.executed ? "✅ 已执行" : "❌ 未执行"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Symbol Decisions */}
                  {decision.symbol_decisions.length > 0 && (
                    <div>
                      <div className="text-sm font-medium mb-2">资产分析</div>
                      <div className="space-y-2">
                        {decision.symbol_decisions.map((sd, idx) => {
                          if (!sd.ai_analysis) return null;
                          
                          return (
                            <div key={idx} className="border rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{sd.symbol}</span>
                                <div className="flex items-center gap-2">
                                  <Badge
                                    className={
                                      sd.ai_analysis.action.toLowerCase() === "buy"
                                        ? "bg-green-500"
                                        : sd.ai_analysis.action.toLowerCase() === "sell"
                                        ? "bg-red-500"
                                        : "bg-gray-500"
                                    }
                                  >
                                    {sd.ai_analysis.action.toUpperCase()}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    信心度: {sd.ai_analysis.confidence.toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                {sd.ai_analysis.reasoning}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Portfolio State */}
                  <div className="grid grid-cols-4 gap-2 pt-2 border-t">
                    <div>
                      <div className="text-xs text-muted-foreground">总价值</div>
                      <div className="text-sm font-medium">
                        ${decision.portfolio_state.total_value.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">持仓数</div>
                      <div className="text-sm font-medium">
                        {decision.portfolio_state.total_pnl >= 0 ? "+" : ""}
                        {decision.symbol_decisions.length}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">分析资产</div>
                      <div className="text-sm font-medium">
                        {decision.symbol_decisions.length}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">时间</div>
                      <div className="text-sm font-medium">
                        {new Date(decision.timestamp).toLocaleTimeString("zh-CN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        );
      })}
    </div>
  );
}

