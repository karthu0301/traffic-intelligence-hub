"use client";

import { useState, useEffect } from "react";

export function useAnalytics(baseUrl: string = "http://192.168.50.143:8000") {
  const [plateFrequency, setPlateFrequency] = useState<{ plate: string; count: number }[]>([]);
  const [accuracyTrends, setAccuracyTrends] = useState<{ date: string; avg_confidence: number }[]>([]);

  useEffect(() => {
    fetch(`${baseUrl}/plate-frequency`)
      .then((r) => r.json())
      .then(setPlateFrequency)
      .catch(console.error);

    fetch(`${baseUrl}/detection-accuracy-trends`)
      .then((r) => r.json())
      .then(setAccuracyTrends)
      .catch(console.error);
  }, [baseUrl]);

  return { plateFrequency, setPlateFrequency, accuracyTrends, setAccuracyTrends };
}
