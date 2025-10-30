"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

interface TechnicalIndicators {
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
}

interface TechnicalIndicatorsChartProps {
  symbol: string;
  price: number;
  indicators: TechnicalIndicators;
  historicalPrices?: number[];
  historicalVolumes?: number[];
}

export default function TechnicalIndicatorsChart({
  symbol,
  price,
  indicators,
  historicalPrices = [],
  historicalVolumes = [],
}: TechnicalIndicatorsChartProps) {
  const priceChartRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  
  const priceChartInstance = useRef<echarts.ECharts | null>(null);
  const macdChartInstance = useRef<echarts.ECharts | null>(null);
  const rsiChartInstance = useRef<echarts.ECharts | null>(null);

  // Price + Bollinger Bands Chart
  useEffect(() => {
    if (!priceChartRef.current) return;

    if (!priceChartInstance.current) {
      priceChartInstance.current = echarts.init(priceChartRef.current);
    }

    // Prepare data
    const prices = historicalPrices.length > 0 ? historicalPrices : [price];
    const times = prices.map((_, i) => `T${i}`);
    
    const option: echarts.EChartsOption = {
      title: {
        text: `${symbol} - Price & Bollinger Bands`,
        left: "center",
      },
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          let result = `${params[0].name}<br/>`;
          params.forEach((param: any) => {
            result += `${param.seriesName}: $${param.value.toFixed(2)}<br/>`;
          });
          return result;
        },
      },
      xAxis: {
        type: "category",
        data: times,
        axisLabel: {
          show: false,
        },
      },
      yAxis: {
        type: "value",
        axisLabel: {
          formatter: (value: number) => `$${(value / 1000).toFixed(1)}k`,
        },
      },
      series: [
        {
          name: "Price",
          type: "line",
          data: prices,
          smooth: true,
          lineStyle: {
            width: 2,
            color: "#10b981",
          },
          itemStyle: {
            color: "#10b981",
          },
        },
        ...(indicators.bb_upper !== undefined &&
        indicators.bb_middle !== undefined &&
        indicators.bb_lower !== undefined
          ? [
              {
                name: "BB Upper",
                type: "line",
                data: Array(prices.length).fill(indicators.bb_upper),
                lineStyle: {
                  width: 1,
                  color: "#ef4444",
                  type: "dashed",
                },
                symbol: "none",
              } as any,
              {
                name: "BB Middle",
                type: "line",
                data: Array(prices.length).fill(indicators.bb_middle),
                lineStyle: {
                  width: 1,
                  color: "#64748b",
                  type: "dotted",
                },
                symbol: "none",
              } as any,
              {
                name: "BB Lower",
                type: "line",
                data: Array(prices.length).fill(indicators.bb_lower),
                lineStyle: {
                  width: 1,
                  color: "#3b82f6",
                  type: "dashed",
                },
                symbol: "none",
              } as any,
            ]
          : []),
        ...(indicators.ema_12 !== undefined
          ? [
              {
                name: "EMA 12",
                type: "line",
                data: Array(prices.length).fill(indicators.ema_12),
                lineStyle: {
                  width: 1,
                  color: "#f59e0b",
                },
                symbol: "none",
              } as any,
            ]
          : []),
        ...(indicators.ema_26 !== undefined
          ? [
              {
                name: "EMA 26",
                type: "line",
                data: Array(prices.length).fill(indicators.ema_26),
                lineStyle: {
                  width: 1,
                  color: "#8b5cf6",
                },
                symbol: "none",
              } as any,
            ]
          : []),
        ...(indicators.ema_50 !== undefined
          ? [
              {
                name: "EMA 50",
                type: "line",
                data: Array(prices.length).fill(indicators.ema_50),
                lineStyle: {
                  width: 1,
                  color: "#ec4899",
                },
                symbol: "none",
              } as any,
            ]
          : []),
      ],
      grid: {
        left: "60px",
        right: "20px",
        top: "60px",
        bottom: "40px",
      },
    };

    priceChartInstance.current?.setOption(option);
  }, [symbol, price, indicators, historicalPrices]);

  // MACD Chart
  useEffect(() => {
    if (!macdChartRef.current) return;

    if (!macdChartInstance.current) {
      macdChartInstance.current = echarts.init(macdChartRef.current);
    }

    if (
      indicators.macd === undefined ||
      indicators.macd_signal === undefined ||
      indicators.macd_histogram === undefined
    ) {
      return;
    }

    const option: echarts.EChartsOption = {
      title: {
        text: "MACD",
        left: "center",
      },
      tooltip: {
        trigger: "axis",
      },
      xAxis: {
        type: "category",
        data: ["MACD", "Signal", "Histogram"],
      },
      yAxis: {
        type: "value",
      },
      series: [
        {
          name: "MACD",
          type: "bar",
          data: [indicators.macd, indicators.macd_signal, indicators.macd_histogram],
          itemStyle: {
            color: (params: any) => {
              if (params.name === "Histogram") {
                return params.value[params.dataIndex] >= 0
                  ? "#10b981"
                  : "#ef4444";
              }
              return params.dataIndex === 0
                ? "#3b82f6"
                : params.dataIndex === 1
                ? "#f59e0b"
                : "#10b981";
            },
          },
        },
      ],
      grid: {
        left: "60px",
        right: "20px",
        top: "60px",
        bottom: "40px",
      },
    };

    macdChartInstance.current?.setOption(option);
  }, [indicators]);

  // RSI Chart
  useEffect(() => {
    if (!rsiChartRef.current) return;

    if (!rsiChartInstance.current) {
      rsiChartInstance.current = echarts.init(rsiChartRef.current);
    }

    if (indicators.rsi === undefined) {
      return;
    }

    const option: echarts.EChartsOption = {
      title: {
        text: `RSI: ${indicators.rsi.toFixed(2)}`,
        left: "center",
      },
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          return `RSI: ${params[0].value.toFixed(2)}`;
        },
      },
      xAxis: {
        type: "category",
        data: ["RSI"],
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        splitLine: {
          lineStyle: {
            color: ["#ef4444", "#10b981"],
          },
          lineDash: [2, 2],
        },
      },
      series: [
        {
          name: "RSI",
          type: "bar",
          data: [indicators.rsi],
          itemStyle: {
            color: (params: any) => {
              const value = params.value[params.dataIndex];
              if (value >= 70) return "#ef4444"; // Overbought
              if (value <= 30) return "#10b981"; // Oversold
              return "#f59e0b"; // Neutral
            },
          },
          markLine: {
            data: [
              { yAxis: 70, name: "Overbought" },
              { yAxis: 30, name: "Oversold" },
            ],
            lineStyle: {
              color: "#64748b",
              type: "dashed",
            },
          },
        },
      ],
      grid: {
        left: "60px",
        right: "20px",
        top: "60px",
        bottom: "40px",
      },
    };

    rsiChartInstance.current?.setOption(option);
  }, [indicators]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      priceChartInstance.current?.resize();
      macdChartInstance.current?.resize();
      rsiChartInstance.current?.resize();
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="space-y-4">
      {/* Price & Bollinger Bands */}
      <div>
        <div ref={priceChartRef} className="w-full h-[300px]" />
      </div>

      {/* MACD & RSI */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div ref={macdChartRef} className="w-full h-[200px]" />
        </div>
        <div>
          <div ref={rsiChartRef} className="w-full h-[200px]" />
        </div>
      </div>

      {/* Indicators Summary */}
      <div className="grid grid-cols-3 gap-2 text-sm">
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-xs text-muted-foreground">EMA 12</p>
          <p className="font-mono">
            {indicators.ema_12 ? `$${indicators.ema_12.toFixed(2)}` : "N/A"}
          </p>
        </div>
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-xs text-muted-foreground">EMA 26</p>
          <p className="font-mono">
            {indicators.ema_26 ? `$${indicators.ema_26.toFixed(2)}` : "N/A"}
          </p>
        </div>
        <div className="p-2 bg-muted/50 rounded">
          <p className="text-xs text-muted-foreground">EMA 50</p>
          <p className="font-mono">
            {indicators.ema_50 ? `$${indicators.ema_50.toFixed(2)}` : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
}

