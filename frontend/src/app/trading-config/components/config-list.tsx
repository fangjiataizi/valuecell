"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2, Play, Activity } from "lucide-react";

interface TradingConfig {
  id: string;
  name: string;
  crypto_symbols: string[];
  initial_capital: number;
  check_interval: number;
  use_ai_signals: boolean;
  agent_models: string[];
  risk_per_trade: number;
  max_positions: number;
  created_at: string;
  updated_at: string;
  active_instances: string[];
}

interface ConfigListProps {
  configs: TradingConfig[];
  onEdit: (config: TradingConfig) => void;
  onDelete: (configId: string) => void;
  onStart: (configId: string) => void;
}

export default function ConfigList({
  configs,
  onEdit,
  onDelete,
  onStart,
}: ConfigListProps) {
  if (configs.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <p className="text-lg font-medium">暂无配置</p>
          <p className="text-sm mt-2">点击"新建配置"开始创建</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {configs.map((config) => (
        <Card key={config.id} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg">{config.name}</CardTitle>
                {config.active_instances.length > 0 && (
                  <Badge variant="default" className="mt-2">
                    <Activity className="h-3 w-3 mr-1" />
                    {config.active_instances.length} 个运行中
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Symbols */}
            <div>
              <p className="text-sm text-muted-foreground mb-1">交易符号</p>
              <div className="flex flex-wrap gap-1">
                {config.crypto_symbols.map((symbol) => (
                  <Badge key={symbol} variant="outline">
                    {symbol}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Models */}
            <div>
              <p className="text-sm text-muted-foreground mb-1">AI 模型</p>
              <div className="flex flex-wrap gap-1">
                {config.agent_models.slice(0, 2).map((model) => (
                  <Badge key={model} variant="secondary" className="text-xs">
                    {model.split("/").pop()}
                  </Badge>
                ))}
                {config.agent_models.length > 2 && (
                  <Badge variant="secondary" className="text-xs">
                    +{config.agent_models.length - 2}
                  </Badge>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-muted-foreground">初始资金</p>
                <p className="font-medium">
                  ${config.initial_capital.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">检查间隔</p>
                <p className="font-medium">{config.check_interval}秒</p>
              </div>
              <div>
                <p className="text-muted-foreground">单笔风险</p>
                <p className="font-medium">{(config.risk_per_trade * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">最大持仓</p>
                <p className="font-medium">{config.max_positions}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2 border-t">
              <Button
                variant="default"
                size="sm"
                onClick={() => onStart(config.id)}
                className="flex-1"
              >
                <Play className="h-4 w-4 mr-1" />
                启动
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(config)}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDelete(config.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            {/* Timestamp */}
            <p className="text-xs text-muted-foreground">
              创建于: {new Date(config.created_at).toLocaleString("zh-CN")}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

