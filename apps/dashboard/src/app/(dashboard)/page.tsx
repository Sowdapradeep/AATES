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
  FileCode,
  Users,
  Compass,
  BookOpen,
  ClipboardList,
  Eye,
  Settings
} from "lucide-react";

export default function DashboardHome() {
  const [activeTab, setActiveTab] = useState("overview");

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

  const councilMembers = [
    { name: "CEO Agent", role: "Executive Queue Orchestrator", status: "Running", version: "1.0.0", mission: "Maximize production throughput while enforcing quality & budget bounds.", scope: "Global planning, release schedules.", kpi: "98% queue compliance" },
    { name: "Creative Director Agent", role: "Lore Continuity Guardian", status: "Running", version: "1.0.0", mission: "Ensure all narrative output matches the cultural slang and universe Story Bible rules.", scope: "Story, characters, dialogue.", kpi: "96% tone alignment" },
    { name: "Production Director Agent", role: "Assets Render Pipeline Lead", status: "Running", version: "1.0.0", mission: "Convert screenplay blueprints to structured scene render layouts.", scope: "Universe scene plans.", kpi: "0.2% frame error rate" },
    { name: "Business Director Agent", role: "Financial Engine Monitor", status: "Running", version: "1.0.0", mission: "Inspect model API usage and token expenditures.", scope: "Billing limits, cost bounds.", kpi: "$0.02 average cost per query" },
    { name: "Technology Director Agent", role: "Provider Telemetry Analyst", status: "Running", version: "1.0.0", mission: "Monitor external model latency and load balance traffic.", scope: "Provider APIs routing, runtime DI.", kpi: "115ms average latency" },
    { name: "Analytics Director Agent", role: "Audience Trends Analyzer", status: "Running", version: "1.0.0", mission: "Optimize episode release targets based on community feedback signals.", scope: "Publish scheduling, engagement reviews.", kpi: "88% publish optimization score" }
  ];

  const decisionsList = [
    { id: "dec-909", actor: "CEO Agent", type: "Episode Queue Scheduling", selected: "Trigger episode production immediately", confidence: 95, constraints: "Allocated budget, deadline", timestamp: "2026-07-15 18:21:59" },
    { id: "dec-908", actor: "Creative Director Agent", type: "Narrative Tone Alignment Check", selected: "Approve screenplay beat", confidence: 92, constraints: "Tamil regional style, Character continuity", timestamp: "2026-07-15 18:22:45" },
    { id: "dec-907", actor: "Technology Director Agent", type: "Provider Endpoint Selection", selected: "Route to Gemini Flash 1.5", confidence: 91, constraints: "Latency tolerance limits", timestamp: "2026-07-15 18:23:12" }
  ];

  const storyBible = {
    universe: "Kadamban",
    version: 4,
    rules: [
      "Realism must prioritize local Tamil cultural structures.",
      "Character continuity is absolute; lore states are frozen after release."
    ],
    characters: [
      { name: "Kadamban", role: "Protagonist", attributes: "Noble, defender of the land, village coordinator" },
      { name: "Nallasamy", role: "Antagonist", attributes: "Corporate land manager, greedy, cunning" }
    ],
    history: [
      { id: "chg-01", author: "Creative Director Agent", action: "Characters section add 'Kadamban'", reason: "Establish lore core protagonist", timestamp: "2026-07-15 18:05:12" }
    ]
  };

  const planningBoard = {
    universe: "Formulates themes, world rules, and long-term directions.",
    season: "Structures conflicts, character development arcs, and episode lists.",
    episode: "Defines episode script outlines, scene goals, and narrative paces.",
    scene: "Coordinates emotional goals, constraints, participating characters, and outcome beats."
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            AATES System Control Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Operational control dashboard for AI-powered autonomous Tamil cinema universes creation
          </p>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex bg-slate-900/60 p-1 rounded-xl border border-slate-800/80 gap-1 overflow-x-auto">
          {["overview", "council", "bible", "decisions", "planning", "memory"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === tab
                  ? "bg-gradient-to-r from-violet-600 to-pink-600 text-white shadow-lg"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Main Sections based on Active Tab */}
      {activeTab === "overview" && (
        <div className="space-y-8">
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

          {/* Table list */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
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
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Executive Council Tab */}
      {activeTab === "council" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Users className="h-5 w-5 text-violet-400" /> Executive Council Members
            </h2>
            <p className="text-xs text-slate-400 mt-1">Autonomous council agents executing in runtime wrappers</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {councilMembers.map((member, i) => (
              <div key={i} className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-bold text-slate-100">{member.name}</span>
                    <p className="text-[10px] text-violet-400 uppercase tracking-wider">{member.role}</p>
                  </div>
                  <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase font-bold">
                    {member.status}
                  </span>
                </div>
                <div className="space-y-2 text-xs text-slate-400">
                  <p><strong>Mission:</strong> {member.mission}</p>
                  <p><strong>Scope:</strong> {member.scope}</p>
                  <p><strong>KPI:</strong> {member.kpi}</p>
                </div>
                <div className="text-[10px] text-slate-500 font-mono text-right">v{member.version}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Story Bible Tab */}
      {activeTab === "bible" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-pink-400" /> Story Bible Rules ({storyBible.universe})
              </h2>
              <div className="space-y-3">
                {storyBible.rules.map((rule, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/60 text-sm text-slate-300">
                    {rule}
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200">Character Registry</h2>
              <div className="space-y-4">
                {storyBible.characters.map((char, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex justify-between gap-4">
                    <div>
                      <span className="text-sm font-bold text-slate-200">{char.name}</span>
                      <p className="text-xs text-slate-400 mt-1">{char.attributes}</p>
                    </div>
                    <span className="text-xs text-violet-400 font-semibold uppercase">{char.role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200">Auditable Change Logs</h2>
            <div className="space-y-3">
              {storyBible.history.map((hist, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-900/30 border border-slate-800/40 space-y-2 text-xs">
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>{hist.timestamp}</span>
                    <span className="font-mono">v{storyBible.version}</span>
                  </div>
                  <p className="text-slate-300"><strong>Action:</strong> {hist.action}</p>
                  <p className="text-slate-400"><strong>Reason:</strong> {hist.reason}</p>
                  <p className="text-right text-[10px] text-violet-400">By {hist.author}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Decision Logs Tab */}
      {activeTab === "decisions" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-violet-400" /> Explainability Decision Audits
            </h2>
            <p className="text-xs text-slate-400 mt-1">Audit logs record for autonomous council operations</p>
          </div>

          <div className="space-y-4">
            {decisionsList.map((dec, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex justify-between items-start gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-200">{dec.type}</span>
                    <span className="text-[10px] font-mono text-slate-500">{dec.id}</span>
                  </div>
                  <p className="text-xs text-slate-400"><strong>Actor:</strong> {dec.actor}</p>
                  <p className="text-xs text-slate-300"><strong>Outcome Chosen:</strong> {dec.selected}</p>
                  <p className="text-[11px] text-slate-500"><strong>Constraints:</strong> {dec.constraints}</p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-emerald-400">{dec.confidence}% Confidence</span>
                  <p className="text-[10px] text-slate-500 mt-1">{dec.timestamp}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Planning Board Tab */}
      {activeTab === "planning" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <Compass className="h-5 w-5 text-pink-400" /> Planning Board Hierarchy
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold text-violet-400 uppercase">1. Universe Planner</span>
              <p className="text-sm text-slate-300">{planningBoard.universe}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold text-violet-400 uppercase">2. Season Planner</span>
              <p className="text-sm text-slate-300">{planningBoard.season}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold text-violet-400 uppercase">3. Episode Planner</span>
              <p className="text-sm text-slate-300">{planningBoard.episode}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold text-violet-400 uppercase">4. Scene Planner</span>
              <p className="text-sm text-slate-300">{planningBoard.scene}</p>
            </div>
          </div>
        </div>
      )}

      {/* Memory Explorer Tab */}
      {activeTab === "memory" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <Database className="h-5 w-5 text-violet-400" /> Memory Explorer
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold uppercase text-violet-400">Working Memory</span>
              <p className="text-xs text-slate-400">Context-specific, active session parameters stored locally in thread variables.</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold uppercase text-violet-400">Long-Term Memory</span>
              <p className="text-xs text-slate-400">Lore rules and character relationships parsed from permanent databases.</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
              <span className="text-xs font-bold uppercase text-violet-400">Episodic Memory</span>
              <p className="text-xs text-slate-400">History record log of generated scripts, scene structures, and completed screenplays.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
