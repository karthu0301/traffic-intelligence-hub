'use client';

import { useState, useEffect } from 'react';
import "./globals.css";
import { useAuth } from './hooks/useAuth';
import { useRouter } from 'next/navigation';
import { Line, Bar } from 'react-chartjs-2';
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
import Link from 'next/link';

// Import new hooks
import { useLLM } from './hooks/useLLM';
import { useDetectionData } from './hooks/useDetection';
import { useAnalytics } from './hooks/useAnalytics';
import { useUploader } from './hooks/useUploader';
import { useReports } from './hooks/useReports';

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

const charMap = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function Home() {
  const router = useRouter();
  const { token, isAuthenticated, logout } = useAuth();
  const {
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
  } = useDetectionData();
  const { files, setFiles, uploadFiles } = useUploader();
  const { llmAnswer, devAnswer, loadingAnswer, askLLM, askDevAssistant } = useLLM();
  const [isSaved, setIsSaved] = useState(true);
  const [llmQuestion, setLlmQuestion] = useState("");
  const [devQuestion, setDevQuestion] = useState("");
  const [devPanelOpen, setDevPanelOpen] = useState(false);
  const [reportRange, setReportRange] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
  const {
  plateFrequency,
  setPlateFrequency,
  accuracyTrends,
  setAccuracyTrends,
  refresh: refreshAnalytics
} = useAnalytics(reportRange);
const { report: analyticsReport, trends, loading: reportLoading, refresh: refreshReports } = useReports(reportRange, true);
  // Charts
  const chartData = {
    labels: plateFrequency.map((i) => String(i.plate)),
    datasets: [{ label: "Frequency", data: plateFrequency.map((i) => i.count), backgroundColor: "#94B4C1" }],
  };
  
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: "Plate Frequency Chart"
      },
      tooltip: {
        callbacks: {
          label(context: import("chart.js").TooltipItem<"line">): string {
            return `Avg Confidence: ${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          callback: function(value: string | number): string {
            const label = String(value);
            return label.length > 8 ? label.slice(0, 6) + "…" : label;
          },
          maxRotation: 45,
          minRotation: 0
        }
      },
      y: {
        title: {
          display: true,
          text: 'Count'
        },
        beginAtZero: true
      }
    }
  };


  const trendData = trends?.daily_counts
  ? {
    labels: trends.daily_counts.map((d: any) => {
      const date = new Date(d.date);
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }),
    datasets: [{
      label: "Avg Detection Confidence",
      data: accuracyTrends.map((t) => t.avg_confidence),
      borderColor: "#94B4C1",
      backgroundColor: "rgba(148, 180, 193, 0.2)",
      tension: 0.3,
      fill: true,
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
      title: {
        display: true,
        text: "Detection Accuracy Trends"
      },
      tooltip: {
        callbacks: {
          label: function(context: import("chart.js").TooltipItem<"line">) {
            return `Avg Confidence: ${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Avg Confidence'
        },
        beginAtZero: true,
        max: 1
      }
    }
  };

    useEffect(() => {
    if (isAuthenticated) {
      fetchFiltered();
    }
  }, [isAuthenticated, fetchFiltered]);


  return (
    <>
      {/* Header at the top */}
      <header className="w-full bg-[#547792] text-white px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-md">
        <h1 className="text-2xl font-bold">Traffic Intelligence Hub</h1>
        {isAuthenticated ? (
          <button
            onClick={() => {
              logout();
              router.push('/login');
            }}
            className="bg-red-400 text-white font-semibold px-4 py-2 rounded hover:bg-red-500"
          >
            Logout
          </button>
        ) : (
          <Link href="/login">
            <button className="bg-[#ECEFCA] text-[#213448] font-semibold px-4 py-2 rounded hover:bg-[#d8e4aa]">
              Login
            </button>
          </Link>
        )}
      </header>

      <main className="min-h-screen flex flex-col md:flex-row bg-[#213448] text-white font-sans">
        {/* Sidebar */}
        <aside className="md:w-1/4 bg-[#547792] p-4 flex flex-col space-y-4">
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
                  {files.map((f) => f.name).join(', ')}
                </p>
              )}
            </div>
            <button
              onClick={() => uploadFiles(token, isAuthenticated, fetchFiltered, setPlateFrequency, setAccuracyTrends, history, fetchFullResult, setIsSaved, setHistory, setResult, refreshAnalytics, refreshReports)}
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
                      onClick={() => {
                        if (isAuthenticated) {
                          fetchFullResult(h.id);
                        } else {
                          setResult(h);
                          setIsSaved(false);
                        }
                      }}
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
                          deleteRecord(h.id, isAuthenticated);
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
              </>
            ) : (
              <p className="text-sm mt-2 text-[#ECEFCA]">No history yet.</p>
            )}
            </div>
          </aside>
         
        {/* Main Viewer */}
        <section className="md:w-2/4 p-6 overflow-y-auto">
          {result ? (
            <>
              <h2 className="text-xl font-semibold mb-2 text-[#ECEFCA]">Detection Results</h2>
              <p className="text-sm text-gray-300 mb-4">{result.filename}</p>
              {!isSaved && (
                <p className="text-yellow-300 text-sm mb-4">
                  ⚠️ This result is <strong>not saved</strong> and will be lost after you leave this page. <a href="/login" className="underline">Login</a> to save your uploads.
                </p>
              )}
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
                {result.detections?.filter((d) => d.plate_crop_path).length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {result.detections.map((d: any, idx: number) => (
                      <div key={idx} className="bg-[#547792] p-3 rounded border border-[#ECEFCA] text-sm">
                        <img
                          src={`http://192.168.50.143:8000${d.plate_crop_path}`}
                          alt={`Plate ${idx}`}
                          className="w-full mb-2 border rounded"
                        />
                        <p><strong>Plate:</strong> {d.plate_string ? d.plate_string : "N/A"}</p>
                        <p><strong>Confidence:</strong> {d.plate_confidence ? `${(d.plate_confidence * 100).toFixed(2)}%` : 'N/A'}</p>
                        <p>
                          <strong>Characters:</strong>{" "}
                          {d.characters?.map((c: any) => charMap[c.class_id] || "?").join('') || "N/A"}
                        </p>
                        <a
                          href={`http://192.168.50.143:8000${d.plate_crop_path}`}
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
        {!isAuthenticated && (
          <p className="text-center text-yellow-300 my-6">
            Log in to save and view more analytics on your data!{" "}
            <Link href="/login" className="underline">
              Login
            </Link>
          </p>
        )}
        {isAuthenticated && (
          <>
            <aside className="md:w-1/4 bg-[#1B2C3E] p-6 border-l border-[#ECEFCA]">
              <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">
                📈 Detection Accuracy Trends
              </h3>
              {accuracyTrends.length > 0 ? (
                <Line data={trendData} options={trendOptions} />
              ) : (
                <p className="text-sm text-[#ECEFCA]">No accuracy data yet.</p>
              )}
              <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">
                📊 Plate Frequency Chart
              </h3>
              {plateFrequency.length > 0 ? (
                <Bar data={chartData} options={chartOptions} />
              ) : (
                <p className="text-sm text-[#ECEFCA]">No frequency data yet.</p>
              )}
              <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">📊 Analytics Report</h3>
                <div className="mb-2">
                  <select
                    value={reportRange}
                    onChange={(e) => setReportRange(e.target.value as any)}
                    className="bg-[#ECEFCA] text-[#213448] rounded px-2 py-1"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>

                <div className="bg-[#547792] p-4 rounded border border-[#ECEFCA] text-sm whitespace-pre-wrap mb-4">
                  {reportLoading ? "Loading..." : analyticsReport}
                </div>

                {trends && trends.daily_counts.length > 0 && (
                  <div className="mt-4">
                    <Bar
                      data={{
                        labels: trends.daily_counts.map((d: any) => d.date),
                        datasets: [{
                          label: "Detections per day",
                          data: trends.daily_counts.map((d: any) => d.count),
                          backgroundColor: "#94B4C1"
                        }]
                      }}
                      options={{ responsive: true }}
                    />
                  </div>
                )}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-[#94B4C1] mb-2">💬 Ask a question</h3>
                <div className="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-2">
                  <input
                    type="text"
                    value={llmQuestion}
                    onChange={(e) => setLlmQuestion(e.target.value)}
                    placeholder="e.g. What plates were most common yesterday?"
                    className="flex-1 p-2 rounded bg-[#ECEFCA] text-[#213448]"
                  />
                  <button onClick={() => askLLM(llmQuestion)} className="bg-[#ECEFCA] text-[#213448] px-4 py-2 rounded font-semibold text-sm">
                    Ask
                  </button>
                </div>
                {llmAnswer && (
                  <div className="mt-4 bg-[#547792] p-4 rounded border border-[#ECEFCA]">
                    <p>{llmAnswer}</p>
                  </div>
                )}
              </div>
              <button
                onClick={() => setDevPanelOpen((prev) => !prev)}
                className="fixed bottom-4 right-4 bg-[#94B4C1] text-[#213448] px-4 py-2 rounded-lg font-bold shadow-lg z-50"
              >
                {devPanelOpen ? 'Close Assistant' : 'Open Assistant'}
              </button>

              {devPanelOpen && (
                <div className="md:w-1/4 bg-[#1B2C3E] p-6 border-l border-[#ECEFCA]">
                  <h3 className="text-lg font-semibold mb-4 text-[#94B4C1]">🛠 Developer Assistant</h3>
                  <textarea
                    placeholder="Ask why detection failed..."
                    className="w-full p-2 rounded bg-[#ECEFCA] text-[#213448] h-24"
                    value={devQuestion}
                    onChange={(e) => setDevQuestion(e.target.value)}
                  />
                  <button
                    onClick={() => askDevAssistant(devQuestion, result)}
                    disabled={loadingAnswer}
                    className="mt-2 w-full bg-[#94B4C1] text-[#213448] py-2 rounded font-semibold"
                  >
                    {loadingAnswer ? "Thinking..." : "Ask"}
                  </button>

                  {devAnswer && (
                    <div className="mt-4 bg-[#547792] p-4 rounded-lg border border-[#ECEFCA] text-sm whitespace-pre-wrap">
                      {devAnswer}
                    </div>
                  )}
                </div>
              )}
            </aside>

          </>
        )}
      </main>
    </>
  );
}