'use client';
import { useState, useEffect } from 'react';
import "./globals.css";
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

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
  id: number;
  filename: string;
  annotated_image: string;
  detections?: Detection[];
  timestamp?: string;
};

const charMap = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [history, setHistory] = useState<Result[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5); 
  const [totalResults, setTotalResults] = useState(0);
  const [sortBy, setSortBy] = useState("timestamp");
  const [order, setOrder] = useState("desc");
  const [plateFrequency, setPlateFrequency] = useState<{ plate: string; count: number }[]>([]);

  const uploadFiles = async () => {
    if (files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
      formData.append('files', file);
    }

    try {
      const res = await fetch('http://192.168.50.143:8000/upload', {
        method: 'POST',
        body: formData,
      });


      if (!res.ok) throw new Error(`Failed to upload. Status: ${res.status}`);

      const data: Result[] = await res.json();

      const detailedResult = await fetch(`http://192.168.50.143:8000/result/${data[0].id}`);
      const fullResult = await detailedResult.json();

      setResult(fullResult);
      setFiles([]);
      setHistory((prev) => [...data, ...prev]);
    } catch (err) {
      console.error('❌ Upload failed:', err);
      alert(`Upload failed: ${err}`);
    }
  };

  const fetchFullResult = async (id: number) => {
    try {
      const res = await fetch(`http://192.168.50.143:8000/result/${id}`);
      if (!res.ok) throw new Error("Failed to fetch result");
      const full = await res.json();
      setResult(full);
    } catch (err) {
      console.error("Failed to fetch full result:", err);
    }
  };

  useEffect(() => {
    const fetchFiltered = async () => {
      const query = new URLSearchParams();
      if (searchTerm) {
        query.append("plate_query", searchTerm);
        query.append("filename_query", searchTerm);
      }
      query.append("sort_by", sortBy);
      query.append("order", order);
      query.append("limit", pageSize.toString());
    query.append("offset", ((currentPage - 1) * pageSize).toString());

    const res = await fetch(`http://192.168.50.143:8000/search?${query}`);
    const data = await res.json();
    setHistory(data.results);
    setTotalResults(data.total);
  };
  fetchFiltered();
}, [searchTerm, currentPage]);

  useEffect(() => {
    const fetchPlateFreq = async () => {
      const res = await fetch("http://192.168.50.143:8000/plate-frequency");
      const data = await res.json();
      setPlateFrequency(data);
    };
    fetchPlateFreq();
  }, []);

  const chartData = {
    labels: plateFrequency.map((item) => item.plate),
    datasets: [{
      label: 'Frequency',
      data: plateFrequency.map((item) => item.count),
      backgroundColor: '#94B4C1'
    }]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Plate Frequency Chart' }
    }
  };
  
  const deleteRecord = async (id: number) => {
  const confirmed = confirm("Are you sure you want to delete this upload?");
  if (!confirmed) return;

  try {
    const res = await fetch(`http://192.168.50.143:8000/delete/${id}`, {
      method: 'DELETE'
    });

    if (!res.ok) throw new Error(`Failed to delete. Status: ${res.status}`);

    setHistory(prev => prev.filter(r => r.id !== id));
    if (result?.id === id) setResult(null);
  } catch (err) {
    console.error("❌ Failed to delete:", err);
    alert("Failed to delete. Try again.");
  }
};


  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-[#213448] text-white font-sans">
      {/* Sidebar */}
      <aside className="md:w-1/4 bg-[#547792] p-4 flex flex-col space-y-4">
        <h1 className="text-2xl font-bold">🚗 Traffic Intelligence Hub</h1>
        <div className="flex flex-col space-y-2">
          <div className="flex items-center space-x-2">
            <label className="bg-[#94B4C1] text-[#213448] font-semibold text-sm px-3 py-1.5 rounded cursor-pointer">
              Choose File(s)
              <input
                type="file"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
                style={{ display: 'none' }}
              />
            </label>
            {files.length > 0 && (
              <p className="text-xs text-gray-300 mt-2">
                {files.map(f => f.name).join(', ')}
              </p>
            )}
          </div>
          <button
            onClick={uploadFiles}
            className="bg-[#ECEFCA] text-[#213448] px-4 py-2 rounded font-semibold text-sm"
          >
            Upload Image(s)
          </button>
        </div>

        <div className="flex flex-col mt-4">
          <input
            type="text"
            placeholder="Search by filename or plate..."
            className="w-full p-2 mb-3 rounded bg-[#ECEFCA] text-[#213448]"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="flex space-x-2 mb-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-[#213448] text-sm rounded p-1"
            >
              <option value="timestamp">Sort by Timestamp</option>
              <option value="filename">Sort by Filename</option>
            </select>
            <select
              value={order}
              onChange={(e) => setOrder(e.target.value)}
              className="text-[#213448] text-sm rounded p-1"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
          {history.length > 0 ? (
            <>
              <h2 className="text-lg font-semibold mb-2">📜 Upload History</h2>
              <a
                href={`http://192.168.50.143:8000/download-all?plate_query=${searchTerm}&filename_query=${searchTerm}`}
                download
                className="text-sm text-blue-200 underline block mt-2"
              >
                ⬇ Download Results (ZIP)
              </a>
              <ul className="space-y-2 overflow-y-auto max-h-[60vh] pr-2">
                {history.map((h, idx) => (
                  <li
                    key={idx}
                    className="flex items-center space-x-2 bg-[#94B4C1] p-2 rounded cursor-pointer"
                    onClick={() => fetchFullResult(h.id)}
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
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteRecord(h.id);
                        }}
                        className="text-[#992222] hover:text-[#cc4444] cursor-pointer text-lg"
                        title="Delete"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-5 w-5"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M6 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 112 0v6a1 1 0 11-2 0V8zM4 5a1 1 0 011-1h10a1 1 0 011 1v1H4V5zm2-3a1 1 0 00-1 1v1h10V3a1 1 0 00-1-1H6z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm mt-2 text-[#ECEFCA]">No history yet.</p>
          )}
        </div>
        <div className="flex items-center justify-between mt-4 text-sm">
        <button
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 rounded bg-[#ECEFCA] text-[#213448] disabled:opacity-50"
        >
          ⬅ Prev
        </button>
        <span>
          Page {currentPage} of {Math.ceil(totalResults / pageSize)}
        </span>
        <button
          onClick={() => setCurrentPage((p) => p + 1)}
          disabled={currentPage >= Math.ceil(totalResults / pageSize)}
          className="px-3 py-1 rounded bg-[#ECEFCA] text-[#213448] disabled:opacity-50"
        >
          Next ➡
        </button>
      </div>
      </aside>
      
      {/* Main Viewer */}
      <section className="md:w-2/4 p-6 overflow-y-auto">
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
              <a
                href={`http://192.168.50.143:8000${result.annotated_image}`}
                download
                className="text-blue-200 underline text-sm"
              >
                ⬇ Download Annotated Image
              </a>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2 text-[#94B4C1]">Detected Plates</h3>
              {result.detections && result.detections.length > 0 ? (
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
                      <a
                        href={`http://192.168.50.143:8000${detection.plate_crop_path}`}
                        download
                        className="text-blue-200 underline text-xs"
                      >
                        ⬇ Download Crop
                      </a>
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

      {/* Plate Frequency Chart Panel */}
      <aside className="md:w-1/4 bg-[#1B2C3E] p-6 border-l border-[#ECEFCA]">
        <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">📊 Plate Frequency Chart</h3>
        {plateFrequency.length > 0 ? (
          <div className="bg-[#547792] p-4 rounded-lg border border-[#ECEFCA]">
            <Bar data={chartData} options={chartOptions} />
          </div>
        ) : (
          <p className="text-sm text-[#ECEFCA]">No frequency data yet.</p>
        )}
      </aside>
    </main>
  );
}
