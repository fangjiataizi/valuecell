"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";

interface PortfolioChartProps {
  instanceId: string;
}

export default function PortfolioChart({ instanceId }: PortfolioChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Initialize chart
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // Fetch chart data
    const fetchData = async () => {
      try {
        const response = await fetch(
          `http://localhost:8001/api/v1/trading/instance/${instanceId}/chart`
        );
        const data = await response.json();

        // Parse Google Charts format
        if (data.data && Array.isArray(data.data) && data.data.length > 1) {
          const headers = data.data[0] as string[];
          const rows = data.data.slice(1) as (string | number)[][];

          // Extract time and values
          const times = rows.map(row => row[0] as string);
          const portfolioValues = rows.map(row => row[1] as number);

          // Configure chart
          const option: echarts.EChartsOption = {
            title: {
              text: "TOTAL ACCOUNT VALUE",
              left: "center",
              textStyle: {
                fontSize: 18,
                fontWeight: "bold",
              },
            },
            tooltip: {
              trigger: "axis",
              formatter: (params: any) => {
                const param = params[0];
                return `${param.name}<br/>${param.seriesName}: $${param.value.toLocaleString()}`;
              },
            },
            xAxis: {
              type: "category",
              data: times,
              axisLabel: {
                formatter: (value: string) => {
                  // Format time display
                  const date = new Date(value);
                  return `${date.getHours()}:${date.getMinutes().toString().padStart(2, "0")}`;
                },
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
                name: "Portfolio Value",
                type: "line",
                data: portfolioValues,
                smooth: true,
                lineStyle: {
                  width: 3,
                  color: "#10b981",
                },
                areaStyle: {
                  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: "rgba(16, 185, 129, 0.3)" },
                    { offset: 1, color: "rgba(16, 185, 129, 0.05)" },
                  ]),
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

          chartInstance.current?.setOption(option);
        }
      } catch (error) {
        console.error("Failed to fetch chart data:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s

    return () => clearInterval(interval);
  }, [instanceId]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <div ref={chartRef} className="w-full h-[400px]" />;
}

