'use client';
import { useState, useEffect } from 'react';


type Detection = {
  box: number[];
  confidence: number;
  class_id: number;
  crop_path: string;
};

type Result = {
  filename: string;
  annotated_image: string;
  detections: Detection[];
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [history, setHistory] = useState<Result[]>([]);

  const uploadFile = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://192.168.50.143:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Failed to upload. Status: ${res.status}`);
      }

      const data = await res.json();
      console.log('✅ Upload result:', data);
      setResult(data);
    } catch (err) {
      console.error('❌ Upload failed:', err);
      alert(`Upload failed: ${err}`);
    }

  };

  useEffect(() => {
      const fetchHistory = async () => {
        const res = await fetch('http://192.168.50.143:8000/history');
        const data = await res.json();
        setHistory(data);
      };

      fetchHistory();
    }, []);

  return (
    <main className="p-4">
      <h1 className="text-xl font-bold mb-4">🚗 Traffic Intelligence Hub</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button
        onClick={uploadFile}
        className="bg-blue-500 text-white px-4 py-2 mt-2 rounded"
      >
        Upload Dataset
      </button>

      {result && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">✅ Detection Results</h2>

          <p className="text-sm mt-1 text-gray-500">{result.filename}</p>

          {/* Annotated Image */}
          <div className="my-4">
            <h3 className="font-medium mb-2">Annotated Image</h3>
            <img
              src={`http://192.168.50.143:8000${result.annotated_image}`}
              alt="Annotated"
              className="max-w-md border"
            />
          </div>

          {/* Cropped Plates */}
          <div className="my-4">
            <h3 className="font-medium mb-2">Detected Plates</h3>
            <div className="grid grid-cols-2 gap-4">
              {Array.isArray(result.detections) && result.detections.length > 0 ? (
                result.detections.map((detection, idx) => (
                  <div key={idx} className="text-sm">
                    <img
                      src={`http://192.168.50.143:8000/${detection.crop_path}`}
                      alt={`Plate ${idx}`}
                      className="w-48 border mb-1"
                    />
                    <p>Confidence: {(detection.confidence * 100).toFixed(1)}%</p>
                  </div>
                ))
              ) : (
                <p>No plates detected.</p>
              )}
            </div>
          </div>
          {history.length > 0 && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold">📜 Upload History</h2>
              <ul className="mt-2 space-y-2">
                {history.map((h, idx) => (
                  <li key={idx} className="border p-2 rounded">
                    <p className="text-sm font-medium">{h.filename}</p>
                    <p className="text-xs text-gray-500">{h.timestamp}</p>
                    <button
                      onClick={() => setResult(h)}
                      className="text-blue-500 underline text-sm"
                    >
                      View Result
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
