"use client";

import React, { useEffect, useState } from "react";
import { 
  Compass, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Layers, 
  Sliders, 
  Play, 
  ShieldCheck, 
  Cpu, 
  GitBranch, 
  Radio, 
  Lock, 
  Pause, 
  Trash2, 
  Zap, 
  Settings2 
} from "lucide-react";

export default function OrchestrationCenterPage() {
  const [objectiveType, setObjectiveType] = useState("GENERATE_LONGFORM_VIDEO");
  const [targetPlatform, setTargetPlatform] = useState("all");

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [objectives, setObjectives] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("graph");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const jRes = await fetch("/api/v1/orchestration");
      if (jRes.ok) {
        const data = await jRes.json();
        setJobs(data);
        if (data.length > 0 && !selectedJob) setSelectedJob(data[0]);
      }

      const mRes = await fetch("/api/v1/orchestration/metrics");
      if (mRes.ok) setMetrics(await mRes.json());

      const oRes = await fetch("/api/v1/orchestration/objectives");
      if (oRes.ok) setObjectives(await oRes.json());

      const pRes = await fetch("/api/v1/orchestration/plans");
      if (pRes.ok) setPlans(await pRes.json());
    } catch (e) {
      console.error("Failed to load orchestration data:", e);
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
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/orchestration", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          objective_type: objectiveType,
          target_platform: targetPlatform
        })
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePauseJob = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/orchestration/${id}/pause`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResumeJob = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/orchestration/${id}/resume`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-purple-400 via-pink-400 to-amber-400 bg-clip-text text-transparent flex items-center gap-3">
            <span>AI Multi-Agent Orchestrator</span>
            <span className="text-xs bg-purple-950/80 text-purple-300 border border-purple-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
              Strategic Control v1.0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Master strategic coordination layer planning, scheduling, and adaptively replanning multi-agent execution graphs (DAGs) across all 12 platform agents and engines.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-purple-400 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Orchestration Score</div>
              <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <span className="text-purple-300 font-black">{Math.round(metrics.overall_orchestration_confidence * 100)}%</span>
                <span className="text-[10px] bg-purple-950 text-purple-300 px-1.5 py-0.2 rounded font-mono">DAG Active</span>
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
              <Compass className="h-3.5 w-3.5 text-purple-400" />
              Active Objectives
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.total_active_objectives || objectives.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5 text-pink-400" />
              Generated Plans
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.total_plans_generated || plans.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-amber-400 animate-pulse" />
              Executing Jobs
            </div>
            <div className="text-2xl font-black text-amber-400">{metrics.jobs_processing}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
              Completed Jobs
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_succeeded}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20 col-span-2">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              Global Orchestration Confidence
            </div>
            <div className="text-2xl font-black text-slate-100">{Math.round(metrics.overall_orchestration_confidence * 100)}%</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & Jobs Queue */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Dispatch Strategic Objective Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Compass className="h-5 w-5 text-purple-400" />
              Dispatch Business Objective
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Objective Blueprint</label>
                <select
                  value={objectiveType}
                  onChange={(e) => setObjectiveType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-purple-500 focus:outline-none text-slate-200"
                >
                  <option value="GENERATE_LONGFORM_VIDEO">Generate Longform Video (YouTube + Shorts)</option>
                  <option value="GENERATE_SHORTS">Generate Viral Shorts Pipeline</option>
                  <option value="REPUBLISH_EXISTING_CONTENT">Republish Content to Multi-Platform</option>
                  <option value="RUN_THUMBNAIL_EXPERIMENT">Run Thumbnail A/B Contrast Experiment</option>
                  <option value="MULTI_PLATFORM_PUBLISHING">Multi-Platform Simultaneous Campaign</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Destination Platform</label>
                <div className="grid grid-cols-3 gap-2">
                  {["all", "instagram", "youtube"].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setTargetPlatform(p)}
                      className={`p-2.5 rounded-xl border text-xs font-bold capitalize transition-all ${targetPlatform === p ? 'bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-900/30' : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-900'}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-95 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting}
              >
                <Play className="h-4 w-4 fill-white" />
                {submitting ? 'Planning...' : 'Plan & Orchestrate Objective'}
              </button>
            </form>
          </div>

          {/* Orchestrated Jobs Queue */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-pink-400" />
              Orchestration Jobs Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading orchestration history...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active orchestration jobs found.
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
                          {job.objective_type}
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
                              className="bg-gradient-to-r from-purple-500 to-amber-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div>Platform: <span className="uppercase text-slate-300">{job.target_platform}</span></div>
                        <div className="flex items-center gap-2">
                          {job.status === "PROCESSING" ? (
                            <button onClick={(e) => { e.stopPropagation(); handlePauseJob(job.id); }} className="text-amber-400 hover:text-amber-300 font-bold flex items-center gap-1">
                              <Pause className="h-3 w-3" /> Pause
                            </button>
                          ) : (
                            <button onClick={(e) => { e.stopPropagation(); handleResumeJob(job.id); }} className="text-purple-400 hover:text-purple-300 font-bold flex items-center gap-1">
                              <Play className="h-3 w-3" /> Resume
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Orchestration Dashboard */}
        <div className="lg:col-span-8">
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
            
            {/* Navigation Tabs */}
            <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
              {[
                { id: "graph", label: "Live Execution Graph (DAG)", icon: GitBranch },
                { id: "objectives", label: "Objectives & Plans", icon: Compass },
                { id: "resources", label: "Resource Reservations & Health", icon: Cpu },
                { id: "replanning", label: "Adaptive Replanning & Decisions", icon: RefreshCw }
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

            {/* Tab 1: Live Execution Graph (DAG) */}
            {selectedTab === "graph" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                    Multi-Agent Execution DAG Graph
                  </h4>
                  <span className="text-xs bg-slate-900 text-slate-400 border border-slate-800 px-2.5 py-0.5 rounded font-mono">
                    Critical Path: 5 Nodes
                  </span>
                </div>

                <div className="bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-6">
                  {/* Visual Node Chain */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                    {[
                      { id: "node_research", name: "ResearchAgent", role: "Intelligence", status: "SUCCESS", time: "40s" },
                      { id: "node_script", name: "ScriptAgent", role: "Creative", status: "SUCCESS", time: "30s", critical: true },
                      { id: "node_image", name: "ImageAgent", role: "Assets (GPU)", status: "SUCCESS", time: "60s", critical: true },
                      { id: "node_voice", name: "VoiceAgent", role: "Audio", status: "SUCCESS", time: "30s" },
                      { id: "node_video", name: "VideoAgent", role: "Production (GPU)", status: "SUCCESS", time: "90s", critical: true },
                      { id: "node_subtitle", name: "SubtitleAgent", role: "Accessibility", status: "SUCCESS", time: "20s" },
                      { id: "node_music", name: "MusicAgent", role: "Audio", status: "SUCCESS", time: "20s" },
                      { id: "node_thumbnail", name: "ThumbnailAgent", role: "Growth", status: "SUCCESS", time: "25s" },
                      { id: "node_quality", name: "QualityAgent", role: "Governance", status: "SUCCESS", time: "15s", critical: true },
                      { id: "node_publish", name: "PublishingProvider", role: "Distribution", status: "SUCCESS", time: "40s", critical: true }
                    ].map((n) => (
                      <div 
                        key={n.id} 
                        className={`p-3 rounded-lg border flex flex-col justify-between gap-1.5 transition-all ${n.critical ? 'bg-purple-950/40 border-purple-500/80 shadow-sm shadow-purple-900/20' : 'bg-slate-900/50 border-slate-850'}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-200 text-[11px]">{n.name}</span>
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                        </div>
                        <div className="text-[10px] text-slate-400">{n.role}</div>
                        <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800">
                          <span>Est: {n.time}</span>
                          {n.critical && <span className="text-purple-400 font-bold">CP</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Objectives & Plans */}
            {selectedTab === "objectives" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                  Registered Business Objectives ({objectives.length})
                </h4>

                <div className="space-y-3">
                  {objectives.map((o) => (
                    <div key={o.objective_id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-100">{o.title}</span>
                          <span className="text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
                            {o.objective_type}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400">
                          Target Platform: <strong className="text-purple-300 uppercase">{o.target_platform}</strong> • Priority: {o.priority}
                        </div>
                      </div>
                      <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                        {o.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 3: Resource Reservations & Health */}
            {selectedTab === "resources" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                  Resource Reservations & Worker Pool Health
                </h4>

                <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4">
                  <div className="grid grid-cols-2 gap-4 border-b border-slate-900 pb-4">
                    <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                      <div className="text-xs font-bold text-slate-400">GPU Slot Reservations</div>
                      <div className="text-xl font-black text-purple-300 mt-1">1 / 2 Allocated</div>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                      <div className="text-xs font-bold text-slate-400">Worker Pool Slots</div>
                      <div className="text-xl font-black text-amber-300 mt-1">7 / 8 Available</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs font-bold text-slate-300">Active Worker Daemons</div>
                    <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-850 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="font-mono text-slate-200">orchestrator-worker-0</span>
                      </div>
                      <span className="text-slate-400 font-mono">Heartbeat: Healthy (0s ago)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: Adaptive Replanning & Decisions */}
            {selectedTab === "replanning" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                  Strategic Decision Log & Adaptive Replanning Events
                </h4>

                <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-3">
                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850 space-y-1 text-xs">
                    <div className="flex items-center justify-between font-bold text-slate-200">
                      <span>Strategic Planning Decision (obj_longform_001)</span>
                      <span className="text-purple-300 font-mono">Confidence: 0.96</span>
                    </div>
                    <div className="text-slate-400">
                      Selected 10-agent parallel execution plan with GPU allocation for VideoAgent & ImageAgent.
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
}
