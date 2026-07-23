"use client";

import React, { useEffect, useState } from "react";
import { 
  Image as ImageIcon, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Download,
  Sparkles,
  Layers,
  GitCompare,
  Sliders,
  SlidersHorizontal,
  Eye,
  Plus,
  Zap,
  Target,
  LayoutGrid,
  TrendingUp,
  Award,
  Check
} from "lucide-react";

export default function ThumbnailsPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [imageList, setImageList] = useState<any[]>([]);
  const [videoList, setVideoList] = useState<any[]>([]);
  const [subtitleList, setSubtitleList] = useState<any[]>([]);
  const [musicList, setMusicList] = useState<any[]>([]);

  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedImageId, setSelectedImageId] = useState("");
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [selectedSubtitleId, setSelectedSubtitleId] = useState("");
  const [selectedMusicId, setSelectedMusicId] = useState("");
  const [provider, setProvider] = useState("template");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("gallery");
  const [diffVersionId, setDiffVersionId] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const scriptRes = await fetch("/api/v1/scripts");
      if (scriptRes.ok) {
        const data = await scriptRes.json();
        setScriptList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const imageRes = await fetch("/api/v1/images");
      if (imageRes.ok) {
        const data = await imageRes.json();
        setImageList(data.filter((j: any) => j.status === "SUCCESS"));
      }
      
      const videoRes = await fetch("/api/v1/videos");
      if (videoRes.ok) {
        const data = await videoRes.json();
        setVideoList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const subtitleRes = await fetch("/api/v1/subtitles");
      if (subtitleRes.ok) {
        const data = await subtitleRes.json();
        setSubtitleList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const musicRes = await fetch("/api/v1/music");
      if (musicRes.ok) {
        const data = await musicRes.json();
        setMusicList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const jobsRes = await fetch("/api/v1/thumbnails");
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data);
      }

      const metricsRes = await fetch("/api/v1/thumbnails/metrics");
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to load thumbnail assets:", e);
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
    if (!selectedScriptId || !selectedImageId || !selectedVideoId) return;
    setSubmitting(true);
    try {
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const imageJob = imageList.find(j => j.id === selectedImageId);
      const videoJob = videoList.find(j => j.id === selectedVideoId);
      const subtitleJob = subtitleList.find(j => j.id === selectedSubtitleId);
      const musicJob = musicList.find(j => j.id === selectedMusicId);

      const res = await fetch("/api/v1/thumbnails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptJob.packages[0].id,
          image_package_id: imageJob.packages[0].id,
          video_package_id: videoJob.packages[0].id, 
          subtitle_package_id: subtitleJob?.packages?.[0]?.id || null,
          music_package_id: musicJob?.packages?.[0]?.id || null,
          provider,
          priority 
        })
      });
      if (res.ok) {
        setSelectedScriptId("");
        setSelectedImageId("");
        setSelectedVideoId("");
        setSelectedSubtitleId("");
        setSelectedMusicId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegenerate = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/thumbnails/${id}/regenerate?layout_type=centered`, {
        method: "POST"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Regeneration failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/thumbnails/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;
  const diffVersion = activePkg?.versions?.find((v: any) => v.id === diffVersionId) || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 bg-clip-text text-transparent">
            AI Thumbnail Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Weighted multi-source frame selection, explicit text hierarchy, high-contrast layouts, dual heuristic & learned CTR prediction scoring.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-purple-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Thumbnail Daemon</div>
              <div className="text-sm font-bold text-slate-200">
                {metrics.worker_is_running ? `Active (${metrics.current_worker_count} render threads)` : 'Offline'}
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
              <Clock className="h-3.5 w-3.5 text-purple-400" />
              Queued
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-pink-400 animate-pulse" />
              Processing
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_processing}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
              Succeeded
            </div>
            <div className="text-2xl font-black text-emerald-400">{metrics.jobs_succeeded}</div>
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
              <RefreshCw className="h-3.5 w-3.5 text-purple-400 animate-spin" style={{ animationDuration: '6s' }} />
              Avg Mix Speed
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
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
              <Sparkles className="h-5 w-5 text-purple-400" />
              Generate Thumbnails
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Script Package</label>
                <select
                  value={selectedScriptId}
                  onChange={(e) => setSelectedScriptId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-purple-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Script --</option>
                  {scriptList.map((j) => (
                    <option key={j.id} value={j.id}>{j.packages?.[0]?.title || `Script ${j.id.slice(0,6)}`}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Image Package</label>
                <select
                  value={selectedImageId}
                  onChange={(e) => setSelectedImageId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-purple-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Image Package --</option>
                  {imageList.map((j) => (
                    <option key={j.id} value={j.id}>Images ({j.packages?.[0]?.resolution}) - {j.packages?.[0]?.style_preset}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">3. Video Package</label>
                <select
                  value={selectedVideoId}
                  onChange={(e) => setSelectedVideoId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-purple-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Video Package --</option>
                  {videoList.map((j) => (
                    <option key={j.id} value={j.id}>Video {j.packages?.[0]?.platform} ({j.packages?.[0]?.resolution})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Subtitle (Opt)</label>
                  <select
                    value={selectedSubtitleId}
                    onChange={(e) => setSelectedSubtitleId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-purple-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="">-- Optional --</option>
                    {subtitleList.map((j) => (
                      <option key={j.id} value={j.id}>Subtitles ({j.language})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Music (Opt)</label>
                  <select
                    value={selectedMusicId}
                    onChange={(e) => setSelectedMusicId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-purple-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="">-- Optional --</option>
                    {musicList.map((j) => (
                      <option key={j.id} value={j.id}>Music ({j.provider})</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedScriptId || !selectedImageId || !selectedVideoId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing...' : 'Generate High-CTR Thumbnails'}
              </button>
            </form>
          </div>

          {/* History Queue List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-pink-400" />
              Thumbnail Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading thumbnail indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active thumbnail jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-purple-950/60 text-purple-300 border border-purple-800/50";
                  if (job.status === "SUCCESS") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-purple-500/80 shadow-md shadow-purple-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.packages[0].variant_count} Variants)` : `Thumbnail job: ${job.provider}`}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {job.status}
                        </span>
                      </div>

                      {job.status === "PROCESSING" && (
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-[11px] font-medium text-purple-400">
                            <span>Stage: {job.stage}</span>
                            <span>{Math.round(job.progress * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div className="flex items-center gap-1.5">
                          <span>Provider: {job.provider}</span>
                          <span>•</span>
                          <span>Priority: {job.priority}</span>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(job.id); }}
                          className="text-rose-400 hover:text-rose-300 font-bold"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Candidate Variant Gallery Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-purple-400 uppercase tracking-widest">
                    AI Thumbnail Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `${activePkg.variant_count} Candidate Variants • Score: ${activePkg.quality_score}` : `Draft: ${activeJob.provider}`}
                  </h3>
                </div>

                {activePkg && (
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => handleRegenerate(activeJob.id)}
                      className="bg-purple-600 hover:bg-purple-700 text-white p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-purple-900/20"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Regenerate Layouts
                    </button>
                  </div>
                )}
              </div>

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">

                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "gallery", label: "Candidate Variant Gallery", icon: LayoutGrid },
                      { id: "analysis", label: "OCR & Visual Analysis", icon: Sliders },
                      { id: "experiment", label: "A/B Testing Experiments", icon: TrendingUp },
                      { id: "compare", label: "Version Lineage", icon: GitCompare }
                    ].map(t => (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTab(t.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${selectedTab === t.id ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/30' : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'}`}
                      >
                        <t.icon className="h-3.5 w-3.5" />
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab 1: Candidate Variant Gallery */}
                  {selectedTab === "gallery" && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {activePkg.variants?.map((varItem: any) => (
                        <div 
                          key={varItem.id} 
                          className={`bg-slate-950 border rounded-xl p-4 flex flex-col justify-between gap-3 relative transition-all ${varItem.is_selected ? 'border-amber-500/90 bg-amber-950/10 shadow-lg shadow-amber-950/20' : 'border-slate-800'}`}
                        >
                          {varItem.is_selected && (
                            <span className="absolute top-3 right-3 bg-amber-500 text-slate-950 font-black text-[10px] uppercase tracking-wider px-2 py-0.5 rounded flex items-center gap-1">
                              <Award className="h-3 w-3" />
                              Primary (Highest CTR)
                            </span>
                          )}

                          <div className="space-y-2">
                            {/* Simulated Thumbnail Mock Canvas */}
                            <div className="h-36 bg-gradient-to-tr from-slate-900 via-slate-950 to-purple-950 rounded-lg border border-slate-800 flex flex-col justify-between p-3 relative overflow-hidden">
                              <div className="text-[10px] font-black text-amber-400 uppercase tracking-widest bg-black/70 px-1.5 py-0.5 rounded w-fit border border-amber-900/40">
                                {varItem.badge_text || "NEW"}
                              </div>
                              <div>
                                <h4 className="text-white font-black text-sm uppercase tracking-wide drop-shadow-md line-clamp-2">
                                  {varItem.primary_hook}
                                </h4>
                                <p className="text-slate-300 font-bold text-[11px] line-clamp-1 drop-shadow">
                                  {varItem.secondary_hook}
                                </p>
                              </div>
                            </div>

                            <div>
                              <div className="font-bold text-sm text-slate-200">{varItem.variant_name}</div>
                              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                Layout: {varItem.layout_type}
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2 pt-2 border-t border-slate-900">
                            <div className="flex justify-between items-center text-xs font-semibold">
                              <span className="text-slate-400">CTR Prediction:</span>
                              <span className="text-purple-400 font-bold">{varItem.ctr_prediction_score}</span>
                            </div>
                            <div className="flex justify-between items-center text-xs font-semibold">
                              <span className="text-slate-400">Readability:</span>
                              <span className="text-emerald-400 font-bold">{varItem.readability_score}</span>
                            </div>
                            <div className="flex justify-between items-center text-xs font-semibold">
                              <span className="text-slate-400">Contrast:</span>
                              <span className="text-pink-400 font-bold">{varItem.contrast_score}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Visual & OCR Analysis */}
                  {selectedTab === "analysis" && activePkg.analysis && (
                    <div className="bg-slate-950/40 border border-slate-850 p-5 rounded-xl space-y-4">
                      <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">Visual Quality & OCR Inspection</h4>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">WCAG Contrast Ratio</div>
                          <div className="text-emerald-400 font-bold text-sm">{activePkg.analysis.contrast_ratio}:1 (Passes &gt;= 4.5:1)</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Blur Score</div>
                          <div className="text-slate-200 font-bold text-sm">{activePkg.analysis.blur_score} (Passes &lt; 0.25)</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Face Detection</div>
                          <div className="text-slate-200 font-bold text-sm">{activePkg.analysis.face_count} Face ({activePkg.analysis.face_confidence} confidence)</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">OCR Readability</div>
                          <div className="text-slate-200 font-bold text-sm">{activePkg.analysis.ocr_result?.confidence * 100}% Confidence</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: A/B Testing Experiments */}
                  {selectedTab === "experiment" && (
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">A/B Testing Experiments (Bridge for Analytics Agent)</h4>
                      
                      {activePkg.experiments && activePkg.experiments.length > 0 ? (
                        <div className="space-y-3">
                          {activePkg.experiments.map((exp: any) => (
                            <div key={exp.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2 text-xs">
                              <div className="flex justify-between items-center font-bold text-slate-200">
                                <span>Experiment on {exp.platform.toUpperCase()}</span>
                                <span className="bg-purple-950 text-purple-300 px-2 py-0.5 rounded border border-purple-800/60 uppercase text-[10px]">
                                  Status: {exp.status}
                                </span>
                              </div>
                              <div className="text-slate-400">
                                Window: {exp.evaluation_window_hours} hours | Significance: {exp.statistical_significance * 100}%
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                          No active A/B testing experiment scheduled yet.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tab 4: Version Lineages */}
                  {selectedTab === "compare" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">Thumbnail Package version lineage</h4>
                        <select
                          value={diffVersionId}
                          onChange={(e) => setDiffVersionId(e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded-lg p-1.5 text-xs text-slate-200"
                        >
                          <option value="">-- Select Revision Version --</option>
                          {activePkg.versions?.map((v: any) => (
                            <option key={v.id} value={v.id}>
                              Version {v.version} ({v.lineage_action} - {new Date(v.created_at).toLocaleTimeString()})
                            </option>
                          ))}
                        </select>
                      </div>

                      {diffVersion ? (
                        <div className="space-y-4">
                          <div className="text-[11px] font-bold text-purple-400 uppercase tracking-wider">
                            Snapshot Assets List (v{diffVersion.version} - Action: {diffVersion.lineage_action})
                          </div>
                          <div className="grid grid-cols-1 gap-3">
                            {diffVersion.assets_snapshot?.map((snap: any, idx: number) => (
                              <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
                                <div className="font-bold text-slate-200 mb-1">{snap.variant_name} ({snap.layout_type})</div>
                                <div className="text-slate-400 font-mono text-[10px]">Quality Score: {snap.quality_score} | Primary: {snap.is_selected ? 'Yes' : 'No'}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                          Select a historical Thumbnail package version from the dropdown to compare snapshots.
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <ImageIcon className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Thumbnail Workspace</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active thumbnail job from the left queue to view candidate variants, inspect OCR readability, and compare predicted CTR scores.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
