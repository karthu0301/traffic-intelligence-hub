import { useState, useEffect, useCallback } from "react";

export function useAnalytics(
  range: "daily" | "weekly" | "monthly" | "yearly" = "daily"
) {
  const [plateFrequency, setPlateFrequency] = useState<{ plate: string; count: number }[]>([]);
  const [accuracyTrends, setAccuracyTrends] = useState<{ date: string; avg_confidence: number }[]>([]);
  const [analyticsReport, setAnalyticsReport] = useState<string>(""); // Summary from backend
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://192.168.50.143:8000/analytics/report?range=${range}&rich=true`);
      if (!res.ok) throw new Error("Failed to fetch analytics");
      const data = await res.json();
      setPlateFrequency(data.plate_frequency || []);
      setAccuracyTrends(data.accuracy_trends || []);
      setAnalyticsReport(data.summary || "");
    } catch (err) {
      console.error("Analytics fetch failed", err);
    } finally {
      setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    fetchAnalytics();
  }, [range, fetchAnalytics]);


  const chartData = (() => {
    const topPlates = [...plateFrequency]
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      labels: topPlates.map((i) => i.plate),
      datasets: [{
        label: "Frequency",
        data: topPlates.map((i) => i.count),
        backgroundColor: "#94B4C1"
      }]
    };
  })();

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: "Top 10 Plate Frequency" },
      tooltip: {
        callbacks: {
          label: function (context: import("chart.js").TooltipItem<"bar">) {
            return `Frequency: ${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          callback: function (this: any, value: any): string {
            const label = this.getLabelForValue(value);
            return label.length > 8 ? label.slice(0, 6) + "…" : label;
          },
          maxRotation: 45,
          minRotation: 0
        }
      },
      y: {
        title: { display: true, text: "Count" },
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          color: "#eaeaea"
        },
        grid: { color: "#333" }
      }
    }
  };


  const trendData = accuracyTrends.length > 0
    ? {
        labels: accuracyTrends.map((t) => {
          const date = new Date(t.date);
          return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }),
        datasets: [{
          label: "Avg Detection Confidence",
          data: accuracyTrends.map((t) => t.avg_confidence),
          borderColor: "#94B4C1",
          backgroundColor: "rgba(148, 180, 193, 0.2)",
          tension: 0.3,
          fill: true
        }]
      }
    : {
        labels: [],
        datasets: []
      };

  const trendOptions = {
    responsive: true,
    plugins: {
      legend: { display: true },
      title: { display: true, text: "Detection Accuracy Trends" },
      tooltip: {
        callbacks: {
          label: function (context: import("chart.js").TooltipItem<"line">) {
            return `Avg Confidence: ${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: { display: true, text: "Date" }
      },
      y: {
        title: { display: true, text: "Avg Confidence" },
        beginAtZero: true,
        max: 1
      }
    }
  };

  return {
    plateFrequency,
    accuracyTrends,
    analyticsReport,
    chartData,
    chartOptions,
    trendData,
    trendOptions,
    refresh: fetchAnalytics,
    setPlateFrequency,
    setAccuracyTrends,
    loading
  };
}
