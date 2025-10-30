"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, Play, Square, Save, Loader2 } from "lucide-react";
import TradingConfigForm from "./components/config-form";
import ConfigList from "./components/config-list";

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

export default function TradingConfigPage() {
  const [configs, setConfigs] = useState<TradingConfig[]>([]);
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState<TradingConfig | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Fetch configs
      const configsRes = await fetch("http://localhost:8001/api/v1/trading/config/list");
      const configsData = await configsRes.json();
      setConfigs(configsData || []);

      // Fetch available models
      const modelsRes = await fetch("http://localhost:8001/api/v1/trading/config/models/available");
      const modelsData = await modelsRes.json();
      setAvailableModels(modelsData || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setEditingConfig(null);
    setShowForm(true);
  };

  const handleEdit = (config: TradingConfig) => {
    setEditingConfig(config);
    setShowForm(true);
  };

  const handleSave = async () => {
    await fetchData();
    setShowForm(false);
    setEditingConfig(null);
  };

  const handleDelete = async (configId: string) => {
    if (!confirm("确定要删除这个配置吗？")) return;

    try {
      const response = await fetch(
        `http://localhost:8001/api/v1/trading/config/${configId}`,
        { method: "DELETE" }
      );
      if (response.ok) {
        await fetchData();
      }
    } catch (error) {
      console.error("Failed to delete config:", error);
    }
  };

  const handleStart = async (configId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8001/api/v1/trading/config/${configId}/start`,
        { method: "POST" }
      );
      const data = await response.json();
      
      if (response.ok) {
        alert(`配置已准备启动！请通过对话界面启动交易。\n\n配置: ${data.config_name}`);
      } else {
        alert(`启动失败: ${data.detail || "未知错误"}`);
      }
    } catch (error) {
      console.error("Failed to start config:", error);
      alert("启动失败，请检查后端连接");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">加载配置中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">交易配置管理</h1>
            <p className="text-muted-foreground">
              创建和管理 AI 交易策略配置
            </p>
          </div>
          <Button onClick={handleCreateNew} size="lg">
            <Plus className="h-4 w-4 mr-2" />
            新建配置
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="mb-6">
          <TradingConfigForm
            availableModels={availableModels}
            editingConfig={editingConfig}
            onSave={handleSave}
            onCancel={() => {
              setShowForm(false);
              setEditingConfig(null);
            }}
          />
        </div>
      )}

      {/* Config List */}
      <ConfigList
        configs={configs}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onStart={handleStart}
      />
    </div>
  );
}

