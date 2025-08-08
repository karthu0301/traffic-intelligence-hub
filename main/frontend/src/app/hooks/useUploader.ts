"use client";

import { useState } from "react";

export function useUploader(baseUrl: string = "http://192.168.50.143:8000") {
  const [files, setFiles] = useState<File[]>([]);

  const uploadFiles = async (
    token: string | null,
    isAuthenticated: boolean,
    fetchFiltered: () => Promise<void>,
    setPlateFrequency: (d: any) => void,
    setAccuracyTrends: (d: any) => void,
    history: any[],
    fetchFullResult: (id: number) => Promise<void>,
    setIsSaved: (saved: boolean) => void,
    setHistory: (data: any[]) => void,
    setResult: (data: any) => void,
    refreshAnalytics: () => void, 
    refreshReports: () => void 
  ) => {
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));

    try {
      const headers: HeadersInit = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      console.log("Token used:", token);
      const res = await fetch(`${baseUrl}/upload`, {
        method: "POST",
        headers,
        body: fd,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      const uploaded = (await res.json()) as (any & { saved: boolean })[];
      setFiles([]);

      if (isAuthenticated) {
        await fetchFiltered();

        const newest = uploaded[uploaded.length - 1];
        if (newest) {
          const match = history.find((h) => h.filename === newest.filename);
          if (match) fetchFullResult(match.id);
        }

        // Refresh analytics and reports
        refreshAnalytics();
        refreshReports();

        setIsSaved(true);
      } else {
        const items = uploaded.map((r, i) => ({
          id: Date.now() + i,
          filename: r.filename,
          annotated_image: r.annotated_image,
          detections: r.detections,
          timestamp: r.timestamp,
        }));
        setHistory([...items, ...history]);
        const firstWithImage = items.find((r) => r.annotated_image) || items[items.length - 1];
        setResult(firstWithImage);
        setIsSaved(false);
      }
    } catch (err) {
      console.error("Upload failed:", err);
      alert(`Upload failed: ${err}`);
    }
  };

  return { files, setFiles, uploadFiles };
}
