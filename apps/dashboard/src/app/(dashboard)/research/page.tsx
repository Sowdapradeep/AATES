"use client";

import React, { useEffect, useState } from "react";
import { 
  Search, 
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
  Shield,
  Layers,
  Sparkles,
  Award,
  Video,
  Loader2
} from "lucide-react";

export default function ResearchPage() {
  const [topic, setTopic] = useState("");
  const [priority, setPriority] = useState(0);
  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("summary");
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchJobsAndMetrics = async () => {
    try {
      const jobsRes = await fetch("/api/v1/research");
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData);
      }
      const metricsRes = await fetch("/api/v1/research/metrics");
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }
    } catch (e) {
      console.error("Failed to load research data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobsAndMetrics();
    const interval = setInterval(fetchJobsAndMetrics, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, priority })
      });
      if (res.ok) {
        setTopic("");
        setPriority(0);
        fetchJobsAndMetrics();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await fetch(`/api/v1/research/${id}/retry`, { method: "POST" });
      fetchJobsAndMetrics();
    } catch (e) {
      console.error("Failed to retry job:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/research/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      fetchJobsAndMetrics();
    } catch (e) {
      console.error("Failed to delete job:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const knowledgePkg = activeJob?.packages?.[0] || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-violet-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
            AI Research Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated topic research, visual scene prompting, competitor tracking, and Bedrock knowledge packaging.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Research Agents Status</div>
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
              Avg Processing Time
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
              New Research Campaign
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Topic Keyword / Theme</label>
                <div className="relative">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. History of Tanjore Temple or Python Async Tips"
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 pl-10 text-sm focus:border-violet-500 focus:outline-none text-slate-200 placeholder-slate-500"
                    disabled={submitting}
                  />
                  <Search className="absolute left-3 top-3.5 h-4.5 w-4.5 text-slate-500" />
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
                    disabled={submitting || !topic.trim()}
                  >
                    {submitting ? 'Enqueuing...' : 'Initiate Agent'}
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Research Jobs List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Research History
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading campaign indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active research jobs found. Submit a topic above!
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
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">{job.topic}</div>
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
                          <span>Priority: {job.priority}</span>
                          <span>•</span>
                          <span>Search results: {job.search_count}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {job.status === "FAILED" && (
                            <button
                              onClick={(e) => { e.stopPropagation(); handleRetry(job.id); }}
                              className="text-violet-400 hover:text-violet-300 font-bold"
                            >
                              Retry
                            </button>
                          )}
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

        {/* Right Column: Detailed Viewer */}
        <div className="lg:col-span-7">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              {/* Job Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-violet-400 uppercase tracking-widest">Selected Topic Campaign</div>
                  <h3 className="text-xl font-bold text-slate-100">{activeJob.topic}</h3>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs text-slate-400 font-medium">
                    Duration: {activeJob.duration_sec ? `${activeJob.duration_sec.toFixed(1)}s` : 'N/A'}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">
                    Bedrock time: {activeJob.summary_time_sec ? `${activeJob.summary_time_sec.toFixed(1)}s` : 'N/A'}
                  </span>
                </div>
              </div>

              {activeJob.status === "QUEUED" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Clock className="h-12 w-12 text-slate-600 animate-pulse" />
                  <div>
                    <h4 className="font-bold text-slate-300">Campaign Enqueued</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      Waiting for the background Research Agent to pick up and analyze this topic.
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "PROCESSING" && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Activity className="h-12 w-12 text-violet-500 animate-spin" style={{ animationDuration: '4s' }} />
                  <div>
                    <h4 className="font-bold text-slate-300">Researching: Stage {activeJob.stage}</h4>
                    <p className="text-slate-500 text-sm max-w-sm mt-1">
                      The Agent is discovering knowledge urls, collecting documents, and analyzing facts.
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
                    <h4 className="font-bold text-rose-400">Research Failed</h4>
                    <p className="text-slate-400 text-xs max-w-md mt-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-left font-mono break-all">
                      {activeJob.error_message || 'Internal processing error occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {activeJob.status === "SUCCESS" && !knowledgePkg && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <Loader2 className="h-12 w-12 text-slate-600 animate-spin" />
                  <p className="text-slate-500 text-sm">Ingesting Knowledge Package content...</p>
                </div>
              )}

              {activeJob.status === "SUCCESS" && knowledgePkg && (
                <div className="flex flex-col gap-6">
                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "summary", label: "Summary", icon: BookOpen },
                      { id: "story", label: "Story Outline", icon: Video },
                      { id: "visuals", label: "Visual Ideas", icon: Compass },
                      { id: "keywords", label: "Keywords", icon: TrendingUp },
                      { id: "competitors", label: "Competitors", icon: Users },
                      { id: "sources", label: "References", icon: Eye }
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
                    
                    {selectedTab === "summary" && (
                      <div className="space-y-6">
                        <div className="space-y-2">
                          <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Executive Summary</h4>
                          <p className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl text-slate-300 font-medium">
                            {knowledgePkg.summary}
                          </p>
                        </div>
                        
                        {knowledgePkg.statistics && knowledgePkg.statistics.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Key Statistics & Metrics</h4>
                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {knowledgePkg.statistics.map((s: string, idx: number) => (
                                <li key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg flex items-start gap-2">
                                  <Award className="h-4.5 w-4.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                                  <span className="text-slate-300 text-xs">{s}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {knowledgePkg.pain_points && knowledgePkg.pain_points.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Audience Pain Points</h4>
                            <div className="space-y-2">
                              {knowledgePkg.pain_points.map((p: string, idx: number) => (
                                <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg flex items-start gap-2.5">
                                  <span className="h-5 w-5 bg-rose-950 text-rose-400 text-xs font-black flex items-center justify-center rounded-md flex-shrink-0 mt-0.5">
                                    {idx+1}
                                  </span>
                                  <span className="text-slate-300 text-xs">{p}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {knowledgePkg.faqs && knowledgePkg.faqs.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Frequently Asked Questions (FAQs)</h4>
                            <div className="space-y-3">
                              {knowledgePkg.faqs.map((f: any, idx: number) => (
                                <div key={idx} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-1">
                                  <div className="font-bold text-slate-200 text-xs flex items-center gap-1.5">
                                    <span className="text-indigo-400">Q:</span> {f.q}
                                  </div>
                                  <div className="text-slate-400 text-xs font-medium pl-4">{f.a}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {selectedTab === "story" && (
                      <div className="space-y-6">
                        {knowledgePkg.story_structure && (
                          <div className="space-y-4">
                            <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Story Structure & Outline</h4>
                            <div className="grid grid-cols-1 gap-3">
                              {[
                                { stage: "hook", title: "Hook Intro", color: "border-indigo-800/60 bg-indigo-950/10 text-indigo-200" },
                                { stage: "problem", title: "Problem Definition", color: "border-rose-800/60 bg-rose-950/10 text-rose-200" },
                                { stage: "story", title: "Story / Case Study", color: "border-amber-800/60 bg-amber-950/10 text-amber-200" },
                                { stage: "solution", title: "Solution In Detail", color: "border-emerald-800/60 bg-emerald-950/10 text-emerald-200" },
                                { stage: "cta", title: "Call To Action (CTA)", color: "border-violet-800/60 bg-violet-950/10 text-violet-200" }
                              ].map((step, idx) => {
                                const content = knowledgePkg.story_structure[step.stage] || "";
                                return (
                                  <div key={idx} className={`p-4 rounded-xl border ${step.color} space-y-1`}>
                                    <div className="text-xs font-extrabold uppercase tracking-wider">{step.title}</div>
                                    <p className="text-xs font-medium opacity-90">{content || "No outline draft compiled."}</p>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {knowledgePkg.hooks && knowledgePkg.hooks.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Alternate Hook Variations</h4>
                              <div className="space-y-2">
                                {knowledgePkg.hooks.map((h: string, idx: number) => (
                                  <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg text-xs italic text-slate-300">
                                    "{h}"
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {knowledgePkg.ctas && knowledgePkg.ctas.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Alternate CTAs</h4>
                              <div className="space-y-2">
                                {knowledgePkg.ctas.map((c: string, idx: number) => (
                                  <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg text-xs italic text-slate-300">
                                    "{c}"
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {selectedTab === "visuals" && knowledgePkg.visual_ideas && (
                      <div className="space-y-6">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Visual Research & scene Prompts</h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-4">
                            <div className="space-y-1.5">
                              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Style Reference</span>
                              <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs font-semibold text-slate-200">
                                {knowledgePkg.visual_ideas.style_references?.join(", ") || "Minimal illustrative graphic."}
                              </div>
                            </div>
                            <div className="space-y-1.5">
                              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Color Themes</span>
                              <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs font-semibold text-slate-200">
                                {knowledgePkg.visual_ideas.color_themes?.join(", ") || "Vibrant purple gradients."}
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-1.5">
                                <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Emotion Theme</span>
                                <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs font-bold text-indigo-300">
                                  {knowledgePkg.visual_ideas.emotion || "Inspirational"}
                                </div>
                              </div>
                              <div className="space-y-1.5">
                                <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Camera angles</span>
                                <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs text-slate-300">
                                  {knowledgePkg.visual_ideas.camera_angles?.join(", ") || "Cinematic wide-shot."}
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-4">
                            <div className="space-y-1.5">
                              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Character suggestions</span>
                              <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs text-slate-300">
                                {knowledgePkg.visual_ideas.characters?.join(", ") || "N/A"}
                              </div>
                            </div>
                            <div className="space-y-1.5">
                              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Background Ideas</span>
                              <div className="bg-slate-950/60 border border-slate-800/60 p-3 rounded-lg text-xs text-slate-300">
                                {knowledgePkg.visual_ideas.background_ideas?.join(", ") || "N/A"}
                              </div>
                            </div>
                          </div>
                        </div>

                        {knowledgePkg.visual_ideas.scene_suggestions && (
                          <div className="space-y-2">
                            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Scene suggestions</span>
                            <div className="space-y-2">
                              {knowledgePkg.visual_ideas.scene_suggestions.map((scene: string, idx: number) => (
                                <div key={idx} className="bg-slate-950/40 border border-slate-800/40 p-3 rounded-lg text-xs flex items-center gap-2">
                                  <span className="h-2 w-2 rounded-full bg-violet-400" />
                                  <span>{scene}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {selectedTab === "keywords" && (
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Discovered Target Keywords</h4>
                        <div className="overflow-hidden border border-slate-800/80 rounded-xl bg-slate-950/40">
                          <table className="w-full text-left border-collapse text-xs">
                            <thead>
                              <tr className="border-b border-slate-850 bg-slate-900/60 text-slate-400 font-bold uppercase tracking-wider">
                                <th className="p-3">Keyword</th>
                                <th className="p-3">Est. Search Volume</th>
                                <th className="p-3">SEO Difficulty</th>
                              </tr>
                            </thead>
                            <tbody>
                              {activeJob.keywords?.map((kw: any) => (
                                <tr key={kw.id} className="border-b border-slate-900 hover:bg-slate-900/20 font-medium">
                                  <td className="p-3 text-slate-200">{kw.keyword}</td>
                                  <td className="p-3 text-slate-300">{kw.volume.toLocaleString()} searches/mo</td>
                                  <td className="p-3">
                                    <div className="flex items-center gap-2">
                                      <span className={kw.difficulty > 60 ? 'text-rose-400' : kw.difficulty > 35 ? 'text-amber-400' : 'text-emerald-400'}>
                                        {kw.difficulty}%
                                      </span>
                                      <div className="w-16 bg-slate-900 h-1 rounded-full overflow-hidden">
                                        <div className="bg-violet-500 h-full" style={{ width: `${kw.difficulty}%` }} />
                                      </div>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                              {(!activeJob.keywords || activeJob.keywords.length === 0) && (
                                <tr>
                                  <td colSpan={3} className="p-8 text-center text-slate-500">No keyword stats logged.</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {selectedTab === "competitors" && (
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Competitor analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {activeJob.competitors?.map((c: any) => (
                            <div key={c.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-3">
                              <div>
                                <div className="font-extrabold text-slate-200 text-sm">{c.name}</div>
                                <div className="text-[11px] text-slate-500 mt-0.5">{c.url || 'Social Channel'}</div>
                              </div>
                              <p className="text-slate-400 text-xs font-medium leading-relaxed">{c.summary}</p>
                              <div className="grid grid-cols-2 gap-3 text-xs">
                                <div>
                                  <div className="text-emerald-400 font-bold uppercase tracking-wider text-[10px] mb-1">Strengths</div>
                                  <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                                    {c.strengths?.map((s: string, idx: number) => (
                                      <li key={idx} className="line-clamp-1">{s}</li>
                                    ))}
                                  </ul>
                                </div>
                                <div>
                                  <div className="text-rose-400 font-bold uppercase tracking-wider text-[10px] mb-1">Weaknesses</div>
                                  <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                                    {c.weaknesses?.map((w: string, idx: number) => (
                                      <li key={idx} className="line-clamp-1">{w}</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
                            </div>
                          ))}
                          {(!activeJob.competitors || activeJob.competitors.length === 0) && (
                            <div className="col-span-2 text-center p-8 text-slate-500">No competitor analysis entries logged.</div>
                          )}
                        </div>
                      </div>
                    )}

                    {selectedTab === "sources" && (
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold text-violet-400 uppercase tracking-widest">Discovered Reference Sources</h4>
                        <div className="space-y-3">
                          {activeJob.sources?.map((s: any) => (
                            <div key={s.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl flex flex-col gap-2">
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <div className="font-bold text-slate-200 text-xs">{s.title}</div>
                                  <a 
                                    href={s.url} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    className="text-[11px] text-violet-400 hover:underline flex items-center gap-1.5 mt-0.5"
                                  >
                                    {s.url.substring(0, 70)}...
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                </div>
                                <div className="text-[10px] font-bold uppercase tracking-wider bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-indigo-300 flex-shrink-0">
                                  Relevance: {Math.round(s.relevance_score * 100)}%
                                </div>
                              </div>
                              <p className="text-slate-400 text-xs pl-2 border-l border-slate-850 font-medium">{s.summary}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Search className="h-12 w-12 text-slate-700 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Research Output Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any completed topic research campaign from the history list to view the structured Knowledge Package.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
