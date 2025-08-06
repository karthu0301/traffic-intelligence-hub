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
  BarElement,
  Filler
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
  Legend,
  Filler
);

export default function Home() {
  const router = useRouter();
  const { token, isAuthenticated, logout } = useAuth();
  const { files, setFiles, uploadFiles } = useUploader();
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
    const { llmAnswer, devAnswer, loadingAnswer, askLLM, askDevAssistant } = useLLM();
    const [isSaved, setIsSaved] = useState(true);
    const [llmQuestion, setLlmQuestion] = useState("");
    const [devQuestion, setDevQuestion] = useState("");
    const [devPanelOpen, setDevPanelOpen] = useState(false);
    const [reportRange, setReportRange] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
    const { chartData, chartOptions, trendData, trendOptions,plateFrequency, setPlateFrequency, accuracyTrends, setAccuracyTrends, refresh: refreshAnalytics } = useAnalytics(reportRange)
    const { report: analyticsReport, trends, loading: reportLoading, refresh: refreshReports, getStructuredReport, exportCSV } = useReports(reportRange, true);


    useEffect(() => {
    if (isAuthenticated) {
      fetchFiltered();
    }
  }, [isAuthenticated, fetchFiltered]);


return (
    <>
      {/* Header */}
      <header className="w-full bg-slate-800 text-gray-100 px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-lg transition-colors duration-200">
        <h1 className="text-2xl font-bold">Traffic Intelligence Hub</h1>
        {isAuthenticated ? (
          <button
            onClick={() => {
              logout();
              router.push('/login');
            }}
            className="bg-red-600 hover:bg-red-500 text-gray-100 font-semibold px-4 py-2 rounded-lg transition-colors duration-200"
          >
            Logout
          </button>
        ) : (
          <Link href="/login">
            <button className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 font-semibold px-4 py-2 rounded-lg transition-colors duration-200">
              Login
            </button>
          </Link>
        )}
      </header>

      <main className="min-h-screen flex flex-col md:flex-row bg-slate-900 text-gray-100 font-sans transition-colors duration-200">
        {/* Sidebar */}
        <aside className="md:w-1/4 bg-slate-800 p-4 flex flex-col space-y-4 shadow-lg rounded-lg transition-colors duration-200">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <label className="bg-blue-500 text-gray-900 dark:text-gray-100 font-semibold text-sm px-3 py-1.5 rounded-lg cursor-pointer transition-colors duration-200">
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
              className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg font-semibold text-sm transition-colors duration-200"
            >
              Upload Image(s)
            </button>
          </div>

          <div className="flex flex-col mt-4">
            {history.length > 0 ? (
              <>
                <h2 className="text-lg font-semibold mb-2"> Upload History</h2>
                <a
                  href={`http://192.168.50.143:8000/download-all?plate_query=${searchTerm}&filename_query=${searchTerm}`}
                  download
                  className="text-sm text-blue-400 underline hover:text-blue-300 transition-colors duration-200 block mt-2 mb-4 "
                >
                  ⬇ Download Results (ZIP)
                </a>
                            <input
              type="text"
              placeholder="Search by filename or plate..."
              className="w-full p-2 mb-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <div className="flex space-x-2 mb-2 mb-4">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200 "
              >
                <option value="timestamp">Sort by Timestamp</option>
                <option value="filename">Sort by Filename</option>
              </select>
              <select
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
                <ul className="space-y-2 overflow-y-auto max-h-[60vh] pr-2">
                  {history.map((h, idx) => (
                    <li
                      key={idx}
                      className="flex items-center space-x-2 bg-blue-500 p-3 rounded-lg cursor-pointer hover:bg-blue-400 transition-colors duration-200"
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
                        className="w-12 h-12 object-cover rounded-sm border border-gray-600"
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{h.filename}</p>
                        <p className="text-xs text-gray-700 dark:text-gray-400">
                          {h.timestamp?.slice(0, 19).replace("T", " ")}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteRecord(h.id, isAuthenticated);
                        }}
                        className="text-red-600 hover:text-red-500 cursor-pointer text-lg transition-colors duration-200"
                        title="Delete"
                      >
                        …{/* SVG */}
                      </button>
                    </li>
                  ))}
                </ul>
                <div className="flex items-center justify-between mt-4 text-sm">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50 transition-colors duration-200"
                  >
                    ⬅ Prev
                  </button>
                  <span>
                    Page {currentPage} of {Math.ceil(totalResults / pageSize)}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => p + 1)}
                    disabled={currentPage >= Math.ceil(totalResults / pageSize)}
                    className="px-3 py-1 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50 transition-colors duration-200"
                  >
                    Next ➡
                  </button>
                </div>
              </>
            ) : (
              <p className="text-sm mt-2 text-gray-100">No history yet.</p>
            )}
          </div>
        </aside>

        {/* Main Viewer */}
        <section className="md:w-2/4 p-6 overflow-y-auto">
          {result ? (
            <>
              <h2 className="text-xl font-semibold mb-2 text-gray-100">Detection Results</h2>
              <p className="text-sm text-gray-400 mb-4">{result.filename}</p>
              {!isSaved && (
                <p className="text-yellow-400 text-sm mb-4">
                  ⚠️ This result is <strong>not saved</strong> and will be lost. <a href="/login" className="underline text-blue-400 hover:text-blue-300 transition-colors duration-200">Login</a>.
                </p>
              )}

              {/* Annotated Image */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2 text-blue-500">Annotated Image</h3>
                <img
                  src={`http://192.168.50.143:8000${result.annotated_image}`}
                  alt="Annotated"
                  className="w-full max-w-4xl border-4 border-blue-500 rounded-lg shadow-lg"
                />
                <a
                  href={`http://192.168.50.143:8000${result.annotated_image}`}
                  download
                  className="text-blue-400 underline text-sm hover:text-blue-300 transition-colors duration-200"
                >
                  ⬇ Download Annotated Image
                </a>
              </div>

              {/* Detected Plates */}
              <div>
                <h3 className="text-lg font-semibold mb-2 text-blue-500">Detected Plates</h3>
                {result.detections?.filter((d: any) => d.plate_crop_path).length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {result.detections.map((d: any, idx: number) => (
                      <div key={idx} className="bg-slate-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-lg text-sm transition-colors duration-200">
                        <img
                          src={`http://192.168.50.143:8000${d.plate_crop_path}`}
                          alt={`Plate ${idx}`}
                          className="w-full mb-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                        />
                        <p className="text-gray-100"><strong>Plate:</strong> {d.plate_string || "N/A"}</p>
                        <p className="text-gray-100"><strong>Confidence:</strong> {d.plate_confidence ? `${(d.plate_confidence * 100).toFixed(2)}%` : 'N/A'}</p>
                        <a
                          href={`http://192.168.50.143:8000${d.plate_crop_path}`}
                          download
                          className="text-blue-400 underline text-xs hover:text-blue-300 transition-colors duration-200"
                        >
                          ⬇ Download Crop
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400">No plates detected.</p>
                )}
              </div>
            </>
          ) : (
            <p className="text-gray-400">Upload an image to begin.</p>
          )}
        </section>

        {!isAuthenticated && (
          <p className="text-center text-yellow-400 my-6">
            Log in to save and view more analytics!{" "}
            <Link href="/login" className="underline text-blue-400 hover:text-blue-300 transition-colors duration-200">
              Login
            </Link>
          </p>
        )}

        {isAuthenticated && (
          <aside className="md:w-1/4 bg-slate-800 p-6 border-l border-blue-500 shadow-lg transition-colors duration-200">
            <h3 className="text-lg font-semibold mb-4 text-blue-500">Detection Accuracy Trends</h3>
            {accuracyTrends.length > 0 ? <Line data={trendData} options={trendOptions} /> : <p className="text-sm text-gray-100">No data yet.</p>}

            <h3 className="text-lg font-semibold mb-4 text-blue-500">Plate Frequency Chart</h3>
            {plateFrequency.length > 0 ? <Bar data={chartData} options={chartOptions} /> : <p className="text-sm text-gray-100">No data yet.</p>}

            <h3 className="text-lg font-semibold mb-4 text-blue-500">Analytics Report</h3>
            <div className="mb-2">
              <select
                value={reportRange}
                onChange={(e) => setReportRange(e.target.value as any)}
                className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            {reportLoading ? (
              <p className="text-gray-400 text-sm">Loading...</p>
            ) : (
              (() => {
                const structuredReport = getStructuredReport();

                return (
                  <div className="overflow-x-auto">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-gray-200 text-sm">
                        <strong>{structuredReport.length}</strong> uploaded file(s), <strong>
                          {structuredReport.reduce((acc, r) => acc + r.plates.length, 0)}
                        </strong> total plates detected.
                      </p>
                      <button
                        onClick={exportCSV}
                        className="bg-green-600 hover:bg-green-500 text-white px-3 py-1 rounded-md text-sm"
                      >
                        ⬇ Export as CSV
                      </button>
                    </div>
                    <table className="w-full text-sm text-left text-gray-300 mt-2">
                      <thead className="text-xs uppercase text-gray-400 border-b border-gray-700">
                        <tr>
                          <th className="py-2">Date</th>
                          <th className="py-2">Filename</th>
                          <th className="py-2">Detected Plates</th>
                        </tr>
                      </thead>
                      <tbody>
                        {structuredReport.map((entry, idx) => (
                          <tr key={idx} className="border-b border-gray-800 hover:bg-slate-800 transition">
                            <td className="py-2">{entry.date}</td>
                            <td className="py-2">{entry.filename}</td>
                            <td className="py-2 flex flex-wrap gap-2">
                              {entry.plates.map((plate, i) => (
                                <span key={i} className="bg-blue-600 text-white px-2 py-0.5 rounded-full text-xs">
                                  {plate}
                                </span>
                              ))}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()
            )}
            {/* Ask a question */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-blue-500 mb-2">💬 Ask a question</h3>
              <div className="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-2">
                <input
                  type="text"
                  value={llmQuestion}
                  onChange={(e) => setLlmQuestion(e.target.value)}
                  placeholder="e.g. What plates were most common yesterday?"
                  className="flex-1 p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
                />
                <button
                  onClick={() => askLLM(llmQuestion)}
                  className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg font-semibold text-sm transition-colors duration-200"
                >
                  Ask
                </button>
              </div>
              {llmAnswer && (
                <div className="mt-4 bg-slate-800 p-4 rounded-lg border border-blue-500 shadow-lg transition-colors duration-200">
                  <p className="text-gray-100">{llmAnswer}</p>
                </div>
              )}
            </div>

            {/* Dev assistant toggle */}
            <button
              onClick={() => setDevPanelOpen((prev) => !prev)}
              className="fixed bottom-4 right-4 bg-blue-500 hover:bg-blue-400 text-gray-100 px-4 py-2 rounded-lg font-bold shadow-lg transition-colors duration-200 z-50"
            >
              {devPanelOpen ? 'Close Assistant' : 'Open Assistant'}
            </button>

            {devPanelOpen && (
              <div className="md:w-1/4 bg-slate-800 p-6 border-l border-blue-500 shadow-lg transition-colors duration-200">
                <h3 className="text-lg font-semibold mb-4 text-blue-500">🛠 Developer Assistant</h3>
                <textarea
                  placeholder="Ask why detection failed..."
                  className="w-full p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 h-24 transition-colors duration-200"
                  value={devQuestion}
                  onChange={(e) => setDevQuestion(e.target.value)}
                />
                <button
                  onClick={() => askDevAssistant(devQuestion, result)}
                  disabled={loadingAnswer}
                  className="mt-2 w-full bg-blue-500 hover:bg-blue-400 text-gray-100 py-2 rounded-lg font-semibold transition-colors duration-200"
                >
                  {loadingAnswer ? "Thinking..." : "Ask"}
                </button>

                {devAnswer && (
                  <div className="mt-4 bg-slate-800 p-4 rounded-lg border border-blue-500 shadow-lg text-sm whitespace-pre-wrap transition-colors duration-200">
                    <p className="text-gray-100">{devAnswer}</p>
                  </div>
                )}
              </div>
            )}
          </aside>
        )}
      </main>
    </>
  );
}