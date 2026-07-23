"use client";

import React, { useEffect, useState } from "react";
import { 
  Type, 
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
  FileText,
  Search,
  Plus,
  Zap,
  Edit3,
  AlignLeft
} from "lucide-react";

export default function SubtitlesPage() {
  const [voiceList, setVoiceList] = useState<any[]>([]);
  const [videoList, setVideoList] = useState<any[]>([]);

  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [language, setLanguage] = useState("en");
  const [provider, setProvider] = useState("alignment");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("timeline");
  const [diffVersionId, setDiffVersionId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const voiceRes = await fetch("/api/v1/voices");
      if (voiceRes.ok) {
        const data = await voiceRes.json();
        setVoiceList(data.filter((j: any) => j.status === "SUCCESS"));
      }
      
      const videoRes = await fetch("/api/v1/videos");
      if (videoRes.ok) {
        const data = await videoRes.json();
        setVideoList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const jobsRes = await fetch("/api/v1/subtitles");
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data);
      }

      const metricsRes = await fetch("/api/v1/subtitles/metrics");
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to load subtitle assets:", e);
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
    if (!selectedVoiceId || !selectedVideoId) return;
    setSubmitting(true);
    try {
      const voiceJob = voiceList.find(j => j.id === selectedVoiceId);
      const videoJob = videoList.find(j => j.id === selectedVideoId);

      const res = await fetch("/api/v1/subtitles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          voice_package_id: voiceJob.packages[0].id, 
          video_package_id: videoJob.packages[0].id,
          language,
          provider,
          priority 
        })
      });
      if (res.ok) {
        setSelectedVoiceId("");
        setSelectedVideoId("");
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
      const res = await fetch(`/api/v1/subtitles/${id}/regenerate?max_cpl=37`, {
        method: "POST"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Re-segmentation failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/subtitles/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const handleDownloadTrack = (jobId: string, format: string) => {
    window.open(`/api/v1/subtitles/${jobId}/export?format_type=${format}`, '_blank');
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;
  const diffVersion = activePkg?.versions?.find((v: any) => v.id === diffVersionId) || null;

  const filteredScenes = activePkg?.scene_subtitles?.filter((sc: any) => 
    !searchQuery || sc.caption_text.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
            AI Subtitle Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Converts VoicePackage alignments & VideoPackage timings into synchronized SubtitlePackages with SRT, WebVTT, ASS, and JSON timeline exports.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Subtitle Daemon</div>
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
              <Clock className="h-3.5 w-3.5 text-emerald-400" />
              Queued
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-teal-400 animate-pulse" />
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
              <RefreshCw className="h-3.5 w-3.5 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
              Avg Speed
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Enqueuer Form & History */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Submit Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-400" />
              Generate Subtitles
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Voice Package (Narration)</label>
                <select
                  value={selectedVoiceId}
                  onChange={(e) => setSelectedVoiceId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-emerald-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Voice Package --</option>
                  {voiceList.map((j) => (
                    <option key={j.id} value={j.id}>Voice ({j.language}) - {j.packages?.[0]?.speaking_style}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Video Package (Render Output)</label>
                <select
                  value={selectedVideoId}
                  onChange={(e) => setSelectedVideoId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-emerald-500 focus:outline-none text-slate-200"
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
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-emerald-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="en">English (en)</option>
                    <option value="es">Spanish (es)</option>
                    <option value="fr">French (fr)</option>
                    <option value="de">German (de)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-emerald-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="alignment">Alignment Direct</option>
                    <option value="mock">Mock Engine</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedVoiceId || !selectedVideoId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing...' : 'Generate Subtitle Package'}
              </button>
            </form>
          </div>

          {/* History Queue List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-teal-400" />
              Subtitle Jobs Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading subtitle indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active subtitle jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-teal-950/60 text-teal-300 border border-teal-800/50";
                  if (job.status === "SUCCESS") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-emerald-500/80 shadow-md shadow-emerald-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.language.toUpperCase()})` : `Subtitle job: ${job.provider}`}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {job.status}
                        </span>
                      </div>

                      {job.status === "PROCESSING" && (
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-[11px] font-medium text-emerald-400">
                            <span>Stage: {job.stage}</span>
                            <span>{Math.round(job.progress * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-emerald-500 to-teal-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div className="flex items-center gap-1.5">
                          <span>Provider: {job.provider}</span>
                          <span>•</span>
                          <span>Lang: {job.language}</span>
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

        {/* Right Column: Detailed Workspace & Downloads Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Details & Export Downloads */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-widest">
                    AI Subtitle Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `${activePkg.total_captions} Captions • ${activePkg.total_words} Words (${activePkg.language.toUpperCase()})` : `Draft: ${activeJob.provider}`}
                  </h3>
                </div>

                {activePkg && (
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => handleDownloadTrack(activeJob.id, 'srt')}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-300"
                    >
                      <Download className="h-3.5 w-3.5 text-emerald-400" />
                      .SRT
                    </button>
                    <button
                      onClick={() => handleDownloadTrack(activeJob.id, 'vtt')}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-300"
                    >
                      <Download className="h-3.5 w-3.5 text-teal-400" />
                      .VTT
                    </button>
                    <button
                      onClick={() => handleDownloadTrack(activeJob.id, 'ass')}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-300"
                    >
                      <Download className="h-3.5 w-3.5 text-cyan-400" />
                      .ASS
                    </button>
                    <button
                      onClick={() => handleRegenerate(activeJob.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Re-segment
                    </button>
                  </div>
                )}
              </div>

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">

                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "timeline", label: "Caption Editor & Speed", icon: Type },
                      { id: "style", label: "Caption Style Profile", icon: SlidersHorizontal },
                      { id: "thumbnail", label: "Thumbnail Key Phrases", icon: Sparkles },
                      { id: "compare", label: "Version Lineage", icon: GitCompare }
                    ].map(t => (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTab(t.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${selectedTab === t.id ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/30' : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'}`}
                      >
                        <t.icon className="h-3.5 w-3.5" />
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab 1: Timeline & Caption Editor */}
                  {selectedTab === "timeline" && (
                    <div className="space-y-4">
                      {/* Search bar */}
                      <div className="relative">
                        <Search className="h-4 w-4 absolute left-3 top-3 text-slate-500" />
                        <input
                          type="text"
                          placeholder="Search captions..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 pl-9 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                        />
                      </div>

                      <div className="space-y-4 max-h-[420px] overflow-y-auto pr-1">
                        {filteredScenes.map((sc: any) => (
                          <div key={sc.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-3">
                            <div className="flex items-center justify-between">
                              <div className="font-bold text-sm text-slate-200">
                                Scene {sc.scene_number}
                              </div>
                              <div className="flex items-center gap-3 text-xs font-semibold">
                                <span className="text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/40">
                                  {sc.reading_speed_cps} CPS
                                </span>
                                <span className="text-teal-400 bg-teal-950/40 px-2 py-0.5 rounded border border-teal-900/40">
                                  {sc.reading_speed_wpm} WPM
                                </span>
                                <span className="text-slate-400">
                                  Score: {sc.quality_score}
                                </span>
                              </div>
                            </div>

                            <p className="text-slate-200 text-sm font-medium bg-slate-900/40 p-3 rounded-lg border border-slate-850">
                              "{sc.caption_text}"
                            </p>

                            {/* Finer-grained CaptionSegments */}
                            {sc.segments && sc.segments.length > 0 && (
                              <div className="space-y-2 pt-1">
                                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                                  Segment Line Blocks ({sc.segments.length})
                                </div>
                                <div className="grid grid-cols-1 gap-2">
                                  {sc.segments.map((seg: any) => (
                                    <div key={seg.id} className="bg-slate-900/80 border border-slate-800 p-2.5 rounded-lg flex items-center justify-between text-xs">
                                      <div className="space-x-2">
                                        <span className="font-mono text-emerald-400">[{seg.start_ms}ms - {seg.end_ms}ms]</span>
                                        <span className="text-slate-200 font-semibold">{seg.text}</span>
                                      </div>
                                      <div className="text-[10px] text-slate-400 font-mono">
                                        {seg.reading_speed_cpl} CPL
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Caption Style Profile */}
                  {selectedTab === "style" && (
                    <div className="bg-slate-950/40 border border-slate-850 p-5 rounded-xl space-y-4">
                      <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Active Style Profile: {activePkg.caption_style}</h4>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Font Family</div>
                          <div className="text-slate-200 font-bold">Inter / Roboto</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Font Size</div>
                          <div className="text-slate-200 font-bold">24 px (Bold)</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Text Color</div>
                          <div className="text-slate-200 font-bold flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-white border border-slate-700" />
                            #FFFFFF
                          </div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Outline Color</div>
                          <div className="text-slate-200 font-bold flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-black border border-slate-700" />
                            #000000 (2px)
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[100px]">
                        <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">Live Burned Caption Style Render</div>
                        <span className="text-2xl font-black text-white px-4 py-1.5 rounded bg-black/60 shadow-lg tracking-wide border border-black">
                          AATES AUTOMATED CAPTIONS
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Thumbnail Agent Integration */}
                  {selectedTab === "thumbnail" && (
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Thumbnail Agent Metadata Extraction</h4>
                      
                      <div className="space-y-3">
                        {activePkg.scene_subtitles?.map((sc: any) => (
                          <div key={sc.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                            <div className="flex justify-between items-center text-xs">
                              <span className="font-bold text-slate-300">Scene {sc.scene_number} Key Phrases</span>
                              <span className="text-emerald-400 font-bold">Importance: {sc.importance_score}</span>
                            </div>
                            <div className="flex flex-wrap gap-2 pt-1">
                              {sc.key_phrases?.map((kp: string, idx: number) => (
                                <span key={idx} className="bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 font-bold text-xs px-2.5 py-1 rounded-lg">
                                  {kp}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 4: Version Lineages */}
                  {selectedTab === "compare" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Subtitle Package version lineage</h4>
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
                          <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                            Snapshot Assets List (v{diffVersion.version} - Action: {diffVersion.lineage_action})
                          </div>
                          <div className="grid grid-cols-1 gap-3">
                            {diffVersion.assets_snapshot?.map((snap: any, idx: number) => (
                              <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
                                <div className="font-bold text-slate-200 mb-1">Scene {snap.scene_number} ({snap.total_segments} Segments)</div>
                                <div className="text-slate-400">"{snap.text}"</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                          Select a historical Subtitle package version from the dropdown to compare snapshots.
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Type className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Subtitle Workspace</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active subtitle job from the left queue to edit line breaks, inspect reading speed (CPS/CPL), and download SRT/VTT/ASS tracks.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
