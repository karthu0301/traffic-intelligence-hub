"use client";

import { useState, useCallback, useEffect } from "react";

export function useDetectionData(baseUrl: string = "http://192.168.50.143:8000") {
  const [history, setHistory] = useState<any[]>([]);
  const [result, setResult] = useState<any | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(5);
  const [sortBy, setSortBy] = useState("timestamp");
  const [order, setOrder] = useState("desc");

  const fetchFiltered = useCallback(async () => {
    const q = new URLSearchParams();
    if (searchTerm) {
      q.append("plate_query", searchTerm);
      q.append("filename_query", searchTerm);
    }
    q.append("sort_by", sortBy);
    q.append("order", order);
    q.append("limit", pageSize.toString());
    q.append("offset", ((currentPage - 1) * pageSize).toString());

    try {
      const res = await fetch(`${baseUrl}/search?${q}`);
      const data = await res.json();
      setHistory(data.results);
      setTotalResults(data.total);
    } catch (err) {
      console.error("History fetch failed:", err);
    }
  }, [searchTerm, currentPage, sortBy, order, pageSize, baseUrl]);

  const fetchFullResult = async (id: number) => {
    try {
      const res = await fetch(`${baseUrl}/result/${id}`);
      const full = await res.json();
      setResult(full);
    } catch (err) {
      console.error("Failed to fetch full result:", err);
    }
  };

  const deleteRecord = async (id: number, isAuthenticated: boolean) => {
    if (!confirm("Are you sure you want to delete this upload?")) return;
    try {
      const res = await fetch(`${baseUrl}/delete/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      setHistory((prev) => prev.filter((r) => r.id !== id));
      if (result?.id === id) setResult(null);
      if (isAuthenticated) await fetchFiltered();
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Failed to delete. Try again.");
    }
  };


  return {
    history,
    result,
    totalResults,
    searchTerm,
    setSearchTerm,
    currentPage,
    setCurrentPage,
    pageSize,
    sortBy,
    setSortBy,
    order,
    setOrder,
    fetchFiltered,
    fetchFullResult,
    setHistory,
    setResult,
    deleteRecord,
  };
}
