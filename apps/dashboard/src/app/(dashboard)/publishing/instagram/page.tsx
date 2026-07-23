"use client";

import React, { useEffect, useState } from "react";
import { 
  Share2, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  ExternalLink,
  Sparkles,
  Layers,
  Sliders,
  Award,
  Plus,
  Eye,
  Heart,
  MessageSquare,
  Bookmark,
  Send,
  Zap,
  Check,
  RotateCcw
} from "lucide-react";

export default function InstagramPublishingPage() {
  const [qualityList, setQualityList] = useState<any[]>([]);
  const [selectedQualityId, setSelectedQualityId] = useState("");
  const [platformMediaType, setPlatformMediaType] = useState("Reels");
  const [provider, setProvider] = useState("instagram_provider");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("preview");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const qRes = await fetch("/api/v1/quality");
      if (qRes.ok) {
        const data = await qRes.json();
        // Filter approved QualityPackages
        setQualityList(data.filter((j: any) => j.status === "SUCCESS" && j.packages?.[0]?.is_approved_for_publishing));
      }

      const jobsRes = await fetch("/api/v1/publishing/instagram");
      if (jobsRes.ok) setJobs(await jobsRes.json());

      const metricsRes = await fetch("/api/v1/publishing/instagram/metrics");
      if (metricsRes.ok) setMetrics(await metricsRes.json());
    } catch (e) {
      console.error("Failed to load instagram assets:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQualityId) return;
    setSubmitting(true);
    try {
      const qJob = qualityList.find(j => j.id === selectedQualityId);
      const res = await fetch("/api/v1/publishing/instagram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          quality_package_id: qJob.packages[0].id,
          platform_media_type: platformMediaType,
          provider,
          priority 
        })
      });
      if (res.ok) {
        setSelectedQualityId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/publishing/instagram/${id}/retry`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Retry failed:", e);
    }
  };

  const handleSync = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/publishing/instagram/${id}/sync`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Sync failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/publishing/instagram/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) setSelectedJob(null);
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;
  const activePub = activePkg?.publications?.[0] || null;
  const activeInsights = activePub?.insights?.[activePub.insights.length - 1] || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-pink-500 via-rose-400 to-orange-400 bg-clip-text text-transparent flex items-center gap-3">
            <span>Instagram Publishing Provider</span>
            <span className="text-xs bg-pink-950/80 text-pink-300 border border-pink-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
              Graph API v19.0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated multi-format publishing for Reels and Feed posts with Quality Gate validation, PlatformProfile spec verification, and Graph API engagement metrics.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-pink-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Connected Account</div>
              <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <span>@aates_official</span>
                <span className="text-[10px] bg-emerald-950 text-emerald-300 px-1.5 py-0.2 rounded font-mono">OAuth Active</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Grid */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-pink-400" />
              Queued
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-rose-400 animate-pulse" />
              Uploading
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_processing}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
              Published
            </div>
            <div className="text-2xl font-black text-emerald-400">{metrics.total_publications}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
              Failed
            </div>
            <div className="text-2xl font-black text-rose-400">{metrics.jobs_failed + metrics.jobs_cancelled}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20 col-span-2">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Eye className="h-3.5 w-3.5 text-orange-400" />
              Total Instagram Views
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.total_views.toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & Queue */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Submit Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Share2 className="h-5 w-5 text-pink-400" />
              Publish to Instagram
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Approved Quality Package</label>
                <select
                  value={selectedQualityId}
                  onChange={(e) => setSelectedQualityId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-xs focus:border-pink-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Approved Package --</option>
                  {qualityList.map((j) => (
                    <option key={j.id} value={j.id}>
                      Approved Package v{j.packages?.[0]?.version} (Readiness Score: {j.packages?.[0]?.production_readiness_score})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Media Format & Profile</label>
                <div className="grid grid-cols-2 gap-3">
                  {["Reels", "Feed"].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setPlatformMediaType(t)}
                      className={`p-3 rounded-xl border text-xs font-bold transition-all ${platformMediaType === t ? 'bg-pink-600 text-white border-pink-500 shadow-lg shadow-pink-900/30' : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-900'}`}
                    >
                      Instagram {t}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-pink-600 via-rose-600 to-orange-500 hover:opacity-95 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-pink-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedQualityId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing Upload...' : `Publish to Instagram ${platformMediaType}`}
              </button>
            </form>
          </div>

          {/* History Queue List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-rose-400" />
              Publishing Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading publishing records...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active publishing jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  const pkg = job.packages?.[0];
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-pink-950/60 text-pink-300 border border-pink-800/50";
                  if (job.status === "SUCCESS") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-pink-500/80 shadow-md shadow-pink-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          Instagram {job.platform_media_type} Job ({job.provider})
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {job.status}
                        </span>
                      </div>

                      {job.status === "PROCESSING" && (
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-[11px] font-medium text-pink-400">
                            <span>Stage: {job.stage}</span>
                            <span>{Math.round(job.progress * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-pink-500 to-rose-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div className="flex items-center gap-1.5">
                          <span>Format: Instagram {job.platform_media_type}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {job.status === "FAILED" && (
                            <button
                              onClick={(e) => { e.stopPropagation(); handleRetry(job.id); }}
                              className="text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1"
                            >
                              <RotateCcw className="h-3 w-3" /> Retry
                            </button>
                          )}
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(job.id); }}
                            className="text-rose-400 hover:text-rose-300 font-bold"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Publication Details Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-pink-400 uppercase tracking-widest">
                    Publication Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                    <span>Instagram {activeJob.platform_media_type}</span>
                    {activePub && (
                      <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded font-mono">
                        ID: {activePub.instagram_media_id}
                      </span>
                    )}
                  </h3>
                </div>

                {activePub && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSync(activeJob.id)}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Sync Insights
                    </button>
                    <a
                      href={activePub.permalink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-gradient-to-r from-pink-600 to-rose-600 hover:opacity-90 text-white p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-pink-900/20"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      View on Instagram
                    </a>
                  </div>
                )}
              </div>

              {activeJob.status === "SUCCESS" && activePub && (
                <div className="flex flex-col gap-6">

                  {/* Nav Tabs */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "preview", label: "Instagram Visual Mockup", icon: Eye },
                      { id: "insights", label: "Engagement Insights", icon: Activity },
                      { id: "attempts", label: "API Attempt Logs", icon: Sliders },
                      { id: "profile", label: "PlatformProfile Spec", icon: Award }
                    ].map(t => (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTab(t.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${selectedTab === t.id ? 'bg-pink-600 text-white shadow-lg shadow-pink-900/30' : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'}`}
                      >
                        <t.icon className="h-3.5 w-3.5" />
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab 1: Instagram Visual Mockup */}
                  {selectedTab === "preview" && (
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                      
                      {/* Simulated Instagram Phone Mockup */}
                      <div className="md:col-span-5 bg-slate-950 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 max-w-sm mx-auto shadow-2xl">
                        <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                          <div className="flex items-center gap-2">
                            <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-yellow-400 via-rose-500 to-purple-600 p-0.5">
                              <div className="h-full w-full bg-slate-950 rounded-full flex items-center justify-center text-[10px] font-black text-white">
                                AA
                              </div>
                            </div>
                            <span className="text-xs font-bold text-slate-200">aates_official</span>
                          </div>
                          <span className="text-[10px] text-slate-500 font-bold">Sponsored</span>
                        </div>

                        {/* Media Canvas Mock */}
                        <div className="h-64 bg-gradient-to-b from-slate-900 via-slate-950 to-pink-950/40 rounded-xl border border-slate-850 flex items-center justify-center relative overflow-hidden">
                          <Share2 className="h-10 w-10 text-pink-500/40 animate-pulse" />
                          <span className="absolute bottom-2 right-2 bg-black/70 px-2 py-0.5 rounded text-[9px] font-mono text-slate-300">
                            Instagram {activeJob.platform_media_type}
                          </span>
                        </div>

                        {/* Interaction Bar */}
                        <div className="flex items-center justify-between text-slate-400 py-1">
                          <div className="flex items-center gap-3">
                            <Heart className="h-5 w-5 text-rose-500 fill-rose-500/20" />
                            <MessageSquare className="h-5 w-5 hover:text-slate-200" />
                            <Send className="h-5 w-5 hover:text-slate-200" />
                          </div>
                          <Bookmark className="h-5 w-5 hover:text-slate-200" />
                        </div>

                        {/* Caption & Hashtags */}
                        <div className="text-xs space-y-1 text-slate-300">
                          <span className="font-bold text-slate-100">aates_official </span>
                          <span className="whitespace-pre-line text-slate-300">{activePub.caption}</span>
                        </div>
                      </div>

                      {/* Info Metadata */}
                      <div className="md:col-span-7 space-y-4 text-xs">
                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                          <div className="text-[10px] font-bold text-pink-400 uppercase tracking-widest">Publication Metadata</div>
                          <div className="flex justify-between py-1 border-b border-slate-900">
                            <span className="text-slate-400">Media ID:</span>
                            <span className="font-mono text-slate-200">{activePub.instagram_media_id}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-slate-900">
                            <span className="text-slate-400">Container ID:</span>
                            <span className="font-mono text-slate-200">{activePub.container_id}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-slate-900">
                            <span className="text-slate-400">Visibility:</span>
                            <span className="font-bold text-emerald-400">{activePub.visibility}</span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-slate-400">Published At:</span>
                            <span className="text-slate-300">{new Date(activePub.published_at).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                    </div>
                  )}

                  {/* Tab 2: Engagement Insights */}
                  {selectedTab === "insights" && activeInsights && (
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-pink-400 uppercase tracking-widest">Real-Time Graph API Insight Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Views</div>
                          <div className="text-2xl font-black text-slate-100">{activeInsights.views.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Reach</div>
                          <div className="text-2xl font-black text-slate-100">{activeInsights.reach.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Likes</div>
                          <div className="text-2xl font-black text-rose-400">{activeInsights.likes.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Comments</div>
                          <div className="text-2xl font-black text-pink-400">{activeInsights.comments.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Shares</div>
                          <div className="text-2xl font-black text-emerald-400">{activeInsights.shares.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Saves</div>
                          <div className="text-2xl font-black text-orange-400">{activeInsights.saves.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Profile Visits</div>
                          <div className="text-2xl font-black text-purple-400">{activeInsights.profile_visits.toLocaleString()}</div>
                        </div>
                        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Engagement Rate</div>
                          <div className="text-2xl font-black text-pink-400">{Math.round(activeInsights.engagement_rate * 100)}%</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: API Attempt History */}
                  {selectedTab === "attempts" && activeJob.attempts_history && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-pink-400 uppercase tracking-widest">Publishing Attempt History & Latency Log</h4>
                      <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden text-xs">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="border-b border-slate-850 bg-slate-900/60 text-slate-400 font-bold uppercase text-[10px] tracking-wider">
                              <th className="p-3">Attempt #</th>
                              <th className="p-3">API Endpoint</th>
                              <th className="p-3">HTTP Status</th>
                              <th className="p-3">Latency</th>
                              <th className="p-3">Timestamp</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-900 text-slate-300 font-medium">
                            {activeJob.attempts_history.map((att: any) => (
                              <tr key={att.id} className="hover:bg-slate-900/40">
                                <td className="p-3 font-bold text-slate-200">Attempt {att.attempt_number}</td>
                                <td className="p-3 font-mono text-[11px] text-slate-400">{att.api_endpoint}</td>
                                <td className="p-3">
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                                    {att.http_status_code} OK
                                  </span>
                                </td>
                                <td className="p-3 text-pink-400 font-bold">{att.latency_ms}ms</td>
                                <td className="p-3 text-slate-500">{new Date(att.created_at).toLocaleTimeString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Tab 4: PlatformProfile Specification */}
                  {selectedTab === "profile" && (
                    <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4 text-xs">
                      <h4 className="text-xs font-bold text-pink-400 uppercase tracking-widest">Active PlatformProfile Spec</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Format</div>
                          <div className="text-slate-200 font-bold text-sm">Instagram {activeJob.platform_media_type}</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Aspect Ratio</div>
                          <div className="text-slate-200 font-bold text-sm">9:16 (Vertical)</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Max Hashtags</div>
                          <div className="text-slate-200 font-bold text-sm">30 Hashtags</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Max Duration</div>
                          <div className="text-slate-200 font-bold text-sm">90.0 Seconds</div>
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Share2 className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">Instagram Publishing Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active publishing job from the left queue to view visual mockup previews, Graph API attempt history, and engagement metrics.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
