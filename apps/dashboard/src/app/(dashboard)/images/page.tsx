"use client";

import React, { useEffect, useState } from "react";
import { 
  Camera, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Image as ImageIcon,
  Download,
  Award,
  Sparkles,
  Maximize2,
  Play,
  Trash2,
  ExternalLink,
  Layers,
  ChevronRight,
  GitCompare,
  Users
} from "lucide-react";

export default function ImagesPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [selectedScriptId, setSelectedScriptId] = useState("");
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
        const scriptData = await scriptRes.json();
        // Filter scripts that succeeded and have package contents
        const succScripts = scriptData.filter((j: any) => j.status === "SUCCESS" && j.packages?.length > 0);
        setScriptList(succScripts);
      }
      const jobsRes = await fetch("/api/v1/images");
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData);
      }
      const metricsRes = await fetch("/api/v1/images/metrics");
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }
    } catch (e) {
      console.error("Failed to load image data:", e);
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
    if (!selectedScriptId) return;
    setSubmitting(true);
    try {
      // Find package ID corresponding to selected script job
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const scriptPackageId = scriptJob?.packages?.[0]?.id;
      
      const res = await fetch("/api/v1/images", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptPackageId, 
          priority 
        })
      });
      if (res.ok) {
        setSelectedScriptId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegenerateScene = async (id: string, sceneNumber: number) => {
    try {
      const res = await fetch(`/api/v1/images/${id}/regenerate?scene_number=${sceneNumber}`, {
        method: "POST"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Regeneration failed:", e);
    }
  };

  const handleUpscaleScene = async (id: string, sceneNumber: number) => {
    try {
      const res = await fetch(`/api/v1/images/${id}/upscale?scene_number=${sceneNumber}`, {
        method: "POST"
      });
      if (res.ok) {
        alert(`Scene ${sceneNumber} upscaled successfully!`);
        fetchData();
      }
    } catch (e) {
      console.error("Upscale failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/images/${id}`, { method: "DELETE" });
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
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-violet-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
            AI Image Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Converts script scenes into a unified contract of Scene Assets (`ImagePackage`). Manages character profiles, upscales, and style presets.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Image Workers Status</div>
              <div className="text-sm font-bold text-slate-200">
                {metrics.worker_is_running ? `Online (${metrics.current_worker_count} Workers active)` : 'Offline'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Cards */}
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
              Avg Image Build Time
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
          </div>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & History Queue */}
        <div className="lg:col-span-4 space-y-6">
          {/* Submit Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-violet-400" />
              Generate Image Assets
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Active Creative Script</label>
                <select
                  value={selectedScriptId}
                  onChange={(e) => setSelectedScriptId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Script --</option>
                  {scriptList.map((j) => (
                    <option key={j.id} value={j.id}>{j.packages?.[0]?.title || `Script ${j.id.slice(0,6)}`} (v{j.packages?.[0]?.version})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Job Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value={0}>Low (0)</option>
                    <option value={1}>Medium (1)</option>
                    <option value={2}>High (2)</option>
                    <option value={5}>Critical (5)</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-violet-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                    disabled={submitting || !selectedScriptId}
                  >
                    <Play className="h-4 w-4" />
                    {submitting ? 'Enqueuing...' : 'Run Image Agent'}
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Image Jobs List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Image Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading campaign indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active image jobs found. Run the image agent above!
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
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.packages[0].style_preset})` : `Job: ${job.provider}`}
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
                          <span>Model: {job.provider}</span>
                          <span>•</span>
                          <span>Priority: {job.priority}</span>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(job.id); }}
                          className="text-rose-400 hover:text-rose-300 font-bold"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Detailed Image Package Gallery Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-violet-400 uppercase tracking-widest">
                    AI Image Package contract (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `Preset: ${activePkg.style_preset} (${activePkg.resolution})` : `Draft: ${activeJob.provider}`}
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {activePkg && (
                    <button
                      onClick={() => alert("Asset package ZIP compilation complete! Downloading images...")}
                      className="bg-slate-900 hover:bg-slate-850 border border-slate-800 font-semibold rounded-lg p-2 px-3 text-xs flex items-center gap-1.5 text-slate-300 shadow-md transition-all"
                    >
                      <Download className="h-3.5 w-3.5 text-violet-400" />
                      Download ZIP
                    </button>
                  )}
                </div>
              </div>

              {activeJob.status === "QUEUED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Clock className="h-12 w-12 text-slate-600 animate-pulse" />
                  <div>
                    <h4 className="font-bold text-slate-300">Image Generation Enqueued</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Waiting for the background Image Agent to start compiling prompt templates and scene reference configurations.
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "PROCESSING" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Activity className="h-12 w-12 text-violet-500 animate-spin" style={{ animationDuration: '4s' }} />
                  <div>
                    <h4 className="font-bold text-slate-300">Generating Images: {activeJob.stage}</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Building scene prompt scripts, rendering camera views, scoring quality gates, and optimizing.
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
                    <h4 className="font-bold text-rose-400">Image Generation Failed</h4>
                    <p className="text-slate-400 text-xs max-w-md mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-left font-mono break-all">
                      {activeJob.error_message || 'Internal processing error occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "SUCCESS" && !activePkg && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <RefreshCw className="h-12 w-12 text-slate-600 animate-spin" />
                  <p className="text-slate-500 text-sm font-semibold">Ingesting Image Assets...</p>
                </div>
              )}

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">
                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "gallery", label: "Scene Gallery", icon: ImageIcon },
                      { id: "char", label: "Character Profile", icon: Users },
                      { id: "compare", label: "Lineage Diff", icon: GitCompare }
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
                  <div className="min-h-[380px] text-sm text-slate-300 leading-relaxed space-y-4">
                    
                    {/* Scene Gallery Tab */}
                    {selectedTab === "gallery" && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {activePkg.assets?.map((asset: any) => (
                          <div key={asset.id} className="bg-slate-950/60 border border-slate-800/60 rounded-2xl overflow-hidden flex flex-col gap-3 group hover:border-violet-500/40 transition-all p-4">
                            {/* Dummy visual image block simulating the scene visual rendering */}
                            <div className="w-full aspect-[16/9] bg-gradient-to-tr from-slate-950 via-slate-900 to-indigo-950/60 border border-slate-800 rounded-xl relative flex items-center justify-center overflow-hidden">
                              <div className="flex flex-col items-center gap-2 text-slate-500 font-semibold text-xs group-hover:text-slate-300 transition-all text-center p-4">
                                <ImageIcon className="h-8 w-8 text-slate-600 animate-pulse mb-1" />
                                <div>Scene {asset.scene_number} ({asset.duration}s)</div>
                                <div className="text-[10px] text-slate-600 font-medium font-mono line-clamp-1 max-w-[200px]">{asset.storage_key}</div>
                              </div>
                              <span className="absolute top-2 right-2 bg-slate-950/90 text-emerald-400 text-[10px] font-extrabold px-2 py-0.5 rounded-full border border-slate-800">
                                Quality: {Math.round(asset.quality_score * 100)}%
                              </span>
                            </div>

                            <div className="space-y-2">
                              <div className="flex justify-between items-center text-xs font-bold text-slate-200">
                                <span>Scene Details</span>
                                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest">{asset.camera_angle}</span>
                              </div>
                              
                              <div className="bg-slate-900/60 border border-slate-800/50 p-3 rounded-lg text-xs leading-relaxed font-semibold italic text-slate-400">
                                "{asset.prompt}"
                              </div>

                              <div className="grid grid-cols-2 gap-2 text-[10px] font-bold text-slate-500">
                                <div>Seed: <span className="text-slate-400 font-mono">{asset.seed}</span></div>
                                <div>Lighting: <span className="text-slate-400">{asset.lighting}</span></div>
                                <div>Background: <span className="text-slate-400">{asset.background}</span></div>
                                <div>Engine: <span className="text-slate-400">{asset.model}</span></div>
                              </div>

                              <div className="flex gap-2 pt-2 border-t border-slate-900">
                                <button
                                  onClick={() => handleRegenerateScene(activeJob.id, asset.scene_number)}
                                  className="flex-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg p-1.5 text-[11px] font-bold flex items-center justify-center gap-1.5 text-slate-300"
                                >
                                  <RefreshCw className="h-3 w-3" />
                                  Regenerate
                                </button>
                                <button
                                  onClick={() => handleUpscaleScene(activeJob.id, asset.scene_number)}
                                  className="flex-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg p-1.5 text-[11px] font-bold flex items-center justify-center gap-1.5 text-slate-300"
                                >
                                  <Maximize2 className="h-3 w-3" />
                                  Upscale Image
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Character Tab */}
                    {selectedTab === "char" && (
                      <div className="space-y-6">
                        <div className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-4">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Character profile consistency lock</h4>
                          <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-slate-300">
                            <div className="space-y-1.5">
                              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Character ID</div>
                              <p className="text-slate-200 font-mono">{activePkg.character_id}</p>
                            </div>
                            <div className="space-y-1.5">
                              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Visual Consistency Presets</div>
                              <p className="text-slate-200">{activePkg.style_preset}</p>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Style preset profiles description</h4>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            Style profile settings applied across all scenes to ensure character proportions, background illumination, and facial vectors match the canonical reference contract.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Lineage Diff Tab */}
                    {selectedTab === "compare" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Image Version Lineage list</h4>
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
                            <div className="grid grid-cols-2 gap-4">
                              {diffVersion.assets_snapshot?.map((snap: any, idx: number) => (
                                <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
                                  <div className="font-bold text-slate-200 mb-1">Scene {snap.scene_number}</div>
                                  <p className="text-slate-400 italic mb-2">"{snap.prompt}"</p>
                                  <div className="text-[10px] text-slate-500 font-bold">Seed: {snap.seed} | Quality: {snap.quality_score}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                            Select a historical Image package version from the dropdown to run lineage comparison.
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
              <Camera className="h-12 w-12 text-slate-700 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Image Output Gallery</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active image job from the history sidebar list to view generated scene galleries, prompts, Seeds, upscales, and version lineages.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
