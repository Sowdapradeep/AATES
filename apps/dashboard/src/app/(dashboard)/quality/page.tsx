"use client";

import React, { useEffect, useState } from "react";
import { 
  ShieldCheck, 
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
  Award,
  Zap,
  Target,
  LayoutGrid,
  TrendingUp,
  FileCheck,
  AlertCircle,
  HelpCircle,
  Plus,
  RotateCcw
} from "lucide-react";

export default function QualityPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [imageList, setImageList] = useState<any[]>([]);
  const [voiceList, setVoiceList] = useState<any[]>([]);
  const [videoList, setVideoList] = useState<any[]>([]);
  const [subtitleList, setSubtitleList] = useState<any[]>([]);
  const [musicList, setMusicList] = useState<any[]>([]);
  const [thumbnailList, setThumbnailList] = useState<any[]>([]);
  const [policyList, setPolicyList] = useState<any[]>([]);

  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedImageId, setSelectedImageId] = useState("");
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [selectedSubtitleId, setSelectedSubtitleId] = useState("");
  const [selectedMusicId, setSelectedMusicId] = useState("");
  const [selectedThumbnailId, setSelectedThumbnailId] = useState("");
  const [selectedPolicyId, setSelectedPolicyId] = useState("");

  const [provider, setProvider] = useState("policy_engine");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("overview");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const scriptRes = await fetch("/api/v1/scripts");
      if (scriptRes.ok) setScriptList((await scriptRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const imageRes = await fetch("/api/v1/images");
      if (imageRes.ok) setImageList((await imageRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const voiceRes = await fetch("/api/v1/voices");
      if (voiceRes.ok) setVoiceList((await voiceRes.json()).filter((j: any) => j.status === "SUCCESS"));
      
      const videoRes = await fetch("/api/v1/videos");
      if (videoRes.ok) setVideoList((await videoRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const subtitleRes = await fetch("/api/v1/subtitles");
      if (subtitleRes.ok) setSubtitleList((await subtitleRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const musicRes = await fetch("/api/v1/music");
      if (musicRes.ok) setMusicList((await musicRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const thumbRes = await fetch("/api/v1/thumbnails");
      if (thumbRes.ok) setThumbnailList((await thumbRes.json()).filter((j: any) => j.status === "SUCCESS"));

      const polRes = await fetch("/api/v1/quality/policies");
      if (polRes.ok) setPolicyList(await polRes.json());

      const jobsRes = await fetch("/api/v1/quality");
      if (jobsRes.ok) setJobs(await jobsRes.json());

      const metricsRes = await fetch("/api/v1/quality/metrics");
      if (metricsRes.ok) setMetrics(await metricsRes.json());
    } catch (e) {
      console.error("Failed to load quality assets:", e);
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
    if (!selectedScriptId || !selectedImageId || !selectedVoiceId || !selectedVideoId) return;
    setSubmitting(true);
    try {
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const imageJob = imageList.find(j => j.id === selectedImageId);
      const voiceJob = voiceList.find(j => j.id === selectedVoiceId);
      const videoJob = videoList.find(j => j.id === selectedVideoId);
      const subtitleJob = subtitleList.find(j => j.id === selectedSubtitleId);
      const musicJob = musicList.find(j => j.id === selectedMusicId);
      const thumbJob = thumbnailList.find(j => j.id === selectedThumbnailId);

      const res = await fetch("/api/v1/quality", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptJob.packages[0].id,
          image_package_id: imageJob.packages[0].id,
          voice_package_id: voiceJob.packages[0].id,
          video_package_id: videoJob.packages[0].id, 
          subtitle_package_id: subtitleJob?.packages?.[0]?.id || null,
          music_package_id: musicJob?.packages?.[0]?.id || null,
          thumbnail_package_id: thumbJob?.packages?.[0]?.id || null,
          quality_policy_id: selectedPolicyId || null,
          provider,
          priority 
        })
      });
      if (res.ok) {
        setSelectedScriptId("");
        setSelectedImageId("");
        setSelectedVoiceId("");
        setSelectedVideoId("");
        setSelectedSubtitleId("");
        setSelectedMusicId("");
        setSelectedThumbnailId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReevaluate = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/quality/${id}/re-evaluate`, { method: "POST" });
      if (res.ok) fetchData();
    } catch (e) {
      console.error("Re-evaluation failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/quality/${id}`, { method: "DELETE" });
      if (selectedJob?.id === id) setSelectedJob(null);
      fetchData();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const activeJob = selectedJob ? jobs.find(j => j.id === selectedJob.id) || selectedJob : null;
  const activePkg = activeJob?.packages?.[0] || null;

  const filteredIssues = activePkg?.issues?.filter((iss: any) => {
    if (severityFilter === "ALL") return true;
    return iss.severity === severityFilter;
  }) || [];

  return (
    <div className="space-y-8 p-6 bg-[#030307] min-h-screen text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
            AI Quality Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Central governance layer executing versioned QualityPolicy profiles, Cross-Package Consistency Matrix checks, and evidence-backed publishing approval.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Governance Daemon</div>
              <div className="text-sm font-bold text-slate-200">
                {metrics.worker_is_running ? `Active (${metrics.current_worker_count} auditor threads)` : 'Offline'}
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
              <Award className="h-3.5 w-3.5 text-cyan-400" />
              Publishing Approval Rate
            </div>
            <div className="text-2xl font-black text-slate-200">{Math.round(metrics.approval_rate * 100)}%</div>
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
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              Evaluate Package Graph
            </h2>
            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">1. Script Package</label>
                <select
                  value={selectedScriptId}
                  onChange={(e) => setSelectedScriptId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-emerald-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Script --</option>
                  {scriptList.map((j) => (
                    <option key={j.id} value={j.id}>{j.packages?.[0]?.title || `Script ${j.id.slice(0,6)}`}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">2. Image</label>
                  <select
                    value={selectedImageId}
                    onChange={(e) => setSelectedImageId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-emerald-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="">-- Image --</option>
                    {imageList.map((j) => (
                      <option key={j.id} value={j.id}>Images ({j.packages?.[0]?.resolution})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">3. Voice</label>
                  <select
                    value={selectedVoiceId}
                    onChange={(e) => setSelectedVoiceId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-emerald-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="">-- Voice --</option>
                    {voiceList.map((j) => (
                      <option key={j.id} value={j.id}>Voice ({j.packages?.[0]?.language})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">4. Video Package</label>
                <select
                  value={selectedVideoId}
                  onChange={(e) => setSelectedVideoId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-emerald-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Video Package --</option>
                  {videoList.map((j) => (
                    <option key={j.id} value={j.id}>Video {j.packages?.[0]?.platform} ({j.packages?.[0]?.resolution})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Subtitle</label>
                  <select
                    value={selectedSubtitleId}
                    onChange={(e) => setSelectedSubtitleId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-lg p-2 text-xs focus:border-emerald-500 text-slate-200"
                  >
                    <option value="">-- Opt --</option>
                    {subtitleList.map((j) => (
                      <option key={j.id} value={j.id}>Sub</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Music</label>
                  <select
                    value={selectedMusicId}
                    onChange={(e) => setSelectedMusicId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-lg p-2 text-xs focus:border-emerald-500 text-slate-200"
                  >
                    <option value="">-- Opt --</option>
                    {musicList.map((j) => (
                      <option key={j.id} value={j.id}>Music</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Thumbnail</label>
                  <select
                    value={selectedThumbnailId}
                    onChange={(e) => setSelectedThumbnailId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-lg p-2 text-xs focus:border-emerald-500 text-slate-200"
                  >
                    <option value="">-- Opt --</option>
                    {thumbnailList.map((j) => (
                      <option key={j.id} value={j.id}>Thumb</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">5. Quality Policy Profile</label>
                <select
                  value={selectedPolicyId}
                  onChange={(e) => setSelectedPolicyId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 text-xs focus:border-emerald-500 focus:outline-none text-slate-200"
                >
                  <option value="">-- Default Platform Policy --</option>
                  {policyList.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.platform})</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedScriptId || !selectedImageId || !selectedVoiceId || !selectedVideoId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Auditing Graph...' : 'Execute Governance Audit'}
              </button>
            </form>
          </div>

          {/* History Queue List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-teal-400" />
              Audit Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading governance records...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active quality jobs found.
              </div>
            ) : (
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  const pkg = job.packages?.[0];
                  let statusBg = "bg-slate-800 text-slate-400";
                  if (job.status === "PROCESSING") statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "SUCCESS" && pkg?.is_approved_for_publishing) statusBg = "bg-emerald-950/60 text-emerald-300 border border-emerald-800/50";
                  if (job.status === "SUCCESS" && !pkg?.is_approved_for_publishing) statusBg = "bg-amber-950/60 text-amber-300 border border-amber-800/50";
                  if (job.status === "FAILED") statusBg = "bg-rose-950/60 text-rose-300 border border-rose-800/50";

                  return (
                    <div
                      key={job.id}
                      onClick={() => setSelectedJob(job)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2.5 hover:bg-slate-900/60 ${isSelected ? 'bg-slate-900/90 border-emerald-500/80 shadow-md shadow-emerald-900/10' : 'bg-slate-950/40 border-slate-800/60'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-sm text-slate-200 line-clamp-1">
                          {pkg ? `Quality Package v${pkg.version} (Score: ${pkg.production_readiness_score})` : `Quality Audit: ${job.provider}`}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${statusBg}`}>
                          {pkg ? (pkg.is_approved_for_publishing ? 'Approved' : 'Flagged') : job.status}
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
                          <span>Lifecycle: {pkg?.publishing_lifecycle_state || 'Draft'}</span>
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

        {/* Right Column: Quality Governance Console */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-widest">
                    Governance Quality Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                    {activePkg ? (
                      <>
                        <span>Production Readiness: {activePkg.production_readiness_score}</span>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${activePkg.is_approved_for_publishing ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}`}>
                          {activePkg.is_approved_for_publishing ? 'Approved for Publishing' : 'Draft Rejected'}
                        </span>
                      </>
                    ) : (
                      `Draft: ${activeJob.provider}`
                    )}
                  </h3>
                </div>

                {activePkg && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReevaluate(activeJob.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-900/20"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      Re-Evaluate Policy
                    </button>
                  </div>
                )}
              </div>

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">

                  {/* Nav Tabs */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "overview", label: "Readiness & Matrix Checks", icon: LayoutGrid },
                      { id: "dimensions", label: "QualityDimensions Breakdown", icon: Sliders },
                      { id: "issues", label: `Issues (${activePkg.issues?.length || 0})`, icon: AlertTriangle },
                      { id: "policy", label: "QualityPolicy Profile", icon: FileCheck }
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

                  {/* Tab 1: Cross-Package Consistency Matrix */}
                  {selectedTab === "overview" && (
                    <div className="space-y-6">
                      
                      {/* Gauge & Summary */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex flex-col justify-between">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Lifecycle State</div>
                          <div className="text-2xl font-black text-emerald-400 mt-2">{activePkg.publishing_lifecycle_state}</div>
                          <div className="text-[10px] text-slate-500 mt-1">Ready for automated publisher dispatch</div>
                        </div>

                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex flex-col justify-between">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Critical Issues</div>
                          <div className={`text-2xl font-black mt-2 ${activePkg.critical_issue_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {activePkg.critical_issue_count}
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1">Zero critical issues required</div>
                        </div>

                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex flex-col justify-between">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Major / Minor Issues</div>
                          <div className="text-2xl font-black text-amber-400 mt-2">
                            {activePkg.major_issue_count} Major / {activePkg.minor_issue_count} Minor
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1">Auto-remediation available</div>
                        </div>
                      </div>

                      {/* Cross-Package Consistency Matrix Table */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Cross-Package Consistency Matrix</h4>
                        <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden text-xs">
                          <table className="w-full text-left border-collapse">
                            <thead>
                              <tr className="border-b border-slate-850 bg-slate-900/60 text-slate-400 font-bold uppercase text-[10px] tracking-wider">
                                <th className="p-3">Package Interface</th>
                                <th className="p-3">Dimension</th>
                                <th className="p-3">Check Rule Name</th>
                                <th className="p-3">Evaluated Value</th>
                                <th className="p-3">Status</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-900 text-slate-300 font-medium">
                              {activePkg.checks?.map((chk: any) => (
                                <tr key={chk.id} className="hover:bg-slate-900/40">
                                  <td className="p-3 font-bold text-slate-200">{chk.package_type}</td>
                                  <td className="p-3 text-slate-400">{chk.dimension}</td>
                                  <td className="p-3">{chk.check_name}</td>
                                  <td className="p-3 font-mono text-[11px] text-emerald-400">{chk.evaluated_value}</td>
                                  <td className="p-3">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${chk.status === 'PASSED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}`}>
                                      {chk.status}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                    </div>
                  )}

                  {/* Tab 2: QualityDimensions Breakdown */}
                  {selectedTab === "dimensions" && activePkg.dimension_scores && (
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">QualityDimensions Weighted Breakdown</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(activePkg.dimension_scores).map(([dim, score]: [string, any]) => (
                          <div key={dim} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                            <div className="flex justify-between items-center text-xs font-bold">
                              <span className="text-slate-200">{dim} Dimension</span>
                              <span className="text-emerald-400">{score * 100}%</span>
                            </div>
                            <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                              <div 
                                className="bg-gradient-to-r from-emerald-500 to-teal-500 h-full rounded-full" 
                                style={{ width: `${score * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Issues, Evidence & Recommendations Drawer */}
                  {selectedTab === "issues" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          {["ALL", "CRITICAL", "MAJOR", "MINOR"].map(sev => (
                            <button
                              key={sev}
                              onClick={() => setSeverityFilter(sev)}
                              className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${severityFilter === sev ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-slate-200'}`}
                            >
                              {sev}
                            </button>
                          ))}
                        </div>
                      </div>

                      {filteredIssues.length > 0 ? (
                        <div className="space-y-3">
                          {filteredIssues.map((iss: any) => (
                            <div key={iss.id} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-3">
                              <div className="flex justify-between items-start">
                                <div>
                                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${iss.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border-rose-800' : 'bg-amber-950 text-amber-300 border-amber-800'}`}>
                                    {iss.severity} • {iss.issue_code}
                                  </span>
                                  <h5 className="text-sm font-bold text-slate-200 mt-2">{iss.description}</h5>
                                </div>
                                <span className="text-[10px] text-slate-500 font-bold">Target: {iss.impacted_component}</span>
                              </div>

                              {iss.remediation_suggestion && (
                                <div className="text-xs bg-slate-900/60 border border-slate-850 p-2.5 rounded-lg text-slate-300">
                                  <strong className="text-emerald-400">Remediation Hint:</strong> {iss.remediation_suggestion}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                          No quality issues found matching filter criteria.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tab 4: QualityPolicy Profile */}
                  {selectedTab === "policy" && activeJob.policy && (
                    <div className="bg-slate-950 border border-slate-800 p-5 rounded-xl space-y-4 text-xs">
                      <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Active Policy Profile: {activeJob.policy.name}</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Platform</div>
                          <div className="text-slate-200 font-bold text-sm">{activeJob.policy.platform}</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Policy Version</div>
                          <div className="text-slate-200 font-bold text-sm">{activeJob.policy.policy_version}</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Rule Set Version</div>
                          <div className="text-slate-200 font-bold text-sm">{activeJob.policy.rule_set_version}</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-850">
                          <div className="text-[10px] text-slate-500 font-bold uppercase">Min Readiness Score</div>
                          <div className="text-emerald-400 font-bold text-sm">{activeJob.policy.min_readiness_score * 100}%</div>
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <ShieldCheck className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Governance Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active quality job from the left queue to view cross-package matrix checks, QualityDimension scores, and evidence-backed publishing approval.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
