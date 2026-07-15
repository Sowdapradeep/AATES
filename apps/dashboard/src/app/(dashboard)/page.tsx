"use client";

import React, { useState } from "react";
import {
  Server,
  DollarSign,
  Cpu,
  Database,
  Layers,
  ArrowUpRight,
  TrendingUp,
  FileCode
} from "lucide-react";

export default function DashboardHome() {
  const [stats] = useState({
    activeWorkflows: 3,
    remainingBudget: 120.45,
    dailySpend: 1.22,
    tokenUsage: "412K",
    workersAlive: 2,
    uptime: "99.98%"
  });

  const activeWorkflowsList = [
    { id: "wf-101", name: "Story Planning Cycle", universe: "Kadamban", status: "Running", progress: 65 },
    { id: "wf-102", name: "Storyboard Render Stage 2", universe: "Kadamban", status: "Running", progress: 40 },
    { id: "wf-103", name: "Audio Track Sync Pipeline", universe: "Ponniyin V2", status: "Suspended", progress: 85 }
  ];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
          AATES System Control Center
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Operational control dashboard for AI-powered autonomous Tamil cinema universes creation
        </p>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-violet-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-violet-600/10 to-transparent rounded-full blur-xl"></div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Workflows</span>
            <Layers className="h-5 w-5 text-violet-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{stats.activeWorkflows}</span>
            <span className="text-xs text-emerald-400 flex items-center gap-0.5">
              <TrendingUp className="h-3 w-3" /> +10%
            </span>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-pink-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-pink-600/10 to-transparent rounded-full blur-xl"></div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Remaining Budget</span>
            <DollarSign className="h-5 w-5 text-pink-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">${stats.remainingBudget}</span>
            <span className="text-xs text-slate-500">of $150.00</span>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-violet-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-violet-600/10 to-transparent rounded-full blur-xl"></div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Daily cost usage</span>
            <Server className="h-5 w-5 text-violet-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">${stats.dailySpend}</span>
            <span className="text-xs text-emerald-400 flex items-center gap-0.5">
              <ArrowUpRight className="h-3 w-3" /> 0.8%
            </span>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-pink-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-pink-600/10 to-transparent rounded-full blur-xl"></div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">API Tokens Billed</span>
            <FileCode className="h-5 w-5 text-pink-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{stats.tokenUsage}</span>
            <span className="text-xs text-slate-400">tokens</span>
          </div>
        </div>
      </div>

      {/* Main Grid Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Workflow List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
            <h2 className="text-lg font-semibold mb-4 text-slate-200">Active Workflow Executions</h2>
            <div className="space-y-4">
              {activeWorkflowsList.map((wf) => (
                <div key={wf.id} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100">{wf.name}</span>
                      <span className="text-xs font-mono text-slate-500">{wf.id}</span>
                    </div>
                    <span className="text-xs text-slate-400">Universe: {wf.universe}</span>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Progress Bar */}
                    <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-gradient-to-r from-violet-500 to-pink-500 h-1.5" style={{ width: `${wf.progress}%` }}></div>
                    </div>
                    <span className="text-xs font-semibold text-slate-300">{wf.progress}%</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      wf.status === "Running" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                    }`}>
                      {wf.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Resource Health Status */}
        <div className="space-y-6">
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
            <h2 className="text-lg font-semibold mb-4 text-slate-200">Infrastructure Health</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-violet-400" />
                  <span className="text-sm font-medium text-slate-300">FastAPI API Instance</span>
                </div>
                <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Online</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-pink-400" />
                  <span className="text-sm font-medium text-slate-300">PostgreSQL DB Pool</span>
                </div>
                <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-violet-400" />
                  <span className="text-sm font-medium text-slate-300">Redis Cache Queue</span>
                </div>
                <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
              </div>
            </div>

            <hr className="my-6 border-slate-800/60" />

            <div className="space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Workers online</span>
                <span className="font-semibold">{stats.workersAlive}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">System Uptime</span>
                <span className="font-semibold">{stats.uptime}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
