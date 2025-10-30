"use client";

import { useState, useEffect } from "react";
import { Activity, CheckCircle2, XCircle } from "lucide-react";

interface ConnectionStatusProps {
  apiUrl?: string;
}

export default function ConnectionStatus({ apiUrl = "http://localhost:8001" }: ConnectionStatusProps) {
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [lastCheck, setLastCheck] = useState<Date>(new Date());

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/trading/dashboard`, {
          method: "HEAD",
          signal: AbortSignal.timeout(3000),
        });
        if (response.ok) {
          setStatus("connected");
        } else {
          setStatus("disconnected");
        }
      } catch (error) {
        setStatus("disconnected");
      }
      setLastCheck(new Date());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000); // Check every 5s
    return () => clearInterval(interval);
  }, [apiUrl]);

  const statusConfig = {
    connecting: {
      icon: Activity,
      text: "CONNECTING TO SERVER",
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/20",
    },
    connected: {
      icon: CheckCircle2,
      text: "CONNECTED",
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      borderColor: "border-green-500/20",
    },
    disconnected: {
      icon: XCircle,
      text: "DISCONNECTED",
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/20",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${config.bgColor} ${config.borderColor}`}
    >
      <Icon className={`h-4 w-4 ${config.color} ${status === "connecting" ? "animate-pulse" : ""}`} />
      <span className={`text-xs font-mono font-medium ${config.color}`}>
        STATUS: {config.text}
      </span>
      {status === "connected" && (
        <span className="text-xs text-muted-foreground ml-2">
          ({lastCheck.toLocaleTimeString()})
        </span>
      )}
    </div>
  );
}

