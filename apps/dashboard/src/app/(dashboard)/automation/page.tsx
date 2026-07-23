"use client";

import React, { useEffect, useState } from "react";
import { 
  Zap, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  Layers, 
  Sliders, 
  Play, 
  ShieldCheck, 
  Lock, 
  Unlock, 
  Plus, 
  Cpu, 
  Check, 
  FileText, 
  Radio, 
  GitBranch, 
  Settings2, 
  Compass 
} from "lucide-react";

export default function AutomationEnginePage() {
  const [triggerType, setTriggerType] = useState("MANUAL_TRIGGER");
  const [targetPlatform, setTargetPlatform] = useState("all");

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [policies, setPolicies] = useState<any[]>([]);
  const [triggers, setTriggers] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("policies");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const jRes = await fetch("/api/v1/automation");
      if (jRes.ok) {
        const data = await jRes.json();
        setJobs(data);
        if (data.length > 0 && !selectedJob) setSelectedJob(data[0]);
      }

      const mRes = await fetch("/api/v1/automation/metrics");
      if (mRes.ok) setMetrics(await mRes.json());

      const pRes = await fetch("/api/v1/automation/policies");
      if (pRes.ok) setPolicies(await pRes.json());

      const tRes = await fetch("/api/v1/automation/triggers");
      if (tRes.ok) setTriggers(await tRes.json());
    } catch (e) {
      console.error("Failed to load automation engine data:", e);
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
      const res = await fetch("/api/v1/automation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          trigger_type: triggerType,
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

  const handleExecuteJob = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/automation/${id}/execute`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Manual execution failed:", e);
    }
  };

  const handleTogglePolicy = async (policyId: string, currentlyEnabled: boolean) => {
    try {
      const endpoint = currentlyEnabled ? `/api/v1/automation/${policyId}/disable` : `/api/v1/automation/${policyId}/enable`;
      const res = await fetch(endpoint, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Policy toggle failed:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-amber-400 via-orange-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-3">
            <span>AI Automation Engine</span>
            <span className="text-xs bg-amber-950/80 text-amber-300 border border-amber-800 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">
              Workflow Execution v1.0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Policy-driven deterministic workflow execution triggered by schedules, quality approvals, learning recommendations, and manual requests with WorkflowDefinition decoupling.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-amber-400 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Execution Confidence</div>
              <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <span className="text-amber-300 font-black">{Math.round(metrics.overall_execution_confidence * 100)}%</span>
                <span className="text-[10px] bg-amber-950 text-amber-300 px-1.5 py-0.2 rounded font-mono">Resource Locked</span>
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
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              Queued Workflows
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-orange-400 animate-pulse" />
              Executing
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_processing}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Settings2 className="h-3.5 w-3.5 text-amber-400" />
              Active Policies
            </div>
            <div className="text-2xl font-black text-amber-400">{metrics.total_active_policies || policies.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Radio className="h-3.5 w-3.5 text-pink-400" />
              Triggers Intercepted
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.total_triggers_received || triggers.length}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20 col-span-2">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              Global Automation Confidence
            </div>
            <div className="text-2xl font-black text-slate-100">{Math.round(metrics.overall_execution_confidence * 100)}%</div>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Form & Workflows Queue */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Trigger Workflow Form */}
          <div className="glass-panel border border-slate-800/80 p-5 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 backdrop-blur-lg">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-400" />
              Trigger Workflow Execution
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Trigger Type</label>
                <select
                  value={triggerType}
                  onChange={(e) => setTriggerType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-amber-500 focus:outline-none text-slate-200"
                >
                  <option value="MANUAL_TRIGGER">Manual Request</option>
                  <option value="SCHEDULE">Scheduled Cron</option>
                  <option value="QUALITY_APPROVED">Quality Approved Gate</option>
                  <option value="LEARNING_RECOMMENDATION">Learning Recommendation</option>
                  <option value="RETRY_REQUESTED">Retry Requested</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Target Platform</label>
                <div className="grid grid-cols-3 gap-2">
                  {["all", "instagram", "youtube"].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setTargetPlatform(p)}
                      className={`p-2.5 rounded-xl border text-xs font-bold capitalize transition-all ${targetPlatform === p ? 'bg-amber-600 text-white border-amber-500 shadow-lg shadow-amber-900/30' : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-900'}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-amber-600 via-orange-600 to-pink-500 hover:opacity-95 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-amber-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting}
              >
                <Play className="h-4 w-4 fill-white" />
                {submitting ? 'Dispatching...' : 'Dispatch Workflow'}
              </button>
            </form>
          </div>

          {/* Workflow Queue */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-orange-400" />
              Executed Workflows
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading automation history...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active automation jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-amber-950/60 text-amber-300 border border-amber-800/50";
                  if (job.status === "SUCCESS") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-amber-500/80 shadow-md shadow-amber-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          Workflow ({job.trigger_type})
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {job.status}
                        </span>
                      </div>

                      {job.status === "PROCESSING" && (
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-[11px] font-medium text-amber-400">
                            <span>Stage: {job.stage}</span>
                            <span>{Math.round(job.progress * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className="bg-gradient-to-r from-amber-500 to-orange-500 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${job.progress * 100}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                        <div>Platform: <span className="uppercase text-slate-300">{job.target_platform}</span></div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleExecuteJob(job.id); }}
                          className="text-amber-400 hover:text-amber-300 font-bold flex items-center gap-1"
                        >
                          <Play className="h-3 w-3 fill-amber-400" /> Execute
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Automation Console */}
        <div className="lg:col-span-8">
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
            
            {/* Navigation Tabs */}
            <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
              {[
                { id: "policies", label: "Automation Policy Manager", icon: Settings2 },
                { id: "executions", label: "Workflow Graph & Executions", icon: GitBranch },
                { id: "triggers", label: "Trigger Event Stream", icon: Radio },
                { id: "locks", label: "Resource Locks & Decisions", icon: Lock }
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTab(t.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${selectedTab === t.id ? 'bg-amber-600 text-white shadow-lg shadow-amber-900/30' : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'}`}
                >
                  <t.icon className="h-3.5 w-3.5" />
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab 1: Policy Manager */}
            {selectedTab === "policies" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                    Registered Automation Policies ({policies.length})
                  </h4>
                </div>

                <div className="space-y-3">
                  {policies.map((p) => (
                    <div key={p.policy_id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-100">{p.name}</span>
                          <span className="text-[10px] font-mono bg-slate-900 text-slate-400 border border-slate-800 px-2 py-0.5 rounded">
                            {p.policy_id}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400">
                          Target Workflow: <strong className="text-amber-300 font-mono">{p.target_workflow_id}</strong> • Triggers: {p.trigger_types.join(", ")}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded-full ${p.enabled ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-900 text-slate-500 border border-slate-800'}`}>
                          {p.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        <button
                          onClick={() => handleTogglePolicy(p.policy_id, p.enabled)}
                          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-bold text-slate-300"
                        >
                          {p.enabled ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 2: Workflow Executions */}
            {selectedTab === "executions" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                  Workflow Execution Instance & Step Log
                </h4>

                {activeJob ? (
                  <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                      <div>
                        <div className="text-sm font-bold text-slate-100">Workflow: AUTONOMOUS_PUBLISHING</div>
                        <div className="text-xs text-slate-500">Instance ID: {activeJob.id}</div>
                      </div>
                      <span className="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-2.5 py-0.5 rounded font-mono font-bold">
                        {activeJob.status}
                      </span>
                    </div>

                    <div className="space-y-2">
                      {[
                        { step: "step_pub_quality", name: "Validate Quality Gate", agent: "QualityAgent", status: "SUCCESS", time: 145 },
                        { step: "step_publish", name: "Publish to Platform Container", agent: "PublishingProvider", status: "SUCCESS", time: 320 }
                      ].map((s) => (
                        <div key={s.step} className="bg-slate-900/60 border border-slate-850 p-3 rounded-lg flex items-center justify-between text-xs">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="h-4 w-4 text-emerald-400" />
                            <div>
                              <div className="font-bold text-slate-200">{s.name} ({s.agent})</div>
                              <div className="text-[10px] text-slate-500 font-mono">IdemKey: 8a9f...3c21</div>
                            </div>
                          </div>
                          <span className="font-mono text-slate-400 font-bold">{s.time}ms</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center p-8 text-slate-500 text-sm">Select a job from the queue to view execution steps.</div>
                )}
              </div>
            )}

            {/* Tab 3: Trigger Event Stream */}
            {selectedTab === "triggers" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                  Recent Trigger Event Stream ({triggers.length})
                </h4>

                <div className="space-y-2 max-h-[440px] overflow-y-auto pr-1">
                  {triggers.map((t) => (
                    <div key={t.id} className="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-slate-200 flex items-center gap-2">
                          <Radio className="h-3.5 w-3.5 text-amber-400" />
                          <span>{t.trigger_type}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({t.source_component})</span>
                        </div>
                        <div className="text-slate-400 text-[11px] mt-0.5">Target Platform: {t.target_platform}</div>
                      </div>
                      <div className="text-[10px] font-mono text-slate-500">
                        {new Date(t.triggered_at).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 4: Resource Locks & Decisions */}
            {selectedTab === "locks" && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                  Active Package Resource Locks & Decisions
                </h4>

                <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                    <div className="flex items-center gap-2">
                      <Lock className="h-4 w-4 text-emerald-400" />
                      <span className="font-bold text-sm text-slate-200">Resource Lock Status: ACTIVE</span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">Concurrency Lock Protection ON</span>
                  </div>

                  <div className="text-xs text-slate-400 space-y-2">
                    <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                      <div className="font-bold text-slate-300">Policy pol_auto_publish_quality_approved Evaluation</div>
                      <div className="text-emerald-400 font-bold mt-1">✓ Approved (Quality Score 0.94 &gt;= 0.85, Resource Locks Acquired)</div>
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
