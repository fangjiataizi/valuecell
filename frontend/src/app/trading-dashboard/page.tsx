"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Activity, DollarSign } from "lucide-react";
import InstanceDetails from "./components/instance-details";
import MarketPrices from "./components/market-prices";
import ConnectionStatus from "./components/connection-status";

interface DashboardData {
  total_instances: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  active_positions: number;
  total_trades: number;
}

interface LeaderboardEntry {
  rank: number;
  instance_id: string;
  model: string;
  symbols: string[];
  pnl: number;
  pnl_pct: number;
  sharpe_ratio: number;
  win_rate: number;
  max_drawdown: number;
  total_trades: number;
  current_value: number;
  initial_capital: number;
  active: boolean;
}

export default function TradingDashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      // Fetch dashboard data
      const dashboardRes = await fetch("http://localhost:8001/api/v1/trading/dashboard");
      const dashboardData = await dashboardRes.json();
      setDashboard(dashboardData);

      // Fetch leaderboard data
      const leaderboardRes = await fetch("http://localhost:8001/api/v1/trading/leaderboard");
      const leaderboardData = await leaderboardRes.json();
      setLeaderboard(leaderboardData);

      setLastUpdate(new Date());
      setError(null);
      
      // Auto-select first instance if none selected
      if (!selectedInstance && leaderboardData.length > 0) {
        setSelectedInstance(leaderboardData[0].instance_id);
      }
    } catch (err) {
      setError("Failed to fetch data. Make sure the backend is running.");
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading Trading Dashboard...</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">Alpha Arena Trading Dashboard</h1>
            <p className="text-muted-foreground">
              Real-time AI trading monitoring inspired by nof1.ai
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground mb-2">
              <p>Last updated: {lastUpdate.toLocaleTimeString()}</p>
              <p className="text-xs mt-1">Auto-refresh every 10s</p>
            </div>
            <ConnectionStatus />
          </div>
        </div>
      </div>

      {/* Real-time Market Prices (参考 nof1.ai) */}
      <div className="mb-6">
        <MarketPrices />
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
          <p className="font-medium">⚠️ Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Total Account Value (参考 nof1.ai) */}
      {dashboard && (
        <Card className="mb-6 bg-primary/5 border-primary/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-2 uppercase tracking-wider">
                  Total Account Value
                </p>
                <p className="text-5xl font-bold">{formatCurrency(dashboard.total_value)}</p>
                <div className="flex items-center gap-4 mt-4">
                  <div>
                    <span className="text-xs text-muted-foreground">P&L: </span>
                    <span
                      className={`text-lg font-bold ${
                        dashboard.total_pnl >= 0 ? "text-green-500" : "text-red-500"
                      }`}
                    >
                      {dashboard.total_pnl >= 0 ? "+" : ""}
                      {formatCurrency(dashboard.total_pnl)}
                    </span>
                    <span
                      className={`ml-2 text-sm ${
                        dashboard.total_pnl_pct >= 0 ? "text-green-500" : "text-red-500"
                      }`}
                    >
                      ({formatPercent(dashboard.total_pnl_pct)})
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {dashboard.total_instances} Model{dashboard.total_instances !== 1 ? "s" : ""}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Cards */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Instances</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboard.total_instances}</div>
              <p className="text-xs text-muted-foreground mt-1">
                AI trading models
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Positions</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboard.active_positions}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {dashboard.total_trades} total trades
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Leaderboard */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-2xl">🏆 Model Leaderboard</CardTitle>
          <p className="text-sm text-muted-foreground">
            Ranked by P&L performance
          </p>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No active trading instances</p>
              <p className="text-sm mt-2">
                Create a trading instance in the AutoTradingAgent to see it here
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-medium">Rank</th>
                    <th className="text-left p-3 font-medium">Model</th>
                    <th className="text-left p-3 font-medium">Symbols</th>
                    <th className="text-right p-3 font-medium">Portfolio</th>
                    <th className="text-right p-3 font-medium">P&L</th>
                    <th className="text-right p-3 font-medium">Sharpe</th>
                    <th className="text-right p-3 font-medium">Win Rate</th>
                    <th className="text-right p-3 font-medium">Max DD</th>
                    <th className="text-right p-3 font-medium">Trades</th>
                    <th className="text-center p-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((entry) => (
                    <tr
                      key={entry.instance_id}
                      onClick={() => setSelectedInstance(entry.instance_id)}
                      className={`border-b hover:bg-muted/50 transition-colors cursor-pointer ${
                        selectedInstance === entry.instance_id ? "bg-primary/10" : ""
                      }`}
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {entry.rank === 1 && <span className="text-xl">🥇</span>}
                          {entry.rank === 2 && <span className="text-xl">🥈</span>}
                          {entry.rank === 3 && <span className="text-xl">🥉</span>}
                          <span className="font-mono">#{entry.rank}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div>
                          <div className="font-medium text-sm">{entry.model.split("/").pop()}</div>
                          <div className="text-xs text-muted-foreground font-mono">
                            {entry.instance_id.slice(0, 20)}...
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex gap-1 flex-wrap">
                          {entry.symbols.map((symbol) => (
                            <span
                              key={symbol}
                              className="px-2 py-1 bg-primary/10 text-primary rounded text-xs font-mono"
                            >
                              {symbol}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <div className="font-medium">{formatCurrency(entry.current_value)}</div>
                        <div className="text-xs text-muted-foreground">
                          / {formatCurrency(entry.initial_capital)}
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <div className={`font-bold ${entry.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                          {formatCurrency(entry.pnl)}
                        </div>
                        <div className={`text-xs ${entry.pnl_pct >= 0 ? "text-green-500" : "text-red-500"}`}>
                          {formatPercent(entry.pnl_pct)}
                        </div>
                      </td>
                      <td className="p-3 text-right font-mono">{entry.sharpe_ratio.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono">{entry.win_rate.toFixed(1)}%</td>
                      <td className="p-3 text-right font-mono text-red-500">
                        {entry.max_drawdown.toFixed(2)}%
                      </td>
                      <td className="p-3 text-right font-mono">{entry.total_trades}</td>
                      <td className="p-3 text-center">
                        {entry.active ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-500 rounded text-xs">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-500/10 text-gray-500 rounded text-xs">
                            Stopped
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instance Details */}
      {selectedInstance && (
        <div className="mb-6">
          {(() => {
            const instance = leaderboard.find((e) => e.instance_id === selectedInstance);
            return instance ? (
              <InstanceDetails instanceId={instance.instance_id} model={instance.model} />
            ) : null;
          })()}
        </div>
      )}

      {/* Info Footer */}
      <div className="text-center text-sm text-muted-foreground mt-8">
        <p>
          💡 Trading Dashboard inspired by{" "}
          <a
            href="https://nof1.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            nof1.ai Alpha Arena
          </a>
        </p>
        <p className="mt-2">
          API Endpoints: Dashboard • Leaderboard • Charts • Trades • Positions
        </p>
      </div>
    </div>
  );
}

