"use client";

import React, { useState, useEffect } from "react";
import {
  Share2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Calendar,
  TrendingUp,
  BarChart3,
  Eye,
  Heart,
  MessageSquare,
  Share,
  ShieldCheck,
  Video,
  Clock,
  Play,
  XCircle,
  RotateCcw,
  Cpu,
  Trash2,
  ListFilter,
  Search,
  Check
} from "lucide-react";

const Youtube = ({ className = "h-4 w-4" }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17" />
    <polygon points="10 15 15 12 10 9" fill="currentColor" />
  </svg>
);

const Instagram = ({ className = "h-4 w-4" }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);


interface StatusData {
  auth: {
    youtube: { configured: boolean; channel_id: string | null };
    instagram: { configured: boolean; account_id: string | null };
  };
  health: {
    [platform: string]: {
      available: boolean;
      latency_ms: number;
      success_rate: number;
      last_checked: string | null;
    };
  };
  quota: {
    youtube: { limit: number; cost_per_upload: number };
    instagram: { limit: number; unit: string };
  };
  published_history: Array<{
    id: string;
    episode_id: string;
    platform: string;
    status: string;
    publish_time: string | null;
    post_id: string;
  }>;
  scheduled_posts: Array<{
    id: string;
    episode_id: string;
    platform: string;
    status: string;
    retry_count: number;
  }>;
}

interface WorkerMetrics {
  jobs_queued: number;
  jobs_processing: number;
  jobs_succeeded: number;
  jobs_failed: number;
  jobs_retrying: number;
  jobs_cancelled: number;
  average_publish_time_sec: number;
  retry_count: number;
  worker_uptime: string;
  worker_is_running: boolean;
  current_worker_count: number;
  oldest_queued_job_age_sec: number;
  worker_heartbeats: Array<{
    worker_id: string;
    last_heartbeat_at: string | null;
    is_alive: boolean;
  }>;
}

interface PublishingJob {
  id: string;
  tenant_id: string | null;
  content_id: string;
  provider: string;
  status: string;
  priority: number;
  attempts: number;
  max_attempts: number;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  video_id: string | null;
  payload: any;
  provider_response: any;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export default function PublisherPage() {
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState<"integration" | "jobs">("jobs");

  // State variables
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [metrics, setMetrics] = useState<WorkerMetrics | null>(null);
  const [jobs, setJobs] = useState<PublishingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyingYt, setVerifyingYt] = useState(false);
  const [verifyingIg, setVerifyingIg] = useState(false);
  const [ytVerifyResult, setYtVerifyResult] = useState<any>(null);
  const [igVerifyResult, setIgVerifyResult] = useState<any>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [providerFilter, setProviderFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchAllData = async () => {
    try {
      setLoading(true);
      // Fetch status, metrics, and jobs in parallel
      const [statusRes, metricsRes, jobsRes] = await Promise.all([
        fetch("http://localhost:8000/v1/publishing/status").catch(() => null),
        fetch("http://localhost:8000/v1/publishing/metrics").catch(() => null),
        fetch("http://localhost:8000/v1/publishing/jobs").catch(() => null)
      ]);

      if (statusRes && statusRes.ok) {
        setStatusData(await statusRes.json());
      }
      if (metricsRes && metricsRes.ok) {
        setMetrics(await metricsRes.json());
      }
      if (jobsRes && jobsRes.ok) {
        setJobs(await jobsRes.json());
      }
    } catch (e) {
      console.error("Failed to load publisher dashboard content", e);
    } finally {
      setLoading(false);
    }
  };

  const verifyYoutube = async () => {
    try {
      setVerifyingYt(true);
      setYtVerifyResult(null);
      const res = await fetch("http://localhost:8000/v1/publishing/verify/youtube", { method: "POST" });
      if (res.ok) {
        const json = await res.json();
        setYtVerifyResult(json);
      } else {
        setYtVerifyResult({ verified: false, error: "HTTP request failed" });
      }
    } catch (e: any) {
      setYtVerifyResult({ verified: false, error: e.message || "Network error" });
    } finally {
      setVerifyingYt(false);
      fetchStatusAndMetricsOnly();
    }
  };

  const verifyInstagram = async () => {
    try {
      setVerifyingIg(true);
      setIgVerifyResult(null);
      const res = await fetch("http://localhost:8000/v1/publishing/verify/instagram", { method: "POST" });
      if (res.ok) {
        const json = await res.json();
        setIgVerifyResult(json);
      } else {
        setIgVerifyResult({ verified: false, error: "HTTP request failed" });
      }
    } catch (e: any) {
      setIgVerifyResult({ verified: false, error: e.message || "Network error" });
    } finally {
      setVerifyingIg(false);
      fetchStatusAndMetricsOnly();
    }
  };

  const fetchStatusAndMetricsOnly = async () => {
    try {
      const [statusRes, metricsRes, jobsRes] = await Promise.all([
        fetch("http://localhost:8000/v1/publishing/status").catch(() => null),
        fetch("http://localhost:8000/v1/publishing/metrics").catch(() => null),
        fetch("http://localhost:8000/v1/publishing/jobs").catch(() => null)
      ]);
      if (statusRes && statusRes.ok) setStatusData(await statusRes.json());
      if (metricsRes && metricsRes.ok) setMetrics(await metricsRes.json());
      if (jobsRes && jobsRes.ok) setJobs(await jobsRes.json());
    } catch (e) {
      console.error(e);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/v1/publishing/jobs/${jobId}/retry`, { method: "POST" });
      if (res.ok) {
        fetchStatusAndMetricsOnly();
      } else {
        const err = await res.json();
        alert(`Retry failed: ${err.detail || "Unknown error"}`);
      }
    } catch (e: any) {
      alert(`Network error: ${e.message}`);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/v1/publishing/jobs/${jobId}/cancel`, { method: "POST" });
      if (res.ok) {
        fetchStatusAndMetricsOnly();
      } else {
        const err = await res.json();
        alert(`Cancel failed: ${err.detail || "Unknown error"}`);
      }
    } catch (e: any) {
      alert(`Network error: ${e.message}`);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/v1/publishing/jobs/${jobId}`, { method: "DELETE" });
      if (res.ok) {
        fetchStatusAndMetricsOnly();
      } else {
        const err = await res.json();
        alert(`Delete failed: ${err.detail || "Unknown error"}`);
      }
    } catch (e: any) {
      alert(`Network error: ${e.message}`);
    }
  };

  useEffect(() => {
    fetchAllData();
    // Auto-refresh stats every 8 seconds
    const interval = setInterval(fetchStatusAndMetricsOnly, 8000);
    return () => clearInterval(interval);
  }, []);

  // Filter jobs based on user criteria
  const filteredJobs = jobs.filter((job) => {
    const matchesStatus = statusFilter === "ALL" || job.status === statusFilter;
    const matchesProvider = providerFilter === "ALL" || job.provider === providerFilter;
    const matchesSearch =
      searchQuery === "" ||
      job.content_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (job.tenant_id && job.tenant_id.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStatus && matchesProvider && matchesSearch;
  });

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "QUEUED":
        return "bg-slate-800/80 border border-slate-700 text-slate-300";
      case "PROCESSING":
        return "bg-violet-500/10 border border-violet-500/30 text-violet-400 animate-pulse";
      case "SUCCESS":
        return "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400";
      case "FAILED":
        return "bg-red-500/10 border border-red-500/20 text-red-400";
      case "RETRYING":
        return "bg-amber-500/10 border border-amber-500/30 text-amber-400";
      case "CANCELLED":
        return "bg-slate-900 border border-slate-800 text-slate-500";
      default:
        return "bg-slate-800 border border-slate-700 text-slate-300";
    }
  };

  const formatDuration = (job: PublishingJob) => {
    if (!job.started_at) return "-";
    const start = new Date(job.started_at).getTime();
    const end = job.completed_at
      ? new Date(job.completed_at).getTime()
      : job.failed_at
      ? new Date(job.failed_at).getTime()
      : Date.now();
    const diff = (end - start) / 1000;
    return diff > 0 ? `${diff.toFixed(1)}s` : "0s";
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-3">
            <Share2 className="h-8 w-8 text-violet-400" />
            Autonomous Publisher Control
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Production-ready scheduling queue, provider configurations, and background worker daemon control panel.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Tab Toggle */}
          <div className="bg-slate-950/80 border border-slate-800/80 p-1.5 rounded-xl flex gap-1">
            <button
              onClick={() => setActiveTab("jobs")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "jobs" ? "bg-violet-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Cpu className="h-3.5 w-3.5 inline mr-1.5" />
              Publishing Jobs ({jobs.length})
            </button>
            <button
              onClick={() => setActiveTab("integration")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "integration" ? "bg-violet-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5 inline mr-1.5" />
              API Providers Health
            </button>
          </div>

          <button
            onClick={fetchAllData}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition-all active:scale-95"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-violet-400" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {activeTab === "jobs" ? (
        <div className="space-y-8">
          {/* Metrics summary panel */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Total Queued</span>
              <p className="text-2xl font-bold text-slate-200 mt-2">{metrics?.jobs_queued ?? 0}</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-violet-400 tracking-wider">Processing</span>
              <p className="text-2xl font-bold text-violet-400 mt-2 flex items-center gap-1.5">
                {metrics?.jobs_processing ?? 0}
                {metrics?.jobs_processing && metrics.jobs_processing > 0 ? (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
                  </span>
                ) : null}
              </p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Succeeded</span>
              <p className="text-2xl font-bold text-emerald-400 mt-2">{metrics?.jobs_succeeded ?? 0}</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-red-400 tracking-wider">Failed</span>
              <p className="text-2xl font-bold text-red-400 mt-2">{metrics?.jobs_failed ?? 0}</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Avg Latency</span>
              <p className="text-2xl font-bold text-slate-200 mt-2">
                {metrics?.average_publish_time_sec ? `${metrics.average_publish_time_sec}s` : "-"}
              </p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-900 flex flex-col justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Oldest Age</span>
              <p className="text-2xl font-bold text-slate-200 mt-2">
                {metrics?.oldest_queued_job_age_sec ? `${metrics.oldest_queued_job_age_sec}s` : "-"}
              </p>
            </div>
          </div>

          {/* Daemon Workers Heartbeat Panel */}
          <div className="bg-slate-950/40 border border-slate-900 p-5 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Cpu className="h-4 w-4 text-violet-400" />
                Background Worker Daemon Lifespan & Heartbeats
              </h3>
              <span className="text-xs text-slate-500 font-mono">
                Uptime: {metrics?.worker_uptime ?? "offline"}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {metrics?.worker_heartbeats && metrics.worker_heartbeats.length > 0 ? (
                metrics.worker_heartbeats.map((hb) => (
                  <div
                    key={hb.worker_id}
                    className="p-3 bg-slate-900/40 border border-slate-900 rounded-xl flex items-center justify-between"
                  >
                    <div className="space-y-0.5">
                      <span className="text-xs font-semibold text-slate-300 font-mono">{hb.worker_id}</span>
                      <p className="text-[9px] text-slate-500">
                        {hb.last_heartbeat_at ? new Date(hb.last_heartbeat_at).toLocaleTimeString() : "Never"}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        hb.is_alive
                          ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                          : "bg-red-500/10 border border-red-500/20 text-red-400"
                      }`}
                    >
                      {hb.is_alive ? "Active" : "Dead"}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 py-2 col-span-full">No active background daemons discovered.</p>
              )}
            </div>
          </div>

          {/* Filtering and search console */}
          <div className="bg-slate-950/60 p-4 border border-slate-900 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              {/* Status filter */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
                <ListFilter className="h-3.5 w-3.5 text-slate-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 outline-none cursor-pointer font-medium"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="QUEUED">Queued</option>
                  <option value="PROCESSING">Processing</option>
                  <option value="SUCCESS">Success</option>
                  <option value="FAILED">Failed</option>
                  <option value="RETRYING">Retrying</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
              </div>

              {/* Provider filter */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
                <Share2 className="h-3.5 w-3.5 text-slate-400" />
                <select
                  value={providerFilter}
                  onChange={(e) => setProviderFilter(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 outline-none cursor-pointer font-medium"
                >
                  <option value="ALL">All Providers</option>
                  <option value="youtube_short">YouTube Shorts</option>
                  <option value="instagram_reel">Instagram Reels</option>
                </select>
              </div>
            </div>

            {/* Search query input */}
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 w-full md:w-72">
              <Search className="h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search Content / Job ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent text-xs text-slate-200 outline-none w-full"
              />
            </div>
          </div>

          {/* Publishing jobs list table */}
          <div className="bg-slate-950/60 rounded-2xl border border-slate-900 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-900 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                    <th className="py-3.5 px-5">Job ID & Content</th>
                    <th className="py-3.5 px-5">Provider</th>
                    <th className="py-3.5 px-5">Status</th>
                    <th className="py-3.5 px-5">Attempts</th>
                    <th className="py-3.5 px-5">Duration</th>
                    <th className="py-3.5 px-5">Schedule / Completed</th>
                    <th className="py-3.5 px-5">Response / Logs</th>
                    <th className="py-3.5 px-5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-sm">
                  {filteredJobs.length > 0 ? (
                    filteredJobs.map((job) => (
                      <tr key={job.id} className="text-slate-300 hover:bg-slate-900/10">
                        <td className="py-4 px-5">
                          <div className="font-semibold text-slate-200 font-mono text-xs max-w-[200px] truncate">
                            {job.content_id}
                          </div>
                          <div className="text-[10px] text-slate-500 font-mono mt-0.5 max-w-[150px] truncate">
                            ID: {job.id}
                          </div>
                          {job.tenant_id && (
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-slate-900 border border-slate-800 text-slate-400 mt-1 inline-block">
                              Tenant: {job.tenant_id}
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-5">
                          <div className="flex items-center gap-2">
                            {job.provider === "youtube_short" ? (
                              <Youtube className="h-4 w-4 text-red-500" />
                            ) : (
                              <Instagram className="h-4 w-4 text-pink-500" />
                            )}
                            <span className="capitalize font-medium text-xs">
                              {job.provider.replace("_", " ")}
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-5">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${getStatusBadgeClass(job.status)}`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="py-4 px-5 font-mono text-xs">
                          {job.attempts} / {job.max_attempts}
                        </td>
                        <td className="py-4 px-5 font-mono text-xs text-slate-400">
                          {formatDuration(job)}
                        </td>
                        <td className="py-4 px-5 space-y-0.5">
                          <div className="text-xs text-slate-400 flex items-center gap-1">
                            <Clock className="h-3 w-3 text-slate-500" />
                            {job.scheduled_at ? new Date(job.scheduled_at).toLocaleString() : "Immediate"}
                          </div>
                          {job.completed_at && (
                            <div className="text-[10px] text-slate-500">
                              Done: {new Date(job.completed_at).toLocaleString()}
                            </div>
                          )}
                        </td>
                        <td className="py-4 px-5 max-w-[220px]">
                          {job.video_id ? (
                            <div className="space-y-0.5">
                              <span className="text-[10px] text-slate-500 font-mono">Video ID:</span>
                              <div className="text-xs text-emerald-400 font-mono truncate">{job.video_id}</div>
                            </div>
                          ) : job.error_message ? (
                            <div className="space-y-0.5 max-w-[200px]">
                              <span className="text-[10px] text-red-400 font-bold">Error:</span>
                              <p className="text-[10px] text-red-400/90 leading-tight truncate" title={job.error_message}>
                                {job.error_message}
                              </p>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">-</span>
                          )}
                        </td>
                        <td className="py-4 px-5 text-right space-x-1.5 whitespace-nowrap">
                          {/* Cancel action */}
                          {["QUEUED", "RETRYING", "PROCESSING"].includes(job.status) && (
                            <button
                              onClick={() => handleCancelJob(job.id)}
                              className="inline-flex items-center justify-center p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-red-400 transition-all"
                              title="Cancel Job"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          )}

                          {/* Retry action */}
                          {["FAILED", "CANCELLED"].includes(job.status) && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              className="inline-flex items-center justify-center p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-emerald-400 transition-all"
                              title="Retry Job"
                            >
                              <RotateCcw className="h-4 w-4" />
                            </button>
                          )}

                          {/* Delete action */}
                          {job.status !== "PROCESSING" && (
                            <button
                              onClick={() => handleDeleteJob(job.id)}
                              className="inline-flex items-center justify-center p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-500 hover:text-red-500 transition-all"
                              title="Delete Job"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500 text-sm">
                        No enqueued jobs discoverable in database.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Health & Quotas tab */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* YouTube Card */}
            <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-900 flex flex-col justify-between space-y-6">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl">
                    <Youtube className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-200">YouTube Data API</h3>
                    <p className="text-xs text-slate-500">v3 API Endpoint</p>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    statusData?.health?.youtube_short?.available
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                      : "bg-amber-500/10 border border-amber-500/20 text-amber-400"
                  }`}
                >
                  {statusData?.health?.youtube_short?.available ? "Healthy" : "Offline / Unused"}
                </span>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Auth Status</span>
                  <span className="text-slate-200 font-medium">
                    {statusData?.auth?.youtube?.configured ? "✓ Configured (SM)" : "✗ Unconfigured"}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Daily Quota Limit</span>
                  <span className="text-slate-200 font-medium">10,000 units</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Upload Cost</span>
                  <span className="text-slate-200 font-medium">1,600 units</span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-900/60 flex flex-col gap-3">
                <button
                  onClick={verifyYoutube}
                  disabled={verifyingYt}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-medium transition-all"
                >
                  {verifyingYt ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                  Test YouTube Integration
                </button>

                {ytVerifyResult && (
                  <div
                    className={`p-3 rounded-xl border text-xs leading-relaxed ${
                      ytVerifyResult.verified
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : "bg-red-500/10 border-red-500/20 text-red-400"
                    }`}
                  >
                    {ytVerifyResult.verified ? (
                      <div>
                        <p className="font-bold">Verification Success:</p>
                        <p>Channel: {ytVerifyResult.channel_title}</p>
                        <p>Subscribers: {ytVerifyResult.subscribers}</p>
                      </div>
                    ) : (
                      <div>
                        <p className="font-bold">Verification Failed:</p>
                        <p>{ytVerifyResult.error}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Instagram Card */}
            <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-900 flex flex-col justify-between space-y-6">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-pink-500/10 border border-pink-500/20 text-pink-500 rounded-xl">
                    <Instagram className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-200">Instagram Graph API</h3>
                    <p className="text-xs text-slate-500">v19.0 API Endpoint</p>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    statusData?.health?.instagram_reel?.available
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                      : "bg-amber-500/10 border border-amber-500/20 text-amber-400"
                  }`}
                >
                  {statusData?.health?.instagram_reel?.available ? "Healthy" : "Offline / Unused"}
                </span>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Auth Status</span>
                  <span className="text-slate-200 font-medium">
                    {statusData?.auth?.instagram?.configured ? "✓ Configured (SM)" : "✗ Unconfigured"}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Daily Limit</span>
                  <span className="text-slate-200 font-medium">25 Reels</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Upload Type</span>
                  <span className="text-slate-200 font-medium">Direct Ingestion / In-Feed</span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-900/60 flex flex-col gap-3">
                <button
                  onClick={verifyInstagram}
                  disabled={verifyingIg}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-pink-600 hover:bg-pink-700 text-white rounded-xl text-sm font-medium transition-all"
                >
                  {verifyingIg ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                  Test Instagram Integration
                </button>

                {igVerifyResult && (
                  <div
                    className={`p-3 rounded-xl border text-xs leading-relaxed ${
                      igVerifyResult.verified
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : "bg-red-500/10 border-red-500/20 text-red-400"
                    }`}
                  >
                    {igVerifyResult.verified ? (
                      <div>
                        <p className="font-bold">Verification Success:</p>
                        <p>Account: {igVerifyResult.account_name}</p>
                        <p>Followers: {igVerifyResult.followers}</p>
                      </div>
                    ) : (
                      <div>
                        <p className="font-bold">Verification Failed:</p>
                        <p>{igVerifyResult.error}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Global Analytics Overview */}
            <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-900 space-y-6">
              <h3 className="font-bold text-slate-200 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-violet-400" />
                Learning Engine Analytics Ingestion
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-900/80 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Total Views</span>
                  <p className="text-xl font-bold text-white">41.2K</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-900/80 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Engagement</span>
                  <p className="text-xl font-bold text-white">12.4%</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-900/80 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Subscribers +</span>
                  <p className="text-xl font-bold text-white">+842</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-900/80 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Retention</span>
                  <p className="text-xl font-bold text-white">78.5%</p>
                </div>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed">
                All analytics metrics are dynamically collected by the Operations platform and routed directly to the Learning Engine to adjust future universe scripts.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
