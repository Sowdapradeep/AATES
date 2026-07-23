"use client";

import React, { useEffect, useState } from "react";
import { 
  FileText, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  BookOpen, 
  TrendingUp, 
  Users, 
  Compass, 
  Eye, 
  ExternalLink,
  Layers,
  Sparkles,
  Award,
  Video,
  Play,
  RotateCcw,
  Edit2,
  ChevronRight,
  GitCompare,
  CheckSquare
} from "lucide-react";

export default function ScriptsPage() {
  const [kpList, setKpList] = useState<any[]>([]);
  const [selectedKpId, setSelectedKpId] = useState("");
  const [platform, setPlatform] = useState("youtube_shorts");
  const [language, setLanguage] = useState("ta");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("script");
  const [diffVersionId, setDiffVersionId] = useState("");
  
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editNarration, setEditNarration] = useState("");

  const fetchData = async () => {
    try {
      const kpRes = await fetch("/api/v1/research");
      if (kpRes.ok) {
        const kpData = await kpRes.json();
        // filter successful ones that have packages
        const succKps = kpData.filter((j: any) => j.status === "SUCCESS" && j.packages?.length > 0);
        setKpList(succKps);
      }
      const jobsRes = await fetch("/api/v1/scripts");
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData);
      }
      const metricsRes = await fetch("/api/v1/scripts/metrics");
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }
    } catch (e) {
      console.error("Failed to load script data:", e);
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
    if (!selectedKpId) return;
    setSubmitting(true);
    try {
      // Find package id corresponding to selected kp research job
      const kpJob = kpList.find(j => j.id === selectedKpId);
      const knowledgePackageId = kpJob?.packages?.[0]?.id;
      
      const res = await fetch("/api/v1/scripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          knowledge_package_id: knowledgePackageId, 
          platform, 
          language,
          priority 
        })
      });
      if (res.ok) {
        setSelectedKpId("");
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
      const res = await fetch(`/api/v1/scripts/${id}/regenerate`, { method: "POST" });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Failed to regenerate:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/scripts/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchData();
    } catch (e) {
      console.error("Failed to delete job:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;

  // Sync edit text when package changes
  useEffect(() => {
    if (activePkg) {
      setEditNarration(activePkg.narration);
    }
  }, [activePkg]);

  const saveScriptEdits = () => {
    if (activePkg) {
      activePkg.narration = editNarration;
      setIsEditing(false);
    }
  };

  // Find selected diff version
  const diffVersion = activePkg?.versions?.find((v: any) => v.id === diffVersionId) || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-violet-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
            AI Script Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Converts researched knowledge packages into production-ready scripts. Review, score, and auto-improve content before production.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Script Agents Status</div>
              <div className="text-sm font-bold text-slate-200">
                {metrics.worker_is_running ? `Online (${metrics.current_worker_count} Agents active)` : 'Offline'}
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
              Avg Script Build Time
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
          </div>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & History */}
        <div className="lg:col-span-5 space-y-6">
          {/* Submit Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-violet-400" />
              Generate Script Package
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Knowledge Package</label>
                <select
                  value={selectedKpId}
                  onChange={(e) => setSelectedKpId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Research --</option>
                  {kpList.map((j) => (
                    <option key={j.id} value={j.id}>{j.topic} (KnowledgePackage)</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Target Platform</label>
                  <select
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="youtube_shorts">YouTube Shorts</option>
                    <option value="youtube_longform">YouTube Long-form</option>
                    <option value="instagram_reels">Instagram Reels</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Locale Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-violet-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="ta">Tamil (ta)</option>
                    <option value="en">English (en)</option>
                  </select>
                </div>
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
                    disabled={submitting || !selectedKpId}
                  >
                    <Play className="h-4 w-4" />
                    {submitting ? 'Enqueuing...' : 'Run Script Agent'}
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Script Jobs List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Script Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading campaign indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active script jobs found. Run a script agent above!
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
                          {job.packages?.[0]?.title || `Script Job: ${job.platform}`}
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
                          <span>Platform: {job.platform}</span>
                          <span>•</span>
                          <span>Priority: {job.priority}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(job.id); }}
                            className="text-rose-400 hover:text-rose-300 font-bold"
                          >
                            Delete
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

        {/* Right Column: Detailed Script Package Viewer */}
        <div className="lg:col-span-7">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Job Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-violet-400 uppercase tracking-widest">
                    Script Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg?.title || `Draft: ${activeJob.platform}`}
                  </h3>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {activePkg && (
                    <button
                      onClick={() => handleRegenerate(activeJob.id)}
                      className="bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-700 hover:to-pink-700 font-semibold rounded-lg p-2 px-3 text-xs flex items-center gap-1.5 shadow-md shadow-violet-900/10 active:scale-95 transition-all text-white"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      Regenerate
                    </button>
                  )}
                </div>
              </div>

              {activeJob.status === "QUEUED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Clock className="h-12 w-12 text-slate-600 animate-pulse" />
                  <div>
                    <h4 className="font-bold text-slate-300">Script Generation Enqueued</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Waiting for the background Script Agent to start parsing the knowledge package references.
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "PROCESSING" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Activity className="h-12 w-12 text-violet-500 animate-spin" style={{ animationDuration: '4s' }} />
                  <div>
                    <h4 className="font-bold text-slate-300">Generating Script: {activeJob.stage}</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Executing Bedrock inference, validating hook presence, scoring, and auto-improving.
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
                    <h4 className="font-bold text-rose-400">Script Generation Failed</h4>
                    <p className="text-slate-400 text-xs max-w-md mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-left font-mono break-all">
                      {activeJob.error_message || 'Internal processing error occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "SUCCESS" && !activePkg && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <RefreshCw className="h-12 w-12 text-slate-600 animate-spin" />
                  <p className="text-slate-500 text-sm font-semibold">Ingesting Script Package elements...</p>
                </div>
              )}

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">
                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "script", label: "Script Editor", icon: Edit2 },
                      { id: "scenes", label: "Scene Breakdown", icon: Video },
                      { id: "review", label: "AI Quality Score", icon: Award },
                      { id: "compare", label: "Version Diff", icon: GitCompare },
                      { id: "checklist", label: "Knowledge Match", icon: CheckSquare }
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
                    
                    {/* Script Editor Tab */}
                    {selectedTab === "script" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Narration Script</h4>
                          <button
                            onClick={() => isEditing ? saveScriptEdits() : setIsEditing(true)}
                            className="bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg p-1.5 px-3 text-xs font-semibold flex items-center gap-1.5 text-slate-300"
                          >
                            <Edit2 className="h-3 w-3" />
                            {isEditing ? 'Save Changes' : 'Edit Script'}
                          </button>
                        </div>
                        
                        {isEditing ? (
                          <textarea
                            value={editNarration}
                            onChange={(e) => setEditNarration(e.target.value)}
                            rows={12}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-semibold focus:border-violet-500 focus:outline-none text-slate-200 leading-relaxed"
                          />
                        ) : (
                          <div className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl text-xs font-medium text-slate-300 leading-relaxed whitespace-pre-line">
                            {activePkg.narration}
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1 bg-slate-950/40 border border-slate-800/40 p-3 rounded-xl">
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Hook</span>
                            <p className="text-xs italic text-slate-300">"{activePkg.hook}"</p>
                          </div>
                          <div className="space-y-1 bg-slate-950/40 border border-slate-800/40 p-3 rounded-xl">
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Call to Action (CTA)</span>
                            <p className="text-xs italic text-slate-300">"{activePkg.cta}"</p>
                          </div>
                        </div>

                        {/* Telemetry info */}
                        {activePkg.metadata && (
                          <div className="border-t border-slate-850 pt-4 flex flex-wrap gap-4 text-[11px] text-slate-500 font-medium">
                            <span>Model: {activePkg.metadata.model_id}</span>
                            <span>•</span>
                            <span>Prompt: {activePkg.metadata.prompt_version}</span>
                            <span>•</span>
                            <span>Temp: {activePkg.metadata.temperature}</span>
                            <span>•</span>
                            <span>Review iterations: {activePkg.metadata.improvement_count || 0}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Scene Breakdown Tab */}
                    {selectedTab === "scenes" && (
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Scene Breakdown list</h4>
                        <div className="space-y-4">
                          {activePkg.scene_breakdown?.map((scene: any) => (
                            <div key={scene.scene_number} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-3">
                              <div className="flex justify-between items-center border-b border-slate-850 pb-2">
                                <span className="font-extrabold text-xs text-slate-200">Scene {scene.scene_number} ({scene.duration}s)</span>
                                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                                  {scene.camera_angle || 'Medium Close Up'}
                                </span>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold text-slate-300 leading-relaxed">
                                <div className="space-y-1.5">
                                  <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Visual Prompt</div>
                                  <p className="text-slate-200">{scene.visual_prompt}</p>
                                  {scene.background && <p className="text-[11px] text-slate-400 font-medium">Background: {scene.background}</p>}
                                </div>
                                <div className="space-y-1.5">
                                  <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Audio Narration</div>
                                  <p className="text-slate-300">{scene.narration || scene.audio_narration}</p>
                                  {scene.onscreen_text && <p className="text-[11px] text-pink-400 font-medium">On-screen: "{scene.onscreen_text}"</p>}
                                </div>
                              </div>
                              {scene.sound_effects && scene.sound_effects.length > 0 && (
                                <div className="text-[10px] font-bold text-slate-500">
                                  Sound FX: <span className="text-slate-400">{scene.sound_effects.join(", ")}</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI Quality Score Tab */}
                    {selectedTab === "review" && activePkg.review_report && (
                      <div className="space-y-6">
                        <div className="flex items-center justify-between gap-4 bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl">
                          <div>
                            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">AI Quality Grade</div>
                            <div className="text-3xl font-black text-slate-100">{Math.round(activePkg.quality_score * 100)}%</div>
                          </div>
                          <span className={`text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-lg ${activePkg.quality_score >= 0.8 ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'}`}>
                            {activePkg.quality_score >= 0.8 ? 'Approved' : 'Needs Optimization'}
                          </span>
                        </div>

                        <div className="space-y-2">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Dimension Scores</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                            {[
                              { label: "Hook strength", val: activePkg.review_report.hook_score },
                              { label: "Story flow", val: activePkg.review_report.story_score },
                              { label: "CTA quality", val: activePkg.review_report.cta_score },
                              { label: "SEO indexing", val: activePkg.review_report.seo_score },
                              { label: "Viewer retention", val: activePkg.review_report.retention_score },
                              { label: "Platform Suitability", val: activePkg.review_report.platform_score },
                              { label: "Factual Consistency", val: activePkg.review_report.consistency_score || 0.8 },
                              { label: "Language Quality", val: activePkg.review_report.grammar_score || 0.9 }
                            ].map((dim, idx) => (
                              <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg flex flex-col gap-1">
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{dim.label}</span>
                                <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                                  <span>{Math.round(dim.val * 100)}%</span>
                                  <div className="w-16 bg-slate-900 h-1 rounded-full overflow-hidden">
                                    <div className="bg-violet-500 h-full" style={{ width: `${dim.val * 100}%` }} />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {activePkg.review_report.suggestions && activePkg.review_report.suggestions.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">AI Director Review Comments</h4>
                            <div className="space-y-2">
                              {activePkg.review_report.suggestions.map((comment: string, idx: number) => (
                                <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg flex items-start gap-2.5">
                                  <span className="h-5 w-5 bg-rose-950 text-rose-400 text-xs font-black flex items-center justify-center rounded-md flex-shrink-0">
                                    !
                                  </span>
                                  <span className="text-slate-300 text-xs font-medium">{comment}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Version Diff Tab */}
                    {selectedTab === "compare" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Version Diff comparison</h4>
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
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                                Current Active (v{activePkg.version})
                              </div>
                              <div className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl text-xs text-slate-300 leading-relaxed max-h-[300px] overflow-y-auto">
                                {activePkg.narration}
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="text-[11px] font-bold text-violet-400 uppercase tracking-wider">
                                Historical Archive (v{diffVersion.version})
                              </div>
                              <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-xl text-xs text-slate-400 leading-relaxed max-h-[300px] overflow-y-auto italic">
                                {diffVersion.narration}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                            Select a historical script version from the dropdown to run comparison diff.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Knowledge vs Script Tab */}
                    {selectedTab === "checklist" && (
                      <div className="space-y-4 bg-slate-950/40 border border-slate-800/40 p-4 rounded-2xl">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Knowledge Package coverage checklist</h4>
                        <p className="text-xs text-slate-500 leading-relaxed">
                          Verify that the script successfully carried through facts, keywords, and hooks from the originating research.
                        </p>
                        
                        <div className="space-y-4 mt-2">
                          <div className="space-y-2">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Keywords Index</span>
                            <div className="flex flex-wrap gap-2">
                              {activePkg.target_audience?.map((kw: string, idx: number) => (
                                <div key={idx} className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1.5 px-3 rounded-lg text-xs font-medium text-slate-300">
                                  <input type="checkbox" defaultChecked className="accent-violet-500 rounded" />
                                  <span>{kw}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="space-y-2">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">References URLs</span>
                            <div className="space-y-1.5">
                              {activePkg.references?.map((ref: string, idx: number) => (
                                <div key={idx} className="flex items-center gap-2 text-xs font-medium">
                                  <input type="checkbox" defaultChecked className="accent-violet-500" />
                                  <a href={ref} target="_blank" rel="noreferrer" className="text-violet-400 hover:underline flex items-center gap-1">
                                    {ref}
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <FileText className="h-12 w-12 text-slate-700 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Script Output Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active script job from the history sidebar list to view scene breakdowns, narration transcripts, quality scores, and version lineages.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
