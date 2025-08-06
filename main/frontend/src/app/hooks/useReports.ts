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

  const getStructuredReport = () => {
    return report
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const [left, right] = line.split(' -> ');
        const [date, filename] = left.split(' - ');
        const plates = right?.split(',').map((p) => p.trim()) || [];
        return { date, filename, plates };
      });
  };

  const exportCSV = () => {
    const structured = getStructuredReport();

    const csvRows = [
      ['Date', 'Filename', 'Detected Plates'],
      ...structured.map(({ date, filename, plates }) => [
        date,
        filename,
        plates.join(' ')
      ])
    ];

    const csvContent = csvRows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `analytics-report-${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return {
    report,
    trends,
    loading,
    error,
    refresh: fetchReport,
    getStructuredReport,
    exportCSV
  };
}
