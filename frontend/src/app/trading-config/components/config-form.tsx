"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X, Save, XCircle } from "lucide-react";

interface TradingConfig {
  id?: string;
  name: string;
  crypto_symbols: string[];
  initial_capital: number;
  check_interval: number;
  use_ai_signals: boolean;
  agent_models: string[];
  risk_per_trade: number;
  max_positions: number;
}

interface TradingConfigFormProps {
  availableModels: Array<{
    id: string;
    name: string;
    provider: string;
  }>;
  editingConfig?: TradingConfig | null;
  onSave: () => void;
  onCancel: () => void;
}

const CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "ADA", "AVAX", "DOT", "MATIC"];

export default function TradingConfigForm({
  availableModels,
  editingConfig,
  onSave,
  onCancel,
}: TradingConfigFormProps) {
  const [formData, setFormData] = useState<TradingConfig>({
    name: "",
    crypto_symbols: [],
    initial_capital: 10000,
    check_interval: 60,
    use_ai_signals: true,
    agent_models: [],
    risk_per_trade: 0.02,
    max_positions: 3,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingConfig) {
      setFormData(editingConfig);
    }
  }, [editingConfig]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const url = editingConfig
        ? `http://localhost:8001/api/v1/trading/config/${editingConfig.id}`
        : "http://localhost:8001/api/v1/trading/config/create";

      const method = editingConfig ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "保存失败");
      }

      onSave();
    } catch (err: any) {
      setError(err.message || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  const toggleSymbol = (symbol: string) => {
    const symbols = formData.crypto_symbols.includes(symbol)
      ? formData.crypto_symbols.filter((s) => s !== symbol)
      : [...formData.crypto_symbols, symbol];
    setFormData({ ...formData, crypto_symbols: symbols });
  };

  const toggleModel = (modelId: string) => {
    const models = formData.agent_models.includes(modelId)
      ? formData.agent_models.filter((m) => m !== modelId)
      : [...formData.agent_models, modelId];
    setFormData({ ...formData, agent_models: models });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {editingConfig ? "编辑配置" : "新建配置"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              {error}
            </div>
          )}

          {/* Name */}
          <div>
            <Label htmlFor="name">配置名称 *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="例如：BTC-ETH 保守策略"
              required
            />
          </div>

          {/* Crypto Symbols */}
          <div>
            <Label>交易符号 *</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {CRYPTO_SYMBOLS.map((symbol) => (
                <Badge
                  key={symbol}
                  variant={formData.crypto_symbols.includes(symbol) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleSymbol(symbol)}
                >
                  {symbol}
                  {formData.crypto_symbols.includes(symbol) && (
                    <X className="h-3 w-3 ml-1" />
                  )}
                </Badge>
              ))}
            </div>
            {formData.crypto_symbols.length === 0 && (
              <p className="text-sm text-muted-foreground mt-1">
                至少选择一个交易符号
              </p>
            )}
          </div>

          {/* Initial Capital */}
          <div>
            <Label htmlFor="initial_capital">初始资金 (USD) *</Label>
            <Input
              id="initial_capital"
              type="number"
              min="100"
              step="100"
              value={formData.initial_capital}
              onChange={(e) =>
                setFormData({ ...formData, initial_capital: parseFloat(e.target.value) || 0 })
              }
              required
            />
          </div>

          {/* Check Interval */}
          <div>
            <Label htmlFor="check_interval">检查间隔 (秒) *</Label>
            <Input
              id="check_interval"
              type="number"
              min="10"
              step="10"
              value={formData.check_interval}
              onChange={(e) =>
                setFormData({ ...formData, check_interval: parseInt(e.target.value) || 60 })
              }
              required
            />
            <p className="text-sm text-muted-foreground mt-1">
              建议: 60秒 (1分钟) 或更长
            </p>
          </div>

          {/* AI Models */}
          <div>
            <Label>AI 模型 *</Label>
            <div className="space-y-2 mt-2">
              {availableModels.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  没有可用的模型。请检查 API Key 配置。
                </p>
              ) : (
                availableModels.map((model) => (
                  <div key={model.id} className="flex items-center space-x-2">
                    <Checkbox
                      checked={formData.agent_models.includes(model.id)}
                      onCheckedChange={() => toggleModel(model.id)}
                    />
                    <Label className="cursor-pointer flex-1">
                      <span className="font-medium">{model.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">
                        ({model.provider})
                      </span>
                    </Label>
                  </div>
                ))
              )}
            </div>
            {formData.agent_models.length === 0 && (
              <p className="text-sm text-muted-foreground mt-1">
                至少选择一个 AI 模型
              </p>
            )}
          </div>

          {/* Use AI Signals */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="use_ai_signals"
              checked={formData.use_ai_signals}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, use_ai_signals: checked as boolean })
              }
            />
            <Label htmlFor="use_ai_signals" className="cursor-pointer">
              启用 AI 交易信号
            </Label>
          </div>

          {/* Risk Per Trade */}
          <div>
            <Label htmlFor="risk_per_trade">单笔风险 (%) *</Label>
            <Input
              id="risk_per_trade"
              type="number"
              min="0.01"
              max="1"
              step="0.01"
              value={formData.risk_per_trade}
              onChange={(e) =>
                setFormData({ ...formData, risk_per_trade: parseFloat(e.target.value) || 0.02 })
              }
              required
            />
            <p className="text-sm text-muted-foreground mt-1">
              每笔交易的风险比例 (0.02 = 2%)
            </p>
          </div>

          {/* Max Positions */}
          <div>
            <Label htmlFor="max_positions">最大持仓数 *</Label>
            <Input
              id="max_positions"
              type="number"
              min="1"
              max="10"
              value={formData.max_positions}
              onChange={(e) =>
                setFormData({ ...formData, max_positions: parseInt(e.target.value) || 3 })
              }
              required
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button type="submit" disabled={loading}>
              <Save className="h-4 w-4 mr-2" />
              {loading ? "保存中..." : "保存"}
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              <XCircle className="h-4 w-4 mr-2" />
              取消
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

