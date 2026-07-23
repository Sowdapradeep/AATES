"use client";

import React, { useState } from "react";
import { TrendingUp, Play, CheckCircle2, Loader2, DollarSign } from "lucide-react";

export default function RevenueEnginePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const triggerCycle = async () => {
    setLoading(true);
    setResult(null);

    // Fetch master universe ID first
    try {
      const uRes = await fetch("http://localhost:8000/v1/narrative/universes");
      const uData = await uRes.json();
      const uId = uData && uData.length > 0 ? uData[0].id : "00000000-0000-0000-0000-000000000000";

      const res = await fetch("http://localhost:8000/v1/revenue/execute-cycle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          universe_id: uId,
          season: 1,
          episode: 1,
          objective_prompt: "Autonomous production cycle trigger from dashboard"
        })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ status: "error", message: "Failed to connect to API server." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <TrendingUp className="h-7 w-7 text-violet-500" />
            Autonomous Revenue Engine
          </h1>
          <p className="text-sm text-slate-400">
            End-to-End Orchestration: Reasoning -&gt; Financial Governance -&gt; Rendering -&gt; Marketing -&gt; YouTube/Instagram Publishing -&gt; ROI Monetization.
          </p>
        </div>

        <button
          onClick={triggerCycle}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white font-medium rounded-xl shadow-lg shadow-violet-500/25 transition-all disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Play className="h-5 w-5 fill-current" />
          )}
          Trigger Autonomous Cycle
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Production Mode</span>
          <div className="text-xl font-bold text-emerald-400 mt-1">100% Autonomous</div>
          <span className="text-xs text-slate-500">Worker Daemon Running</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Target Channels</span>
          <div className="text-xl font-bold text-white mt-1">YouTube & Instagram Reels</div>
          <span className="text-xs text-slate-500">Automated Short-Form Distribution</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Monetization Model</span>
          <div className="text-xl font-bold text-amber-400 mt-1">Ad Sense + CPM Strategy</div>
          <span className="text-xs text-slate-500">Real-Time ROI Tracking</span>
        </div>
      </div>

      {result && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-lg">
            <CheckCircle2 className="h-6 w-6" />
            Autonomous Cycle Completed
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 font-mono text-sm text-slate-300 space-y-2">
            <div><span className="text-slate-500">Job ID:</span> {result.job_id}</div>
            <div><span className="text-slate-500">Title:</span> {result.title}</div>
            <div><span className="text-slate-500">Blueprint Status:</span> {result.blueprint_status}</div>
            <div><span className="text-slate-500">Viral Hook:</span> {result.viral_hook}</div>
            <div><span className="text-slate-500">Hashtags:</span> {result.hashtags?.join(" ")}</div>
            <div><span className="text-slate-500">Provider Used:</span> {result.financial_summary?.provider_used}</div>
            <div><span className="text-slate-500">Production Cost:</span> ${result.financial_summary?.cost_usd}</div>
          </div>
        </div>
      )}
    </div>
  );
}
