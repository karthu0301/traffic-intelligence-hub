import { useState, useEffect, useCallback } from "react";

export type ReportRange = "daily" | "weekly" | "monthly" | "yearly";

export function useReports(
  range: ReportRange = "daily",
  rich: boolean = false,
  baseUrl: string = "http://192.168.50.143:8000"
) {
  const [report, setReport] = useState<string>("");
  const [trends, setTrends] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = useCallback(async (r: ReportRange = range, richFlag: boolean = rich) => {
    try {
      setLoading(true);
      const res = await fetch(`${baseUrl}/analytics/report?range=${r}&rich=${richFlag}`);
      if (!res.ok) throw new Error(`Failed with ${res.status}`);
      const data = await res.json();
      setReport(data.summary);
      setTrends(data.trends || null);
    } catch (err: any) {
      console.error("Failed to fetch report:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [range, baseUrl, rich]);

  useEffect(() => {
    fetchReport(range, rich);
  }, [range, rich, fetchReport]);

  return {
    report,
    trends, 
    loading,
    error,
    refresh: fetchReport,
  };
}
