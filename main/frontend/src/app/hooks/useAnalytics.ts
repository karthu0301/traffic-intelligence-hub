import { useState, useEffect, useCallback } from "react";

export function useAnalytics(
  range: "daily" | "weekly" | "monthly" | "yearly" = "daily"
) {
  const [plateFrequency, setPlateFrequency] = useState<{ plate: string; count: number }[]>([]);
  const [accuracyTrends, setAccuracyTrends] = useState<{ date: string; avg_confidence: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://192.168.50.143:8000/analytics/report?range=${range}&rich=true`);
      if (!res.ok) throw new Error("Failed to fetch analytics");
      const data = await res.json();
      setPlateFrequency(data.plate_frequency || []);
      setAccuracyTrends(data.accuracy_trends || []);
    } catch (err) {
      console.error("Analytics fetch failed", err);
    } finally {
      setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    fetchAnalytics();
  }, [range, fetchAnalytics]);

  return { plateFrequency, accuracyTrends, setPlateFrequency, setAccuracyTrends, loading, refresh: fetchAnalytics };
}
