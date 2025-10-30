"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PortfolioChart from "./portfolio-chart";
import DecisionTimeline from "./decision-timeline";
import TechnicalAnalysis from "./technical-analysis";
import ModelChat from "./model-chat";

interface Trade {
  timestamp: string;
  symbol: string;
  action: string;
  trade_type: string;
  price: number;
  quantity: number;
  notional: number;
  pnl?: number;
}

interface Position {
  timestamp: string;
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  trade_type: string;
  unrealized_pnl: number;
  notional: number;
}

interface InstanceDetailsProps {
  instanceId: string;
  model: string;
}

export default function InstanceDetails({ instanceId, model }: InstanceDetailsProps) {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch trades
        const tradesRes = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/trades`
        );
        const tradesData = await tradesRes.json();
        setTrades(tradesData.trades || []);

        // Fetch positions
        const positionsRes = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/positions`
        );
        const positionsData = await positionsRes.json();
        setPositions(positionsData.positions || []);

        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch instance details:", error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [instanceId]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">
          {model.split("/").pop()} - Detailed View
        </CardTitle>
        <p className="text-sm text-muted-foreground font-mono">
          Instance ID: {instanceId}
        </p>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="modelchat" className="w-full">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="modelchat">💬 Model Chat</TabsTrigger>
            <TabsTrigger value="chart">📈 Chart</TabsTrigger>
            <TabsTrigger value="decisions">🤖 Decisions</TabsTrigger>
            <TabsTrigger value="positions">💼 Positions</TabsTrigger>
            <TabsTrigger value="trades">📋 Trades</TabsTrigger>
            <TabsTrigger value="analysis">📊 Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="modelchat" className="mt-4">
            <ModelChat instanceId={instanceId} />
          </TabsContent>

          <TabsContent value="chart" className="mt-4">
            <PortfolioChart instanceId={instanceId} />
          </TabsContent>

          <TabsContent value="decisions" className="mt-4">
            <DecisionTimeline instanceId={instanceId} />
          </TabsContent>

          <TabsContent value="positions" className="mt-4">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : positions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No open positions
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">Symbol</th>
                      <th className="text-left p-3 font-medium">Type</th>
                      <th className="text-right p-3 font-medium">Quantity</th>
                      <th className="text-right p-3 font-medium">Entry</th>
                      <th className="text-right p-3 font-medium">Current</th>
                      <th className="text-right p-3 font-medium">Notional</th>
                      <th className="text-right p-3 font-medium">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((pos, idx) => (
                      <tr key={idx} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-mono font-bold">{pos.symbol}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              pos.trade_type === "long"
                                ? "bg-green-500/10 text-green-500"
                                : "bg-red-500/10 text-red-500"
                            }`}
                          >
                            {pos.trade_type.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">
                          {pos.quantity.toFixed(4)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(pos.entry_price)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(pos.current_price)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(pos.notional)}
                        </td>
                        <td
                          className={`p-3 text-right font-mono font-bold ${
                            pos.unrealized_pnl >= 0 ? "text-green-500" : "text-red-500"
                          }`}
                        >
                          {formatCurrency(pos.unrealized_pnl)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>

          <TabsContent value="trades" className="mt-4">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : trades.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No trades yet
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">Time</th>
                      <th className="text-left p-3 font-medium">Symbol</th>
                      <th className="text-left p-3 font-medium">Action</th>
                      <th className="text-left p-3 font-medium">Type</th>
                      <th className="text-right p-3 font-medium">Price</th>
                      <th className="text-right p-3 font-medium">Quantity</th>
                      <th className="text-right p-3 font-medium">Notional</th>
                      <th className="text-right p-3 font-medium">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.slice().reverse().map((trade, idx) => (
                      <tr key={idx} className="border-b hover:bg-muted/50">
                        <td className="p-3 text-xs text-muted-foreground">
                          {formatTime(trade.timestamp)}
                        </td>
                        <td className="p-3 font-mono font-bold">{trade.symbol}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              trade.action === "buy"
                                ? "bg-green-500/10 text-green-500"
                                : "bg-red-500/10 text-red-500"
                            }`}
                          >
                            {trade.action.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 text-xs">{trade.trade_type.toUpperCase()}</td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(trade.price)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {trade.quantity.toFixed(4)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(trade.notional)}
                        </td>
                        <td
                          className={`p-3 text-right font-mono ${
                            trade.pnl
                              ? trade.pnl >= 0
                                ? "text-green-500"
                                : "text-red-500"
                              : ""
                          }`}
                        >
                          {trade.pnl ? formatCurrency(trade.pnl) : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>

          <TabsContent value="analysis" className="mt-4">
            <TechnicalAnalysis instanceId={instanceId} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

