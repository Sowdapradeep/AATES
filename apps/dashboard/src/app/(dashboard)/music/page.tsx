"use client";

import React, { useEffect, useState } from "react";
import { 
  Music, 
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
  Volume2,
  VolumeX,
  Play,
  Pause,
  Plus,
  Zap,
  Radio,
  Activity as Waveform
} from "lucide-react";

export default function MusicPage() {
  const [scriptList, setScriptList] = useState<any[]>([]);
  const [voiceList, setVoiceList] = useState<any[]>([]);
  const [videoList, setVideoList] = useState<any[]>([]);
  const [subtitleList, setSubtitleList] = useState<any[]>([]);

  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [selectedSubtitleId, setSelectedSubtitleId] = useState("");
  const [provider, setProvider] = useState("library");
  const [priority, setPriority] = useState(0);

  const [jobs, setJobs] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState("cues");
  const [diffVersionId, setDiffVersionId] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const scriptRes = await fetch("/api/v1/scripts");
      if (scriptRes.ok) {
        const data = await scriptRes.json();
        setScriptList(data.filter((j: any) => j.status === "SUCCESS"));
      }

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

      const subtitleRes = await fetch("/api/v1/subtitles");
      if (subtitleRes.ok) {
        const data = await subtitleRes.json();
        setSubtitleList(data.filter((j: any) => j.status === "SUCCESS"));
      }

      const jobsRes = await fetch("/api/v1/music");
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data);
      }

      const metricsRes = await fetch("/api/v1/music/metrics");
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to load music assets:", e);
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
    if (!selectedScriptId || !selectedVoiceId || !selectedVideoId) return;
    setSubmitting(true);
    try {
      const scriptJob = scriptList.find(j => j.id === selectedScriptId);
      const voiceJob = voiceList.find(j => j.id === selectedVoiceId);
      const videoJob = videoList.find(j => j.id === selectedVideoId);
      const subtitleJob = subtitleList.find(j => j.id === selectedSubtitleId);

      const res = await fetch("/api/v1/music", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          script_package_id: scriptJob.packages[0].id,
          voice_package_id: voiceJob.packages[0].id, 
          video_package_id: videoJob.packages[0].id,
          subtitle_package_id: subtitleJob?.packages?.[0]?.id || null,
          provider,
          priority 
        })
      });
      if (res.ok) {
        setSelectedScriptId("");
        setSelectedVoiceId("");
        setSelectedVideoId("");
        setSelectedSubtitleId("");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemix = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/music/${id}/remix?music_volume_db=-14.0&ducking_level_db=-12.0`, {
        method: "POST"
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Remix failed:", e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/music/${id}`, { method: "DELETE" });
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
          <h1 className="font-extrabold text-3xl leading-tight bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent">
            AI Music Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Intelligently maps music cues, performs scene-aware narration ducking, applies LUFS loudness normalization (-14 LUFS), and exports master audio stems.
          </p>
        </div>
        {metrics && (
          <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 px-4 backdrop-blur-md">
            <div className={`h-2.5 w-2.5 rounded-full ${metrics.worker_is_running ? 'bg-amber-500 animate-pulse' : 'bg-rose-500'}`} />
            <div>
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Music Worker Daemon</div>
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
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              Queued
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.jobs_queued}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800/60 bg-slate-900/20">
            <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-orange-400 animate-pulse" />
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
              <RefreshCw className="h-3.5 w-3.5 text-amber-400 animate-spin" style={{ animationDuration: '6s' }} />
              Avg Mix Speed
            </div>
            <div className="text-2xl font-black text-slate-200">{metrics.average_duration_sec}s</div>
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
              <Sparkles className="h-5 w-5 text-amber-400" />
              Mix Background Audio
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">1. Script Package</label>
                <select
                  value={selectedScriptId}
                  onChange={(e) => setSelectedScriptId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Completed Script --</option>
                  {scriptList.map((j) => (
                    <option key={j.id} value={j.id}>{j.packages?.[0]?.title || `Script ${j.id.slice(0,6)}`}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">2. Voice Package</label>
                <select
                  value={selectedVoiceId}
                  onChange={(e) => setSelectedVoiceId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Voice Package --</option>
                  {voiceList.map((j) => (
                    <option key={j.id} value={j.id}>Voice ({j.language}) - {j.packages?.[0]?.speaking_style}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">3. Video Package</label>
                <select
                  value={selectedVideoId}
                  onChange={(e) => setSelectedVideoId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- Select Video Package --</option>
                  {videoList.map((j) => (
                    <option key={j.id} value={j.id}>Video {j.packages?.[0]?.platform} ({j.packages?.[0]?.resolution})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">4. Subtitle Package (Optional)</label>
                <select
                  value={selectedSubtitleId}
                  onChange={(e) => setSelectedSubtitleId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
                  disabled={submitting}
                >
                  <option value="">-- None (Optional) --</option>
                  {subtitleList.map((j) => (
                    <option key={j.id} value={j.id}>Subtitles ({j.language}) - {j.packages?.[0]?.caption_style}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
                    disabled={submitting}
                  >
                    <option value="library">Local Licensed Library</option>
                    <option value="mock">Mock Engine</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-sm focus:border-amber-500 focus:outline-none text-slate-200"
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
                className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 font-semibold rounded-xl p-3 text-sm flex items-center justify-center gap-2 shadow-lg shadow-amber-900/20 active:scale-[0.98] transition-all disabled:opacity-50 text-white"
                disabled={submitting || !selectedScriptId || !selectedVoiceId || !selectedVideoId}
              >
                <Plus className="h-4 w-4" />
                {submitting ? 'Enqueuing...' : 'Mix Audio Track'}
              </button>
            </form>
          </div>

          {/* History Queue List */}
          <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/20 p-5 space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="h-5 w-5 text-orange-400" />
              Music Jobs Queue
            </h2>
            
            {loading && jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm">Loading music indexes...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center p-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                No active music jobs found.
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
                          {job.packages?.[0] ? `Package v${job.packages[0].version} (${job.provider})` : `Music job: ${job.provider}`}
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
                        <div className="flex items-center gap-1.5">
                          <span>Provider: {job.provider}</span>
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

        {/* Right Column: Audio Console & Waveforms */}
        <div className="lg:col-span-8">
          {activeJob ? (
            <div className="glass-panel border border-slate-800/80 rounded-2xl bg-slate-900/10 p-6 flex flex-col gap-6 min-h-[580px]">
              
              {/* Header Info */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
                <div>
                  <div className="text-[11px] font-bold text-amber-400 uppercase tracking-widest">
                    AI Music Package (v{activePkg?.version || 1})
                  </div>
                  <h3 className="text-xl font-bold text-slate-100">
                    {activePkg ? `Master Audio Mix: ${(activePkg.duration_ms / 1000).toFixed(1)}s` : `Draft: ${activeJob.provider}`}
                  </h3>
                </div>

                {activePkg && (
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => handleRemix(activeJob.id)}
                      className="bg-amber-600 hover:bg-amber-700 text-white p-2 px-3 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-amber-900/20"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Remix Audio
                    </button>
                  </div>
                )}
              </div>

              {activeJob.status === "SUCCESS" && activePkg && (
                <div className="flex flex-col gap-6">

                  {/* Audio Waveform & Player Console */}
                  <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Radio className="h-5 w-5 text-amber-400 animate-pulse" />
                        <span className="font-bold text-sm text-slate-200">Master Mix Waveform & Stems</span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
                        Target: {activePkg.telemetry_metadata?.integrated_lufs || -14.0} LUFS | Peak: {activePkg.telemetry_metadata?.peak_level || -1.0} dBFS
                      </div>
                    </div>

                    {/* Simulated Waveform Visualization */}
                    <div className="h-20 bg-slate-900/80 rounded-xl border border-slate-850 p-2 flex items-center gap-1 overflow-hidden relative">
                      {Array.from({ length: 48 }).map((_, idx) => {
                        const heights = [30, 45, 70, 90, 60, 40, 85, 95, 50, 35, 80, 65, 40, 75, 90, 55, 30, 60];
                        const h = heights[idx % heights.length];
                        return (
                          <div 
                            key={idx} 
                            className="flex-1 bg-gradient-to-t from-amber-500 to-orange-400 rounded-sm opacity-85 hover:opacity-100 transition-all cursor-pointer"
                            style={{ height: `${h}%` }}
                          />
                        );
                      })}
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <audio controls className="w-full h-10 accent-amber-500">
                        <source src={`/api/v1/music/${activeJob.id}/preview`} type="audio/mpeg" />
                        Your browser does not support audio playback.
                      </audio>
                    </div>
                  </div>

                  {/* Tabs Nav */}
                  <div className="flex overflow-x-auto gap-1.5 border-b border-slate-800 pb-2">
                    {[
                      { id: "cues", label: "Music Cues & Scenes", icon: Music },
                      { id: "automation", label: "Ducking & Mix Envelope", icon: Volume2 },
                      { id: "analysis", label: "LUFS Loudness Analysis", icon: Sliders },
                      { id: "compare", label: "Version Lineage", icon: GitCompare }
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

                  {/* Tab 1: Music Cues */}
                  {selectedTab === "cues" && (
                    <div className="space-y-4">
                      {activePkg.scene_musics?.map((sc: any) => (
                        <div key={sc.id} className="bg-slate-950/60 border border-slate-800/60 p-4 rounded-xl space-y-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-bold text-sm text-slate-200">
                                Scene {sc.scene_number}: {sc.track_name}
                              </div>
                              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mt-0.5">
                                <span>Genre: {sc.genre}</span>
                                <span>•</span>
                                <span>Mood: {sc.mood}</span>
                                <span>•</span>
                                <span>BPM: {sc.tempo_bpm}</span>
                              </div>
                            </div>
                            <div className="text-xs font-bold text-amber-400 bg-amber-950/40 px-2.5 py-1 rounded border border-amber-900/40">
                              Vol: {sc.music_volume_db} dB | Ducking: {sc.narration_ducking_db} dB
                            </div>
                          </div>

                          {/* MusicCues derived */}
                          {sc.cues && sc.cues.length > 0 && (
                            <div className="grid grid-cols-1 gap-2 pt-1">
                              {sc.cues.map((cue: any) => (
                                <div key={cue.id} className="bg-slate-900/80 border border-slate-800 p-3 rounded-lg flex items-center justify-between text-xs">
                                  <div>
                                    <span className="font-bold text-slate-200">{cue.cue_name}</span>
                                    <span className="text-[10px] text-slate-400 uppercase tracking-wider ml-2 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                                      Purpose: {cue.cue_purpose}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-slate-400 font-mono">
                                    Crossfade: {cue.crossfade_recommendation}ms | Emotion Score: {cue.emotion_score}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Ducking Automation Envelope */}
                  {selectedTab === "automation" && (
                    <div className="bg-slate-950/40 border border-slate-850 p-5 rounded-xl space-y-4">
                      <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">Narration Ducking Volume Automation Envelope</h4>
                      
                      <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                        <div className="flex justify-between text-xs text-slate-400 font-semibold">
                          <span>0ms (Intro -14dB)</span>
                          <span className="text-amber-400">Speech Active (-26dB Ducking)</span>
                          <span>Outro (-14dB)</span>
                        </div>
                        <div className="h-12 bg-slate-900 rounded-lg border border-slate-800 relative flex items-center px-4">
                          <div className="w-full bg-slate-800 h-1 rounded-full relative">
                            <div className="absolute left-10 right-10 top-0 bottom-0 bg-amber-500 rounded-full h-1 animate-pulse" />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-xs font-medium">
                        <div className="bg-slate-900/40 border border-slate-800 p-3 rounded-lg">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Attack Time</div>
                          <div className="text-slate-200 font-bold">100 ms</div>
                        </div>
                        <div className="bg-slate-900/40 border border-slate-800 p-3 rounded-lg">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Release Time</div>
                          <div className="text-slate-200 font-bold">300 ms</div>
                        </div>
                        <div className="bg-slate-900/40 border border-slate-800 p-3 rounded-lg">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Ducking Level</div>
                          <div className="text-slate-200 font-bold">-12.0 dB</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: LUFS Loudness Analysis */}
                  {selectedTab === "analysis" && activePkg.analysis && (
                    <div className="bg-slate-950/40 border border-slate-850 p-5 rounded-xl space-y-4">
                      <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">Integrated Audio Loudness Analysis</h4>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Integrated LUFS</div>
                          <div className="text-slate-200 font-bold">{activePkg.analysis.lufs} LUFS</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">True Peak</div>
                          <div className="text-slate-200 font-bold">{activePkg.analysis.peak_db} dBFS</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Dynamic Range (LRA)</div>
                          <div className="text-slate-200 font-bold">{activePkg.analysis.dynamic_range_db} dB</div>
                        </div>
                        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">RMS Power</div>
                          <div className="text-slate-200 font-bold">{activePkg.analysis.rms_db} dB</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 4: Version Lineages */}
                  {selectedTab === "compare" && (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-amber-400 uppercase tracking-widest">Music Package version lineage</h4>
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
                          <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                            Snapshot Assets List (v{diffVersion.version} - Action: {diffVersion.lineage_action})
                          </div>
                          <div className="grid grid-cols-1 gap-3">
                            {diffVersion.assets_snapshot?.map((snap: any, idx: number) => (
                              <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
                                <div className="font-bold text-slate-200 mb-1">Scene {snap.scene_number}: {snap.track_name}</div>
                                <div className="text-slate-400 font-mono text-[10px]">Genre: {snap.genre} | Mood: {snap.mood} | Vol: {snap.music_volume_db} dB</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center p-12 text-slate-500 border border-dashed border-slate-850 rounded-xl">
                          Select a historical Music package version from the dropdown to compare snapshots.
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel border border-slate-800/85 rounded-2xl bg-slate-900/10 p-6 flex flex-col items-center justify-center text-center min-h-[580px] gap-4">
              <Music className="h-12 w-12 text-slate-750 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-slate-300 text-lg">AI Music Audio Console</h3>
                <p className="text-slate-500 text-sm max-w-sm mt-1">
                  Select any active music job from the left queue to view waveforms, inspect ducking automation graphs, and download master audio stems.
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
