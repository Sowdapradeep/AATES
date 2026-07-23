"use client";

import React, { useEffect, useState } from "react";
import { 
  Film, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Play, 
  Pause,
  Download,
  Sparkles,
  Volume2,
  Trash2,
  Layers,
  GitCompare,
  Sliders,
  Maximize2,
  Monitor,
  Eye,
  Plus
} from "lucide-react";

export default function VideosPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [imageList, setImageList] = useState<any[]>([]);
  const [voiceList, setVoiceList] = useState<any[]>([]);

  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedImageId, setSelectedImageId] = useState("");
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  
  const [renderer, setRenderer] = useState("ffmpeg");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("timeline");
  const [diffVersionId, setDiffVersionId] = useState("");
  
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [playingVideoId, setPlayingVideoId] = useState<string | null>(null);

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

      const voiceRes = await fetch("/api/v1/voices");
      if (voiceRes.ok) {
        const data = await voiceRes.json();
        setVoiceList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const jobsRes = await fetch("/api/v1/videos");
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data);
      }

      const metricsRes = await fetch("/api/v1/videos/metrics");
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to load video assets:", e);
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
    if (!selectedScriptId || !selectedImageId || !selectedVoiceId) return;
    setSubmitting(true);
    try {
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const imageJob = imageList.find(j => j.id === selectedImageId);
      const voiceJob = voiceList.find(j => j.id === selectedVoiceId);

      const res = await fetch("/api/v1/videos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptJob.packages[0].id, 
          image_package_id: imageJob.packages[0].id,
          voice_package_id: voiceJob.packages[0].id,
          renderer,
          priority 
        })
      });
      if (res.ok) {
        setSelectedScriptId("");
        setSelectedImageId("");
        setSelectedVoiceId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleForceRender = async (id: string) => {
    try {
      await fetch(`/api/v1/videos/${id}/render`, { method: "POST" });
      fetchData();
    } catch (e) {
      console.error("Force render failed:", e);
    }
  };

  const handleRegenerateScene = async (id: string, sceneNumber: number) => {
    try {
      const res = await fetch(`/api/v1/videos/${id}/regenerate?scene_number=${sceneNumber}`, {
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
      await fetch(`/api/v1/videos/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const handleDownloadTimeline = (pkg: any) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(pkg.metadata_artifacts, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `timeline_v${pkg.version}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;
  const diffVersion = activePkg?.versions?.find((v: any) => v.id === diffVersionId) || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-violet-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
            AI Video Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Orchestrates media assets merging image sequences, voice tracks, panning motions, and slide transition curves into a composite VideoPackage.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Video Worker daemon</div>
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
              <Clock className="h-3.5 w-3.5 text-violet-400" />
              Queued
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
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
              <RefreshCw className="h-3.5 w-3.5 text-pink-400 animate-spin" style={{ animationDuration: '6s' }} />
              Avg Composition Time
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & History Sidebar */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Submit Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-violet-400" />
              Assemble Video
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Script Package</label>
                <select
                  value={selectedScriptId}
                  onChange={(e) => setSelectedScriptId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Script --</option>
                  {scriptList.map((j) => (
                    <option key={j.id} value={j.id}>{j.packages?.[0]?.title || `Script ${j.id.slice(0,6)}`}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Image Package (Visual Assets)</label>
                <select
                  value={selectedImageId}
                  onChange={(e) => setSelectedImageId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Succeeded Visuals --</option>
                  {imageList.map((j) => (
                    <option key={j.id} value={j.id}>Images for {j.packages?.[0]?.platform} (v{j.packages?.[0]?.version})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">3. Voice Package (Narration Audios)</label>
                <select
                  value={selectedVoiceId}
                  onChange={(e) => setSelectedVoiceId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Narrator Audio --</option>
                  {voiceList.map((j) => (
                    <option key={j.id} value={j.id}>Voices ({j.language}) - {j.packages?.[0]?.speaking_style}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Composition Renderer</label>
                  <select
                    value={renderer}
                    onChange={(e) => setRenderer(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="ffmpeg">FFmpeg Engine</option>
                    <option value="mock">Mock Renderer</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value={0}>Low (0)</option>
                    <option value={1}>Medium (1)</option>
                    <option value={2}>High (2)</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-violet-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedScriptId || !selectedImageId || !selectedVoiceId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing...' : 'Compile Video'}
              </button>
            </form>
          </div>

          {/* Video Jobs List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Composition History
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading campaign indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active video render jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-violet-950/60 text-violet-300 border border-violet-800/50";
                  if (job.status === "SUCCESS") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-violet-500/80 shadow-md shadow-violet-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.renderer})` : `Render job: ${job.renderer}`}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {job.status}
                        </span>
                      </div>
                      
                      {job.status === "PROCESSING" && (
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-[11px] font-medium text-violet-400">
                            <span>Stage: {job.stage}</span>
                            <span>{Math.round(job.progress * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div className="flex items-center gap-1.5">
                          <span>Renderer: {job.renderer}</span>
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

        {/* Right Column: Detailed Video Package Render Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-violet-400 uppercase tracking-widest">
                    AI Video Package contract (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `Render Output: ${activePkg.resolution} (${(activePkg.duration_ms / 1000).toFixed(1)}s)` : `Draft: ${activeJob.renderer}`}
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {activeJob.status === "FAILED" && (
                    <button
                      onClick={() => handleForceRender(activeJob.id)}
                      className="bg-violet-600 hover:bg-violet-700 text-white font-bold rounded-lg p-2 px-3 text-xs"
                    >
                      Retry Render
                    </button>
                  )}
                  {activePkg && (
                    <button
                      onClick={() => handleDownloadTimeline(activePkg)}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 text-slate-300"
                    >
                      <Download className="h-4 w-4" />
                      Download Timeline JSON
                    </button>
                  )}
                </div>
              </div>

              {activeJob.status === "QUEUED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Clock className="h-12 w-12 text-slate-600 animate-pulse" />
                  <div>
                    <h4 className="font-bold text-slate-300">Composition Queue Enqueued</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Waiting for the background Video Agent to lock files, verify RenderProfile options, and compile the scene graph.
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "PROCESSING" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Activity className="h-12 w-12 text-violet-500 animate-spin" style={{ animationDuration: '4s' }} />
                  <div>
                    <h4 className="font-bold text-slate-300">Rendering Video: {activeJob.stage}</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Stitching image layers, overlaying audios, applying motion presets, and compiling container tags.
                    </p>
                  </div>
                  <div className="w-64 bg-slate-950 h-2 rounded-full overflow-hidden mt-2">
                    <div 
                      className="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-500" 
                      style={{ width: `${activeJob.progress * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {activeJob.status === "FAILED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center border border-dashed border-rose-950/60 rounded-xl bg-rose-950/10">
                  <AlertTriangle className="h-12 w-12 text-rose-500" />
                  <div>
                    <h4 className="font-bold text-rose-400">Rendering Failed</h4>
                    <p className="text-slate-400 text-xs max-w-md mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-left font-mono break-all">
                      {activeJob.error_message || 'Internal render error occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "SUCCESS" && !activePkg && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <RefreshCw className="h-12 w-12 text-slate-600 animate-spin" />
                  <p className="text-slate-500 text-sm font-semibold">Ingesting Video Assets...</p>
                </div>
              )}

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">
                  
                  {/* Preview Player / Output */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-2xl overflow-hidden aspect-video flex flex-col items-center justify-center relative group">
                    <Monitor className="h-16 w-16 text-slate-700 group-hover:scale-[1.05] transition-all" />
                    <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-xs font-semibold bg-slate-900/90 p-3 rounded-xl border border-slate-800 backdrop-blur-md">
                      <span className="font-mono text-slate-300 truncate">{activePkg.storage_key}</span>
                      <a 
                        href={`/api/v1/videos/${activeJob.id}/preview`} 
                        target="_blank"
                        className="bg-violet-600 hover:bg-violet-700 text-white p-1 px-2.5 rounded-lg flex items-center gap-1 text-[11px]"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Preview Player
                      </a>
                    </div>
                  </div>

                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "timeline", label: "Scene Graph Timeline", icon: Film },
                      { id: "telemetry", label: "Render Telemetry", icon: Sliders },
                      { id: "compare", label: "Lineage Snapshot", icon: GitCompare }
                    ].map(t => (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTab(t.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${selectedTab === t.id ? 'bg-violet-600 text-white shadow-lg shadow-violet-900/30' : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'}`}
                      >
                        <t.icon className="h-3.5 w-3.5" />
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab Contents */}
                  <div className="min-h-[280px] text-sm text-slate-300 leading-relaxed space-y-4">
                    
                    {/* Scene Graph Timeline Tab */}
                    {selectedTab === "timeline" && (
                      <div className="space-y-4">
                        {activePkg.assets?.map((asset: any) => (
                          <div key={asset.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl flex flex-col gap-3 group hover:border-violet-500/40 transition-all">
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <div className="font-bold text-sm text-slate-200">
                                  Scene {asset.scene_number}
                                </div>
                                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mt-0.5">
                                  <span>Time: {asset.timeline_start_ms}ms - {asset.timeline_end_ms}ms</span>
                                  <span>•</span>
                                  <span>Duration: {asset.duration_ms} ms</span>
                                </div>
                              </div>
                              <button
                                onClick={() => handleRegenerateScene(activeJob.id, asset.scene_number)}
                                className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-1.5 px-2 rounded-lg text-[10px] font-bold flex items-center gap-1 text-slate-300"
                              >
                                <RefreshCw className="h-3 w-3" />
                                Re-render Clip
                              </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-xs font-medium">
                              <div className="bg-slate-900/30 border border-slate-850 p-2.5 rounded-lg">
                                <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider mb-1">Motion preset</div>
                                <p className="text-slate-300 font-semibold">{asset.motion_preset || 'None'}</p>
                              </div>
                              <div className="bg-slate-900/30 border border-slate-850 p-2.5 rounded-lg">
                                <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider mb-1">Transition preset</div>
                                <p className="text-slate-300 font-semibold">{asset.transition_preset || 'Cut'}</p>
                              </div>
                            </div>

                            <div className="text-[10px] text-slate-500 font-mono truncate">
                              Path: {asset.rendered_clip}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Telemetry Tab */}
                    {selectedTab === "telemetry" && activePkg.metadata_artifacts?.render_telemetry && (
                      <div className="bg-slate-950/40 border border-slate-850 p-5 rounded-xl space-y-4">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Encoding Telemetry Stats</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Timeline compile</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.timeline_build_time_ms} ms</p>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Scene composite</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.scene_render_time_ms} ms</p>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Final render</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.final_render_time_ms} ms</p>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Output file size</div>
                            <p className="text-slate-200 font-bold">{(activePkg.metadata_artifacts.render_telemetry.output_file_size_bytes / 1024).toFixed(1)} KB</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 border-t border-slate-900 pt-4 text-xs">
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Peak Memory</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.peak_memory_mb} MB</p>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">CPU Load</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.cpu_usage_pct}%</p>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">GPU Load</div>
                            <p className="text-slate-200 font-bold">{activePkg.metadata_artifacts.render_telemetry.gpu_usage_pct}%</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Lineage Snapshot Tab */}
                    {selectedTab === "compare" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Video Package version lineages</h4>
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
                            <div className="text-[11px] font-bold text-violet-400 uppercase tracking-wider">
                              Snapshot Assets List (v{diffVersion.version} - Action: {diffVersion.lineage_action})
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                              {diffVersion.assets_snapshot?.map((snap: any, idx: number) => (
                                <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
                                  <div className="font-bold text-slate-200 mb-1">Scene {snap.scene_number} (Duration: {snap.duration_ms} ms)</div>
                                  <div className="text-[10px] text-slate-500 font-mono truncate">File: {snap.rendered_clip} | Quality: {snap.quality_score}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                            Select a historical Video package version from the dropdown to run lineage comparison.
                          </div>
                        )}
                      </div>
                    )}

                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Film className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Video Composition Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active video render job from the history sidebar list to view generated clips timeline boundaries, encoding stats, and Safe Regions.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
