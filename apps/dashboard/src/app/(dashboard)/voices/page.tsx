"use client";

import React, { useEffect, useState } from "react";
import { 
  Mic, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Play, 
  Pause,
  Download,
  Award,
  Sparkles,
  Volume2,
  Trash2,
  ExternalLink,
  Layers,
  ChevronRight,
  GitCompare,
  Sliders,
  Music,
  Plus
} from "lucide-react";

export default function VoicesPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [language, setLanguage] = useState("en");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("scenes");
  const [diffVersionId, setDiffVersionId] = useState("");
  
  const [cloneName, setCloneName] = useState("");
  const [cloning, setCloning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  const fetchData = async () => {
    try {
      const scriptRes = await fetch("/api/v1/scripts");
      if (scriptRes.ok) {
        const scriptData = await scriptRes.json();
        const succScripts = scriptData.filter((j: any) => j.status === "SUCCESS" && j.packages?.length > 0);
        setScriptList(succScripts);
      }
      const jobsRes = await fetch("/api/v1/voices");
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData);
      }
      const metricsRes = await fetch("/api/v1/voices/metrics");
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }
    } catch (e) {
      console.error("Failed to load voice data:", e);
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
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const scriptPackageId = scriptJob?.packages?.[0]?.id;
      
      const res = await fetch("/api/v1/voices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptPackageId, 
          language,
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
      const res = await fetch(`/api/v1/voices/${id}/regenerate?scene_number=${sceneNumber}`, {
        method: "POST"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Regeneration failed:", e);
    }
  };

  const handleCloneVoice = async (id: string) => {
    if (!cloneName) return;
    setCloning(true);
    try {
      const res = await fetch(`/api/v1/voices/${id}/clone?name=${encodeURIComponent(cloneName)}`, {
        method: "POST"
      });
      if (res.ok) {
        alert(`Cloned voice "${cloneName}" successfully! Added to Speaker profile overrides.`);
        setCloneName("");
        fetchData();
      }
    } catch (e) {
      console.error("Voice cloning failed:", e);
    } finally {
      setCloning(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/voices/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const togglePlayback = (assetId: string) => {
    if (playingAudioId === assetId) {
      setPlayingAudioId(null);
    } else {
      setPlayingAudioId(assetId);
    }
  };

  const handleDownloadAlignment = (asset: any) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(asset.word_alignment, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `scene_${asset.scene_number}_alignment.json`);
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
            AI Voice Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Converts script narration into a standardized `VoicePackage` contract with millisecond alignment, custom pronunciation guides, and SSML builder presets.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Voice Workers Status</div>
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
              Avg Voice Build Time
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
              Synthesize Speech
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
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">TTS Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="en">English (en)</option>
                    <option value="ta">Tamil (ta)</option>
                    <option value="hi">Hindi (hi)</option>
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
                disabled={submitting || !selectedScriptId}
              >
                <Play className="h-4 w-4" />
                {submitting ? 'Enqueuing...' : 'Run Voice Agent'}
              </button>
            </form>
          </div>

          {/* Voice Jobs List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Voice Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading campaign indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active voice jobs found. Enqueue a job above!
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
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.language})` : `Speech job: ${job.provider}`}
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

        {/* Right Column: Detailed Voice Package Playlist Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-violet-400 uppercase tracking-widest">
                    AI Voice Package contract (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `Narration: ${activePkg.language} (${(activePkg.overall_duration_ms / 1000).toFixed(1)}s)` : `Draft: ${activeJob.provider}`}
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {activePkg && (
                    <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg p-1 px-2.5 text-xs text-slate-400 font-semibold">
                      <span>Rate:</span>
                      <select 
                        value={playbackRate} 
                        onChange={(e) => setPlaybackRate(Number(e.target.value))}
                        className="bg-transparent text-slate-200 outline-none font-bold"
                      >
                        <option value={0.75}>0.75x</option>
                        <option value={1.0}>1.0x</option>
                        <option value={1.25}>1.25x</option>
                        <option value={1.5}>1.5x</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>

              {activeJob.status === "QUEUED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Clock className="h-12 w-12 text-slate-600 animate-pulse" />
                  <div>
                    <h4 className="font-bold text-slate-300">Speech Synthesis Enqueued</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Waiting for the background Voice Agent to verify custom speech markers, pronunciation dictionaries, and SSML tags.
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "PROCESSING" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Activity className="h-12 w-12 text-violet-500 animate-spin" style={{ animationDuration: '4s' }} />
                  <div>
                    <h4 className="font-bold text-slate-300">Synthesizing Voice: {activeJob.stage}</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Generating prosody attributes, compiling word timestamp boundaries in milliseconds, and validating.
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
                    <h4 className="font-bold text-rose-400">Speech Synthesis Failed</h4>
                    <p className="text-slate-400 text-xs max-w-md mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-left font-mono break-all">
                      {activeJob.error_message || 'Internal processing error occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "SUCCESS" && !activePkg && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <RefreshCw className="h-12 w-12 text-slate-600 animate-spin" />
                  <p className="text-slate-500 text-sm font-semibold">Ingesting Voice Audio Assets...</p>
                </div>
              )}

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">
                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "scenes", label: "Scene Playlist", icon: Music },
                      { id: "clone", label: "Voice Cloning", icon: Sliders },
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
                    
                    {/* Scene Playlist Tab */}
                    {selectedTab === "scenes" && (
                      <div className="space-y-4">
                        {activePkg.assets?.map((asset: any) => {
                          const isPlaying = playingAudioId === asset.id;
                          return (
                            <div key={asset.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl flex flex-col gap-3 group hover:border-violet-500/40 transition-all">
                              <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                  <button
                                    onClick={() => togglePlayback(asset.id)}
                                    className={`p-2.5 rounded-full flex items-center justify-center transition-all ${isPlaying ? 'bg-rose-600 text-white animate-pulse' : 'bg-violet-600 text-white hover:scale-[1.05]'}`}
                                  >
                                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                                  </button>
                                  <div>
                                    <div className="font-bold text-sm text-slate-200">
                                      Scene {asset.scene_number} ({asset.language})
                                    </div>
                                    <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mt-0.5">
                                      <span>Duration: {asset.duration_ms} ms</span>
                                      <span>•</span>
                                      <span className="text-violet-400 font-semibold">{asset.voice_id}</span>
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => handleDownloadAlignment(asset)}
                                    className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-1.5 px-2 rounded-lg text-[10px] font-bold flex items-center gap-1 text-slate-300"
                                  >
                                    <Download className="h-3 w-3" />
                                    Download Alignment JSON
                                  </button>
                                  <button
                                    onClick={() => handleRegenerateScene(activeJob.id, asset.scene_number)}
                                    className="bg-slate-900 hover:bg-slate-800 border border-slate-800 p-1.5 px-2 rounded-lg text-[10px] font-bold flex items-center gap-1 text-slate-300"
                                  >
                                    <RefreshCw className="h-3 w-3" />
                                    Regenerate
                                  </button>
                                </div>
                              </div>

                              <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-lg text-xs leading-relaxed font-semibold italic text-slate-300">
                                "{asset.narration}"
                              </div>

                              {/* Timestamps Map */}
                              {asset.word_alignment && (
                                <div className="space-y-1.5">
                                  <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Subtitle-Ready Timestamp Offsets (ms)</div>
                                  <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto bg-slate-950 p-2.5 rounded-lg border border-slate-900">
                                    {asset.word_alignment.map((w: any, idx: number) => (
                                      <div key={idx} className="bg-slate-900 border border-slate-800 rounded-md p-1 px-1.5 text-[10px] font-mono font-semibold flex items-center gap-1">
                                        <span className="text-slate-200 font-sans">{w.word}</span>
                                        <span className="text-slate-500">[{w.start_time_ms}-{w.end_time_ms}ms]</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* SSML Prosody tag block */}
                              {asset.ssml && (
                                <div className="space-y-1">
                                  <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">SSML Prosody tag</div>
                                  <code className="block bg-slate-950 p-2.5 rounded-lg border border-slate-900 text-[10px] text-emerald-400 font-mono select-all truncate">
                                    {asset.ssml}
                                  </code>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Cloned Voices Tab */}
                    {selectedTab === "clone" && (
                      <div className="space-y-6">
                        <div className="bg-slate-950/60 border border-slate-800/60 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-3">Clone Custom Voice Profile</h4>
                          <div className="flex items-center gap-3">
                            <input
                              type="text"
                              placeholder="E.g. David Narrator tone"
                              value={cloneName}
                              onChange={(e) => setCloneName(e.target.value)}
                              className="flex-1 bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-xs focus:border-violet-500 focus:outline-none text-slate-200"
                              disabled={cloning}
                            />
                            <button
                              onClick={() => handleCloneVoice(activeJob.id)}
                              className="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-bold rounded-xl p-3 text-xs flex items-center gap-1.5"
                              disabled={cloning || !cloneName}
                            >
                              <Plus className="h-4 w-4" />
                              {cloning ? 'Cloning...' : 'Clone Profile'}
                            </button>
                          </div>
                        </div>

                        {activePkg.voice_profile && (
                          <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl space-y-3">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Active speaker profile</h4>
                            <div className="grid grid-cols-2 gap-4 text-xs font-semibold">
                              <div>
                                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Narration Voice ID</div>
                                <p className="text-slate-200 font-mono">{activePkg.voice_profile.voice_id}</p>
                              </div>
                              <div>
                                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Cloned Voice ID</div>
                                <p className="text-slate-200 font-mono">{activePkg.voice_profile.cloned_voice_id || "None active"}</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Lineage Diff Tab */}
                    {selectedTab === "compare" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Voice Package version lineages</h4>
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
                                  <p className="text-slate-400 italic mb-2">"{snap.narration}"</p>
                                  <div className="text-[10px] text-slate-500 font-bold">Path: {snap.local_path} | Quality: {snap.quality_score}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                            Select a historical Voice package version from the dropdown to run lineage comparison.
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
              <Mic className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Voice Narration Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active voice synthesis job from the history sidebar list to view generated audios, subtitles timeline offsets, and SSML builder scripts.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
