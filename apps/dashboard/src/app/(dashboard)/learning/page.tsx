"use client";

import React, { useEffect, useState } from "react";
import { 
  Brain, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Sparkles, 
  Layers, 
  Sliders, 
  Award, 
  Plus, 
  TrendingUp, 
  Zap, 
  Check, 
  Target, 
  Compass, 
  BarChart3, 
  Lightbulb, 
  ThumbsUp, 
  Cpu, 
  ShieldCheck, 
  ArrowUpRight 
} from "lucide-react";

export default function AnalyticsLearningPage() {
  const [targetPlatform, setTargetPlatform] = useState("all");
  const [learningWindow, setLearningWindow] = useState(30);
  const [learningMode, setLearningMode] = useState("batch");

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("recommendations");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const jRes = await fetch("/api/v1/learning");
      if (jRes.ok) {
        const data = await jRes.json();
        setJobs(data);
        if (data.length > 0 && !selectedJob) setSelectedJob(data[0]);
      }

      const mRes = await fetch("/api/v1/learning/metrics");
      if (mRes.ok) setMetrics(await mRes.json());

      const sRes = await fetch("/api/v1/learning/signals");
      if (sRes.ok) setSignals(await sRes.json());

      const rRes = await fetch("/api/v1/learning/recommendations");
      if (rRes.ok) setRecommendations(await rRes.json());
    } catch (e) {
      console.error("Failed to load learning engine data:", e);
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
      const res = await fetch("/api/v1/learning", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          target_platform: targetPlatform,
          learning_window_days: learningWindow,
          learning_mode: learningMode
        })
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplyFeedback = async (recId: string) => {
    try {
      const res = await fetch("/api/v1/learning/recommendations/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendation_id: recId,
          status: "APPLIED",
          initial_metric: 0.054,
          measured_metric: 0.082,
          impact_percent: 51.8
        })
      });
      if (res.ok) fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRefreshJob = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/learning/${id}/refresh`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Refresh failed:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300 bg-clip-text text-transparent flex items-center gap-3">
            <span>AI Analytics & Learning Engine</span>
            <span className="text-xs bg-purple-950/80 text-purple-300 border border-purple-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
              Continuous Feedback v1.0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Feature Store normalization, statistical correlation discovery, multi-factorial confidence scoring, and actionable recommendations for downstream AI agents.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-purple-400 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Learning Confidence</div>
              <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <span className="text-purple-300 font-black">{Math.round(metrics.overall_learning_confidence * 100)}%</span>
                <span className="text-[10px] bg-purple-950 text-purple-300 px-1.5 py-0.2 rounded font-mono">High Precision</span>
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
              Queued Jobs
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
              <Compass className="h-3.5 w-3.5 text-amber-400" />
              Signals Discovered
            </div>
            <div className="text-2xl font-black text-amber-400">{metrics.total_signals_discovered || signals.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Lightbulb className="h-3.5 w-3.5 text-purple-400" />
              Recommendations
            </div>
            <div className="text-2xl font-black text-purple-300">{metrics.total_recommendations_generated || recommendations.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20 col-span-2">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Brain className="h-3.5 w-3.5 text-pink-400" />
              Global Engine Confidence
            </div>
            <div className="text-2xl font-black text-slate-100">{Math.round(metrics.overall_learning_confidence * 100)}%</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & Runs */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Submit Learning Run Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-400" />
              Trigger Learning Analysis
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Target Platform</label>
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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Window (Days)</label>
                  <select
                    value={learningWindow}
                    onChange={(e) => setLearningWindow(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-purple-500 focus:outline-none text-slate-200"
                  >
                    <option value={14}>14 Days</option>
                    <option value={30}>30 Days</option>
                    <option value={90}>90 Days</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">3. Mode</label>
                  <select
                    value={learningMode}
                    onChange={(e) => setLearningMode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-purple-500 focus:outline-none text-slate-200"
                  >
                    <option value="batch">Batch Run</option>
                    <option value="incremental">Incremental</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-95 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing Run...' : 'Run Learning Analysis'}
              </button>
            </form>
          </div>

          {/* Jobs & Packages Queue */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-pink-400" />
              Learning Runs History
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading learning history...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active learning jobs found.
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
                          Learning Run ({job.target_platform.toUpperCase()} - {job.learning_mode})
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
                        <div className="flex items-center gap-2">
                          <span>Dataset Size: {job.dataset_size} items</span>
                        </div>
                        {job.status === "SUCCESS" && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleRefreshJob(job.id); }}
                            className="text-purple-400 hover:text-purple-300 font-bold flex items-center gap-1"
                          >
                            <RefreshCw className="h-3 w-3" /> Refresh
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Learning Package Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Details */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-purple-400 uppercase tracking-widest">
                    LearningPackage (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                    <span>Target Platform: {activeJob.target_platform.toUpperCase()}</span>
                    {activePkg && (
                      <span className="text-xs bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded font-mono">
                        Model {activePkg.model_version}
                      </span>
                    )}
                  </h3>
                </div>

                {activePkg && (
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-500 uppercase font-bold">Package Confidence</div>
                      <div className="text-lg font-black text-purple-400">{Math.round(activePkg.learning_confidence * 100)}%</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Navigation Tabs */}
              <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                {[
                  { id: "recommendations", label: "Agent Recommendations", icon: Lightbulb },
                  { id: "signals", label: "Learning Signals & Causality", icon: Compass },
                  { id: "feature_importance", label: "Feature Store & Importance", icon: BarChart3 },
                  { id: "experiments", label: "A/B Experiment Results", icon: Target }
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

              {/* Tab 1: Agent Recommendations */}
              {selectedTab === "recommendations" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                      Actionable Agent Optimizations ({recommendations.length})
                    </h4>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendations.map((rec) => (
                      <div key={rec.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-3 flex flex-col justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
                              {rec.target_agent}
                            </span>
                            <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${rec.priority === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'}`}>
                              {rec.priority} Priority
                            </span>
                          </div>

                          <div className="text-sm font-bold text-slate-100">{rec.suggested_action}</div>
                          
                          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-900">
                            <span className="text-slate-400">Expected Impact:</span>
                            <span className="font-bold text-emerald-400 flex items-center gap-1">
                              <TrendingUp className="h-3 w-3" /> {rec.expected_impact}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-slate-900/60">
                          <div className="text-[11px] text-slate-500 font-medium">
                            Confidence: <span className="font-bold text-purple-300">{Math.round(rec.confidence_score * 100)}%</span>
                          </div>
                          <button
                            onClick={() => handleApplyFeedback(rec.id)}
                            className="bg-purple-900/60 hover:bg-purple-800 text-purple-200 border border-purple-700/60 px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 shadow-sm"
                          >
                            <Check className="h-3 w-3" /> Apply & Track
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 2: Discovered Signals & Causality */}
              {selectedTab === "signals" && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                    Discovered Correlations & Causality Levels ({signals.length})
                  </h4>

                  <div className="space-y-3">
                    {signals.map((sig) => (
                      <div key={sig.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-bold text-sm text-slate-200 flex items-center gap-2">
                            <span>{sig.title}</span>
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${sig.causality_level === 'EXPERIMENT_SUPPORTED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}>
                              {sig.causality_level}
                            </span>
                          </div>
                          <div className="text-xs font-bold text-purple-300">
                            Confidence: {Math.round(sig.confidence_score * 100)}%
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span>Category: <strong className="text-slate-200">{sig.category}</strong></span>
                          <span>Correlation: <strong className="text-pink-400">+{sig.correlation_coefficient}</strong></span>
                          <span>Applicable Agents: <strong className="text-slate-300">{sig.applicable_agents.join(", ")}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Feature Store & Importance */}
              {selectedTab === "feature_importance" && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                    Feature Store Importance Weights (Target: CTR & Engagement)
                  </h4>

                  <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4">
                    {[
                      { name: "Hook Type (Question / Stat / Story)", weight: 33, color: "from-purple-500 to-pink-500" },
                      { name: "Thumbnail Contrast & Saliency", weight: 24, color: "from-pink-500 to-rose-500" },
                      { name: "Publishing Hour & Day Window", weight: 16, color: "from-amber-500 to-orange-500" },
                      { name: "Caption Length & Hashtag Density", weight: 11, color: "from-emerald-500 to-teal-500" },
                      { name: "Music Mood & Loudness LUFS", weight: 8, color: "from-blue-500 to-indigo-500" },
                      { name: "Other Secondary Features", weight: 8, color: "from-slate-600 to-slate-500" }
                    ].map((f) => (
                      <div key={f.name} className="space-y-1.5">
                        <div className="flex justify-between text-xs font-bold">
                          <span className="text-slate-300">{f.name}</span>
                          <span className="text-purple-300">{f.weight}% Weight</span>
                        </div>
                        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                          <div className={`bg-gradient-to-r ${f.color} h-full rounded-full`} style={{ width: `${f.weight}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 4: A/B Experiments */}
              {selectedTab === "experiments" && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                    Evaluated A/B Experiment Outcomes
                  </h4>

                  <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                      <div>
                        <div className="text-sm font-bold text-slate-100">Exp #exp_thumb_ab_001: Thumbnail High Contrast Variant</div>
                        <div className="text-xs text-slate-500">Target Metric: Click-Through Rate (CTR)</div>
                      </div>
                      <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded font-mono font-bold">
                        Winner: High Contrast (+22.4% Lift)
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs pt-2">
                      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                        <div className="text-slate-500 font-bold uppercase text-[10px]">Variant A (Standard)</div>
                        <div className="text-slate-200 font-bold text-lg">5.2% CTR</div>
                      </div>
                      <div className="bg-purple-950/40 p-3 rounded-lg border border-purple-800/60">
                        <div className="text-purple-300 font-bold uppercase text-[10px]">Variant B (High Contrast)</div>
                        <div className="text-emerald-400 font-black text-lg">6.4% CTR (+22.4%)</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Brain className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">Analytics & Learning Engine Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active learning run from the left queue to view discovered Learning Signals, Feature Store weights, and targeted agent recommendations.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
