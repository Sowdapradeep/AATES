"use client";

import React, { useEffect, useState } from "react";
import { DollarSign, ShieldAlert, PieChart, ArrowUpRight } from "lucide-react";

export default function FinancialGovernorPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/v1/finance/health")
      .then((res) => res.json())
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <DollarSign className="h-7 w-7 text-emerald-500" />
            Financial & Production Budget Governor
          </h1>
          <p className="text-sm text-slate-400">
            Real-time API expense authorization, daily spend ceilings, and automated cost degradation guardrails.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Ledger Health</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1 uppercase">
            {health ? health.status : "ACTIVE"}
          </div>
          <span className="text-xs text-slate-500">Master Studio Budget</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Allocated Budget</span>
          <div className="text-2xl font-bold text-white mt-1">
            ${health ? health.allocated_budget_usd.toFixed(2) : "100.00"}
          </div>
          <span className="text-xs text-slate-500">Total Capital Ceiling</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Daily Spent</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            ${health ? health.daily_spent_usd.toFixed(2) : "0.00"}
          </div>
          <span className="text-xs text-slate-500">Max Limit: ${health ? health.daily_limit_usd.toFixed(2) : "10.00"}</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <span className="text-sm text-slate-400">Episode Cap</span>
          <div className="text-2xl font-bold text-violet-400 mt-1">
            ${health ? health.episode_limit_usd.toFixed(2) : "1.50"}
          </div>
          <span className="text-xs text-slate-500">Per-Episode Spend Limit</span>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-400" />
          Autonomous Budget Guardrails
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          When daily or per-episode spend limits are approached, the Governor automatically degrades API calls to zero-cost fallback providers (e.g. Pollinations / Groq), preventing financial loss.
        </p>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-white">Active Policy</div>
            <div className="text-xs text-slate-400">AWS Bedrock Nova Pro + Pollinations Zero-Cost Fallback</div>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-full border border-emerald-500/20">
            ENFORCED
          </span>
        </div>
      </div>
    </div>
  );
}
