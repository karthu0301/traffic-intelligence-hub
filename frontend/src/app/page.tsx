'use client';
import { useState, useEffect } from 'react';
import "./globals.css";
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

type Detection = {
  plate_string: string;
  plate_confidence: number;
  plate_crop_path: string;
  characters: {
    box: number[];
    class_id: number;
    confidence: number;
  }[];
};

type Result = {
  filename: string;
  annotated_image: string;
  detections: Detection[];
  timestamp?: string;
};

const charMap = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [history, setHistory] = useState<Result[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [accuracyTrends, setAccuracyTrends] = useState<{ date: string; avg_confidence: number }[]>([]);

  const trendData = {
  labels: accuracyTrends.map((t) => t.date),
  datasets: [
    {
      label: 'Avg Detection Confidence',
      data: accuracyTrends.map((t) => t.avg_confidence),
      borderColor: '#94B4C1',
      backgroundColor: 'rgba(148, 180, 193, 0.2)',
      tension: 0.3,
      fill: true
    }
  ]
};

const trendOptions = {
  responsive: true,
  plugins: {
    legend: { display: true },
    title: {
      display: true,
      text: 'Detection Accuracy Trends'
    }
  }
};

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
      setResult(data);
    } catch (err) {
      console.error('❌ Upload failed:', err);
      alert(`Upload failed: ${err}`);
    }
  };

  useEffect(() => {
  const fetchFiltered = async () => {
    const query = new URLSearchParams();
    if (searchTerm) {
      query.append("plate_query", searchTerm);
      query.append("filename_query", searchTerm);
    }

    const res = await fetch(`http://192.168.50.143:8000/search?${query}`);
    const data = await res.json();
    setHistory(data);
  };

  fetchFiltered();
}, [searchTerm]);

useEffect(() => {
  const fetchTrends = async () => {
    const res = await fetch("http://192.168.50.143:8000/detection-accuracy-trends");
    const data = await res.json();
    setAccuracyTrends(data);
  };
  fetchTrends();
}, []);

  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-[#213448] text-white font-sans">
      {/* Sidebar */}
      <aside className="md:w-1/4 bg-[#547792] p-4 flex flex-col space-y-4">
        <h1 className="text-2xl font-bold">🚗 Traffic Intelligence Hub</h1>

        {/* Upload Section */}
        <div className="flex flex-col space-y-2">
          <div className="flex items-center space-x-2">
            <label className="bg-[#94B4C1] text-[#213448] font-semibold text-sm px-3 py-1.5 rounded cursor-pointer">
              Choose File
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
                id="fileInput"
              />
            </label>
            {file && (
              <span className="text-sm text-[#ECEFCA] truncate max-w-[10rem]">
                {file.name}
              </span>
            )}
          </div>
          <button
            onClick={async () => {
              await uploadFile();
              setFile(null); // Clear file state
              const inputEl = document.getElementById("fileInput") as HTMLInputElement;
              if (inputEl) inputEl.value = ""; // Reset actual input
            }}
            className="bg-[#ECEFCA] text-[#213448] px-4 py-2 rounded font-semibold text-sm"
          >
            Upload Image
          </button>
        </div>

        {/* Search + History */}
        <div className="flex flex-col mt-4">
          <input
            type="text"
            placeholder="Search by filename or plate..."
            className="w-full p-2 mb-3 rounded bg-[#ECEFCA] text-[#213448]"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          {history.length > 0 ? (
            <>
              <h2 className="text-lg font-semibold mb-2">📜 Upload History</h2>
              <ul className="space-y-2 overflow-y-auto max-h-[60vh] pr-2">
                {history.map((h, idx) => (
                  <li
                    key={idx}
                    className="flex items-center space-x-2 bg-[#94B4C1] p-2 rounded cursor-pointer"
                    onClick={() => setResult(h)}
                  >
                    <img
                      src={`http://192.168.50.143:8000${h.annotated_image}`}
                      alt="thumb"
                      className="w-12 h-12 object-cover rounded-sm border"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[#213448]">{h.filename}</p>
                      <p className="text-xs text-[#21344880]">
                        {h.timestamp?.slice(0, 19).replace("T", " ")}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm mt-2 text-[#ECEFCA]">No history yet.</p>
          )}
        </div>
      </aside>

      {/* Main Viewer */}
      <section className="md:flex-1 p-6 overflow-y-auto">
        {result ? (
          <>
            <h2 className="text-xl font-semibold mb-2 text-[#ECEFCA]">✅ Detection Results</h2>
            <p className="text-sm text-gray-300 mb-4">{result.filename}</p>

            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2 text-[#94B4C1]">Annotated Image</h3>
              <img
                src={`http://192.168.50.143:8000${result.annotated_image}`}
                alt="Annotated"
                className="w-full max-w-4xl border-4 border-[#94B4C1] rounded-md"
              />
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2 text-[#94B4C1]">Detected Plates</h3>
              {result.detections.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {result.detections.map((detection, idx) => (
                    <div key={idx} className="bg-[#547792] p-3 rounded border border-[#ECEFCA] text-sm">
                      <img
                        src={`http://192.168.50.143:8000${detection.plate_crop_path}`}
                        alt={`Plate ${idx}`}
                        className="w-full mb-2 border rounded"
                      />
                      <p><strong>Plate:</strong> {detection.plate_string || 'N/A'}</p>
                      <p><strong>Confidence:</strong> {detection.plate_confidence ? `${(detection.plate_confidence * 100).toFixed(2)}%` : 'N/A'}</p>
                      <p>
                        <strong>Characters:</strong>{" "}
                        {detection.characters?.map(c => charMap[c.class_id] || "?").join('') || "N/A"}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No plates detected.</p>
              )}
            </div>
          </>
        ) : (
          <p className="text-gray-400">Upload an image to begin.</p>
        )}
      </section>
      <aside className="md:w-1/4 bg-[#1B2C3E] p-6 border-l border-[#ECEFCA]">
        {accuracyTrends.length > 0 && (
          <div className="mt-10">
            <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">📈 Detection Accuracy Trends</h3>
            <div className="bg-[#547792] p-4 rounded-lg border border-[#ECEFCA]">
              <Line data={trendData} options={trendOptions} />
            </div>
          </div>
        )}
      </aside>
    </main>
  );
}
