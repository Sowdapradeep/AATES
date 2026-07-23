"use client";

import React, { useState, useEffect } from "react";
import {
  Server,
  DollarSign,
  Cpu,
  Layers,
  FileCode,
  Users,
  Compass,
  BookOpen,
  GitBranch,
  ShieldCheck,
  Flame,
  Clock
} from "lucide-react";
import { AgentWorkflowGraph } from "@/components/AgentWorkflowGraph";

export default function DashboardHome() {
  const [activeTab, setActiveTab] = useState("overview");

  const [stats, setStats] = useState({
    activeWorkflows: 3,
    remainingBudget: 100.0,
    dailySpend: 0.0,
    tokenUsage: "Bedrock Nova Pro",
    workersAlive: 1,
    uptime: "99.99%",
    status: "ACTIVE"
  });

  const [universesList, setUniversesList] = useState<any[]>([
    { id: "univ-101", name: "AATES Studio Master Universe", genre: "Action Drama", themes: ["Heritage", "Justice", "Technology"], rulesCount: 2, locationsCount: 3, organizationsCount: 2 }
  ]);

  const [charactersList, setCharactersList] = useState<any[]>([
    { id: "char-01", name: "Kadamban", role: "Protagonist", archetype: "The Heroic Defender", traits: ["resolute", "loyal", "skilled hunter"], motivation: "Protect ancestral forest lands", slang: "Vathalagundu Tamil", type: "hero" },
    { id: "char-02", name: "Nallasamy", role: "Villain", archetype: "The Greedy Corporate Officer", traits: ["manipulative", "ruthless", "polished speaker"], motivation: "Acquire land for mining", slang: "Chennai Corporate Tamil", type: "villain" }
  ]);

  const [activeWorkflowsList, setActiveWorkflowsList] = useState<any[]>([
    { id: "wf-101", name: "Autonomous Episode Production", universe: "AATES Master Universe", status: "Running", progress: 85 },
    { id: "wf-102", name: "Bedrock Nova Continuity Audit", universe: "AATES Master Universe", status: "Running", progress: 95 },
    { id: "wf-103", name: "YouTube Shorts Render & Upload", universe: "AATES Master Universe", status: "Running", progress: 90 }
  ]);

  useEffect(() => {
    // 1. Fetch Real Finance Health
    fetch("http://localhost:8000/v1/finance/health")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.allocated_budget_usd) {
          setStats((prev) => ({
            ...prev,
            remainingBudget: roundVal(data.allocated_budget_usd - data.total_spent_usd),
            dailySpend: roundVal(data.daily_spent_usd),
            status: data.status
          }));
        }
      })
      .catch(() => {});

    // 2. Fetch Real Universes
    fetch("http://localhost:8000/v1/narrative/universes")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.length > 0) {
          const mapped = data.map((u: any) => ({
            id: u.id,
            name: u.name,
            genre: u.genre || "Drama",
            themes: u.core_themes || ["Heritage", "Justice"],
            rulesCount: u.world_rules?.length || 2,
            locationsCount: 3,
            organizationsCount: 2
          }));
          setUniversesList(mapped);

          // Fetch characters for first universe
          fetch(`http://localhost:8000/v1/narrative/universes/${data[0].id}/characters`)
            .then((cRes) => cRes.json())
            .then((cData) => {
              if (cData && cData.length > 0) {
                const cMapped = cData.map((c: any) => ({
                  id: c.id,
                  name: c.name,
                  role: c.role || "Character",
                  archetype: c.archetype || "Key Persona",
                  traits: c.personality_traits || ["Resolute"],
                  motivation: c.motivation || "Story objective",
                  slang: c.slang_preference || "Tamil",
                  type: c.role === "villain" ? "villain" : "hero"
                }));
                setCharactersList(cMapped);
              }
            })
            .catch(() => {});
        }
      })
      .catch(() => {});
  }, []);

  const roundVal = (v: number) => Math.round(v * 100) / 100;

  const councilMembers = [
    { name: "CEO Agent", role: "Executive Queue Orchestrator", status: "Running", version: "1.0.0", mission: "Maximize production throughput while enforcing quality & budget bounds.", kpi: "98% queue compliance" },
    { name: "Creative Director Agent", role: "Lore Continuity Guardian", status: "Running", version: "1.0.0", mission: "Ensure all narrative output matches local Tamil cultural structures.", kpi: "96% tone alignment" },
    { name: "Production Director Agent", role: "Assets Render Lead", status: "Running", version: "1.0.0", mission: "Verify frame blueprints before media production triggers.", kpi: "0.2% frame error rate" },
    { name: "Business Director Agent", role: "Financial Engine Monitor", status: "Running", version: "1.0.0", mission: "Enforce cost limits and token budget caps.", kpi: "$0.02 average cost" }
  ];

  const relationshipsList = [
    { charA: "Kadamban", charB: "Nallasamy", type: "Blood Rivalry", tension: 0.95, description: "Direct ideological clash over forest development vs protection." },
    { charA: "Kadamban", charB: "Elder Farmer", type: "Mentor-Disciple", tension: 0.15, description: "Shared respect and traditional guidance." }
  ];

  const storyArcs = [
    { id: "arc-1", title: "The Warning Signs", theme: "Encroachment of corporate power", climax: "Village council faceoff", status: "Active" },
    { id: "arc-2", title: "The Resistance Begins", theme: "Unifying local farming factions", climax: "Blockade of mining site", status: "Draft" }
  ];

  const conflictsList = [
    { id: "conf-101", parties: "Kadamban vs. Corporate Guards", cause: "Illegal border fencing in deep forest", tension: 0.85, status: "Critical Escalation" },
    { id: "conf-102", parties: "Villagers vs. District Collector", cause: "Biased public hearing proceedings", tension: 0.65, status: "Active Debate" }
  ];

  const timelineBeats = [
    { beat: 1, event: "Survey markers discovered inside native farming lands.", mood: "Tense", clues: "Official blue corporate folder" },
    { beat: 2, event: "Protagonist confronts surveyors, leading to immediate work suspension.", mood: "Confrontational", clues: "Green cotton shirt" },
    { beat: 3, event: "Foreshadowing: Elder tells tale of ancient boundary stones.", mood: "Nostalgic", clues: "Stone scripts" }
  ];

  const validationsList = [
    { scope: "Continuity check: Kadamban wardrobe match", status: "Valid", score: 100.0, details: "Green cotton shirt matches scene 1 settings." },
    { scope: "Canon check: proposed magic elements", status: "Violated", score: 40.0, details: "Proposed levitation script conflicts with local realism world rule." }
  ];

  const decisionsList = [
    { id: "dec-909", actor: "CEO Agent", type: "Episode Queue Scheduling", selected: "Trigger episode production immediately", confidence: 95, constraints: "Allocated budget, deadline", timestamp: "2026-07-15 18:21:59" },
    { id: "dec-908", actor: "Creative Director Agent", type: "Narrative Tone Alignment Check", selected: "Approve screenplay beat", confidence: 92, constraints: "Tamil regional style, Character continuity", timestamp: "2026-07-15 18:22:45" }
  ];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            AATES Creative Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Visualizing dynamic Story Bibles, narrative plot arcs, and regional Tamil dialogue adaptation logic
          </p>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex bg-slate-900/60 p-1 rounded-xl border border-slate-800/80 gap-1 overflow-x-auto">
          {["overview", "universes", "characters", "storylines", "validators", "blueprint", "production", "operations"].map((tab) => (
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

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="space-y-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-violet-500/30">
              <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-violet-600/10 to-transparent rounded-full blur-xl"></div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Workflows</span>
                <Layers className="h-5 w-5 text-violet-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">{stats.activeWorkflows}</span>
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
              </div>
            </div>
          </div>

          {/* Council & Workflows List */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
                <h2 className="text-lg font-semibold mb-4 text-slate-200 flex items-center gap-2">
                  <Users className="h-5 w-5 text-violet-400" /> Executive Council Status
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {councilMembers.map((member, i) => (
                    <div key={i} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold text-slate-100">{member.name}</span>
                        <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 uppercase font-bold border border-emerald-500/20">Running</span>
                      </div>
                      <p className="text-xs text-slate-400">{member.mission}</p>
                      <p className="text-[10px] text-slate-500 font-mono">KPI: {member.kpi}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
                <h2 className="text-lg font-semibold mb-4 text-slate-200">Active Pipelines</h2>
                <div className="space-y-4">
                  {activeWorkflowsList.map((wf) => (
                    <div key={wf.id} className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/60 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-slate-200">{wf.name}</span>
                        <p className="text-[10px] text-slate-500 font-mono">{wf.id}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400">
                        {wf.progress}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* n8n-Style Agent Node & Edge Execution Graph */}
          <AgentWorkflowGraph />
        </div>
      )}



      {/* Universes Explorer Tab */}
      {activeTab === "universes" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <Compass className="h-5 w-5 text-violet-400" /> Universe Explorer
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {universesList.map((u) => (
              <div key={u.id} className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-base font-bold text-slate-200">{u.name}</h3>
                    <p className="text-xs text-violet-400 mt-1">{u.genre}</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{u.id}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {u.themes.map((t: string, idx: number) => (
                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                      #{t}
                    </span>
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs text-slate-400">
                  <div className="p-2 rounded bg-slate-950/40">
                    <span className="block font-bold text-slate-200">{u.rulesCount}</span>
                    Rules
                  </div>
                  <div className="p-2 rounded bg-slate-950/40">
                    <span className="block font-bold text-slate-200">{u.locationsCount}</span>
                    Locations
                  </div>
                  <div className="p-2 rounded bg-slate-950/40">
                    <span className="block font-bold text-slate-200">{u.organizationsCount}</span>
                    Factions
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Characters Explorer Tab */}
      {activeTab === "characters" && (
        <div className="space-y-6">
          {/* Character profiles card */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Users className="h-5 w-5 text-pink-400" /> Character & Villain Profiles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {charactersList.map((char) => (
                <div key={char.id} className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-3 relative">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-base font-bold text-slate-200">{char.name}</h3>
                      <p className="text-[10px] text-violet-400 uppercase font-semibold">{char.archetype}</p>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                      char.type === "hero" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    }`}>
                      {char.role}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400"><strong>Motivation:</strong> {char.motivation}</p>
                  <p className="text-xs text-slate-400"><strong>Tamil Slang:</strong> {char.slang}</p>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {char.traits.map((t: string, idx: number) => (
                      <span key={idx} className="text-[9px] px-2 py-0.5 bg-slate-800 rounded text-slate-300">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Relationship Graph representation */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-violet-400" /> Relationship Graph
            </h2>
            <div className="space-y-4">
              {relationshipsList.map((rel, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3 text-sm font-semibold text-slate-200">
                      <span>{rel.charA}</span>
                      <span className="text-xs px-2 py-0.5 bg-violet-500/10 text-violet-400 rounded-full font-mono border border-violet-500/20">
                        {rel.type}
                      </span>
                      <span>{rel.charB}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{rel.description}</p>
                  </div>
                  <div className="flex items-center gap-2 min-w-[120px]">
                    <span className="text-xs text-slate-400">Tension:</span>
                    <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className={`h-2 ${rel.tension > 0.8 ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${rel.tension * 100}%` }}></div>
                    </div>
                    <span className="text-xs font-mono font-bold">{Math.round(rel.tension * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Storylines & Arcs Tab */}
      {activeTab === "storylines" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Arcs & Conflicts list */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <GitBranch className="h-5 w-5 text-pink-400" /> Story Arcs Viewer
              </h2>
              <div className="space-y-4">
                {storyArcs.map((arc) => (
                  <div key={arc.id} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex justify-between gap-4">
                    <div>
                      <span className="text-sm font-bold text-slate-200">{arc.title}</span>
                      <p className="text-xs text-slate-400 mt-1"><strong>Theme:</strong> {arc.theme}</p>
                      <p className="text-xs text-slate-400"><strong>Climax event:</strong> {arc.climax}</p>
                    </div>
                    <span className="text-xs text-violet-400 font-semibold">{arc.status}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <Flame className="h-5 w-5 text-rose-400" /> Conflict Map
              </h2>
              <div className="space-y-4">
                {conflictsList.map((c) => (
                  <div key={c.id} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex justify-between items-center gap-4">
                    <div>
                      <span className="text-sm font-semibold text-slate-200">{c.parties}</span>
                      <p className="text-xs text-slate-400 mt-0.5"><strong>Cause:</strong> {c.cause}</p>
                    </div>
                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded ${
                      c.status.includes("Critical") ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-yellow-500/10 text-yellow-400"
                    }`}>
                      {c.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Timeline Beats Viewer */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Clock className="h-5 w-5 text-violet-400" /> Timeline Plot Beats
            </h2>
            <div className="relative border-l border-slate-800 pl-4 space-y-6">
              {timelineBeats.map((beat) => (
                <div key={beat.beat} className="relative space-y-1">
                  <div className="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-violet-500"></div>
                  <span className="text-xs font-bold text-violet-400 uppercase">Beat {beat.beat} ({beat.mood})</span>
                  <p className="text-xs text-slate-300">{beat.event}</p>
                  <p className="text-[10px] text-slate-500 font-mono">Foreshadowing: {beat.clues}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Validators & Audits Tab */}
      {activeTab === "validators" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-pink-400" /> Canon & Continuity Validators
              </h2>
              <div className="space-y-4">
                {validationsList.map((val, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 flex justify-between items-center gap-4">
                    <div>
                      <span className="text-sm font-semibold text-slate-200">{val.scope}</span>
                      <p className="text-xs text-slate-400 mt-1">{val.details}</p>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-0.5 text-[9px] font-bold rounded ${
                        val.status === "Valid" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}>
                        {val.status}
                      </span>
                      <p className="text-[10px] text-slate-500 mt-1">{val.score}% Score</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200">Decisions Explainability</h2>
            <div className="space-y-4">
              {decisionsList.map((dec, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-900/30 border border-slate-800/40 space-y-1 text-xs">
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>{dec.timestamp}</span>
                    <span className="font-mono">{dec.id}</span>
                  </div>
                  <p className="text-slate-300"><strong>{dec.type}</strong></p>
                  <p className="text-slate-400">Chosen: {dec.selected}</p>
                  <p className="text-right text-[10px] text-violet-400">By {dec.actor}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Blueprint Tab */}
      {activeTab === "blueprint" && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <FileCode className="h-5 w-5 text-violet-400" /> Standardized Production Blueprint
              </h2>
              <p className="text-xs text-slate-400 mt-1">Consumable package decoupling story creation from media generation</p>
            </div>
            <span className="text-xs font-mono bg-violet-500/10 text-violet-400 border border-violet-500/20 px-3 py-1 rounded-full">
              Episode ID: ep-101
            </span>
          </div>

          <div className="space-y-6">
            <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 block">Location</span>
                  <span className="font-semibold text-slate-200">Village Border Woods</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Time of Day / Weather</span>
                  <span className="font-semibold text-slate-200">DAY / SUNNY</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Lighting Mood</span>
                  <span className="font-semibold text-slate-200">Warm golden natural light</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Camera Intent</span>
                  <span className="font-semibold text-slate-200">Establishing wide slow track</span>
                </div>
              </div>

              <hr className="border-slate-800/60" />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                <div className="space-y-2">
                  <span className="text-violet-400 font-bold block uppercase tracking-wider text-[10px]">Characters & Costumes</span>
                  <ul className="space-y-1 text-slate-300">
                    <li><strong>Kadamban:</strong> Green traditional cotton shirt, rustic dhoti.</li>
                    <li><strong>Nallasamy:</strong> Polished charcoal corporate business suit.</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <span className="text-violet-400 font-bold block uppercase tracking-wider text-[10px]">Audible Elements</span>
                  <ul className="space-y-1 text-slate-300">
                    <li><strong>Music:</strong> Low atmospheric percussion, Tamil flute.</li>
                    <li><strong>SFX:</strong> Forest wind blow, stakes pounding sound.</li>
                  </ul>
                </div>
              </div>

              <hr className="border-slate-800/60" />

              <div className="space-y-2 text-xs">
                <span className="text-pink-400 font-bold block uppercase tracking-wider text-[10px]">Dialogue Line (Tamil Slang Adapted)</span>
                <div className="p-3 rounded bg-slate-950/40 font-mono text-slate-300">
                  <p className="text-slate-200"><strong>Kadamban:</strong> &quot;Idhu enga nilam. Ingu ungaluku velai illai. [MAJA!]&quot;</p>
                  <p className="text-slate-500 mt-1">Delivery note: Quiet indignation, resolute gaze.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Production Tab */}
      {activeTab === "production" && (
        <div className="space-y-8">
          {/* Top Row: Provider cost fees & Render Queue */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                <Cpu className="h-5 w-5 text-violet-400" /> Provider & Costs Monitor
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-xs">
                <div className="p-3 rounded bg-slate-900/40 border border-slate-800/50">
                  <span className="text-slate-500 block">MockImageAI</span>
                  <span className="text-slate-200 font-bold font-mono">$0.03 / Still</span>
                </div>
                <div className="p-3 rounded bg-slate-900/40 border border-slate-800/50">
                  <span className="text-slate-500 block">MockVideoAI</span>
                  <span className="text-slate-200 font-bold font-mono">$0.25 / Clip</span>
                </div>
                <div className="p-3 rounded bg-slate-900/40 border border-slate-800/50">
                  <span className="text-slate-500 block">MockVoiceAI</span>
                  <span className="text-slate-200 font-bold font-mono">$0.05 / Line</span>
                </div>
                <div className="p-3 rounded bg-slate-900/40 border border-slate-800/50">
                  <span className="text-slate-500 block">MockMusicAI</span>
                  <span className="text-slate-200 font-bold font-mono">$0.12 / Track</span>
                </div>
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
              <h2 className="text-lg font-semibold text-slate-200">Rendering Status</h2>
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-emerald-400">Master Reel Compiled</span>
                  <p className="text-[10px] text-slate-500 font-mono">ID: ep-101-reel</p>
                </div>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-2 py-0.5 rounded border border-emerald-500/30">
                  PASS
                </span>
              </div>
            </div>
          </div>

          {/* Storyboard & Shot panels */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-pink-400" /> Storyboard & Shots Planner
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2 text-xs">
                <span className="text-violet-400 font-bold block uppercase tracking-wider text-[10px]">Storyboard Panel 1</span>
                <p className="text-slate-300"><strong>Purpose:</strong> Establishing scene location atmosphere.</p>
                <p className="text-slate-400"><strong>Composition:</strong> Wide screen framing, rule of thirds matching local trees outline.</p>
                <p className="text-slate-500 font-mono">Placement: [Kadamban, Nallasamy]</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2 text-xs">
                <span className="text-violet-400 font-bold block uppercase tracking-wider text-[10px]">Shot Plan Specifications</span>
                <p className="text-slate-300"><strong>Shot ID:</strong> shot_1_1</p>
                <p className="text-slate-400"><strong>Camera Angle:</strong> slow pan-right tracking shot (establishing type)</p>
                <p className="text-slate-500 font-mono">Duration: 5.5s | Transition: FADE</p>
              </div>
            </div>
          </div>

          {/* QA Quality Gates Dashboard */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" /> Automated QA Quality Gates
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex justify-between font-semibold text-slate-200">
                  <span>Character Consistency</span>
                  <span className="text-emerald-400">PASS</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">Costume matches prompt parameters.</p>
              </div>
              <div className="p-3.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex justify-between font-semibold text-slate-200">
                  <span>Audio Speech speed</span>
                  <span className="text-emerald-400">PASS</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">WPS ratio within timing limits.</p>
              </div>
              <div className="p-3.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex justify-between font-semibold text-slate-200">
                  <span>Brand Safety Check</span>
                  <span className="text-emerald-400">PASS</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">No flagged keywords discovered.</p>
              </div>
            </div>
          </div>

          {/* Render Manifest Viewer */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <FileCode className="h-5 w-5 text-violet-400" /> Render Manifest Viewer
            </h2>
            <pre className="p-4 rounded-xl bg-slate-950/60 font-mono text-[10px] text-slate-300 overflow-x-auto max-h-60 scrollbar-thin">
{`{
  "episode_id": "ep-101",
  "universe_id": "univ-101",
  "season": 1,
  "episode": 1,
  "scene_packages": [
    {
      "scene_id": "scene_1",
      "video_asset_id": "s3://aates-assets/videos/clip-9092.mp4",
      "voice_asset_ids": {
        "Kadamban": "s3://aates-assets/audio/voice-3129.mp3"
      },
      "music_asset_id": "s3://aates-assets/audio/theme-1002.mp3",
      "subtitle_asset_id": "s3://aates-assets/subtitles/sub-92cf3.srt",
      "checksums": {
        "video": "sha256-mockvideo-9092",
        "audio": "sha256-mockvoice-3129"
      }
    }
  ],
  "render_settings": {
    "resolution": "1080p",
    "fps": 24
  },
  "version": 1
}`}
            </pre>
          </div>

          {/* Asset Lineage explorer */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200">Asset Lineage Tracking Explorer</h2>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-4 text-xs font-mono">
              <div className="flex flex-col md:flex-row md:items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">Storyboard Frame Still</span>
                <span className="text-slate-600">──►</span>
                <span className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">Animated Video Segment</span>
                <span className="text-slate-600">──►</span>
                <span className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">Mixed Scene Package</span>
                <span className="text-slate-600">──►</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">Master Reel Output (MP4)</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px] text-slate-500 pt-2 border-t border-slate-800">
                <span>Asset ID: asset_master_reel_9019</span>
                <span>Parent Asset ID: asset_scene_package_1002</span>
                <span>Checksum: sha256-mockreel-1022</span>
                <span>Creation time: 2026-07-15 19:35:10</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Operations Tab */}
      {activeTab === "operations" && (
        <div className="space-y-8">
          {/* Operations Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { label: "Active Campaigns", value: "3", icon: "📡", color: "violet" },
              { label: "Queued Publications", value: "12", icon: "📤", color: "blue" },
              { label: "Analytics Snapshots", value: "47", icon: "📊", color: "emerald" },
              { label: "CEO Decisions", value: "8", icon: "🎯", color: "pink" },
            ].map((s) => (
              <div key={s.label} className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-violet-500/30">
                <div className="absolute top-0 right-0 h-24 w-24 bg-gradient-to-br from-violet-600/10 to-transparent rounded-full blur-xl"></div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{s.label}</span>
                  <span className="text-xl">{s.icon}</span>
                </div>
                <div className="text-3xl font-bold text-white">{s.value}</div>
              </div>
            ))}
          </div>

          {/* Campaign Manager */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-violet-400">📡</span> Campaign Manager
            </h3>
            <div className="space-y-3">
              {[
                { name: "Season 1 Launch", status: "active", platforms: ["Instagram Reel", "YouTube Short"], start: "2026-07-16", episodes: 5, priority: "High" },
                { name: "Kadamban Character Intro", status: "draft", platforms: ["Instagram Reel"], start: "2026-07-20", episodes: 3, priority: "Medium" },
                { name: "Finale Event Campaign", status: "draft", platforms: ["Instagram Reel", "YouTube Short"], start: "2026-08-01", episodes: 1, priority: "Critical" },
              ].map((c) => (
                <div key={c.name} className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800 gap-3">
                  <div className="space-y-1">
                    <div className="font-semibold text-white text-sm">{c.name}</div>
                    <div className="flex gap-2 flex-wrap">
                      {c.platforms.map((p) => (
                        <span key={p} className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">{p}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-400">{c.episodes} episodes</span>
                    <span className="text-slate-400">Starts {c.start}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      c.priority === "Critical" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                      c.priority === "High" ? "bg-orange-500/10 text-orange-400 border-orange-500/20" :
                      "bg-slate-700/50 text-slate-400 border-slate-700"
                    }`}>{c.priority}</span>
                    <span className={`px-2 py-1 rounded-full text-[10px] font-bold border ${
                      c.status === "active" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                      "bg-slate-700/50 text-slate-400 border-slate-700"
                    }`}>{c.status.toUpperCase()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Publishing Queue */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-blue-400">📤</span> Publishing Queue
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-800">
                    <th className="text-left py-2 pr-4">Episode</th>
                    <th className="text-left py-2 pr-4">Platform</th>
                    <th className="text-left py-2 pr-4">Status</th>
                    <th className="text-left py-2 pr-4">Scheduled</th>
                    <th className="text-left py-2">Retries</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {[
                    { ep: "S01E01", platform: "Instagram Reel", status: "success", scheduled: "09:00", retries: 0 },
                    { ep: "S01E02", platform: "YouTube Short", status: "queued", scheduled: "09:30", retries: 0 },
                    { ep: "S01E03", platform: "Instagram Reel", status: "queued", scheduled: "10:00", retries: 0 },
                    { ep: "S01E01", platform: "YouTube Short", status: "success", scheduled: "09:00", retries: 0 },
                    { ep: "S01E04", platform: "Instagram Reel", status: "failed", scheduled: "10:30", retries: 2 },
                  ].map((q, i) => (
                    <tr key={i} className="hover:bg-slate-800/20 transition-colors">
                      <td className="py-2 pr-4 font-mono text-slate-300">{q.ep}</td>
                      <td className="py-2 pr-4 text-slate-400">{q.platform}</td>
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          q.status === "success" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                          q.status === "failed" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                          "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        }`}>{q.status}</span>
                      </td>
                      <td className="py-2 pr-4 text-slate-500">{q.scheduled}</td>
                      <td className="py-2 text-slate-500">{q.retries}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Analytics + Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Analytics Snapshots */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-emerald-400">📊</span> Analytics Snapshots
              </h3>
              <div className="space-y-3">
                {[
                  { ep: "S01E01", platform: "Instagram", views: 12500, score: 78.4, trend: "+" },
                  { ep: "S01E01", platform: "YouTube", views: 8200, score: 65.2, trend: "+" },
                  { ep: "S01E02", platform: "Instagram", views: 9100, score: 52.1, trend: "-" },
                ].map((a, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-sm text-white">{a.ep} · {a.platform}</span>
                      <span className={`text-xs font-bold ${a.trend === "+" ? "text-emerald-400" : "text-red-400"}`}>
                        {a.trend} Score: {a.score}
                      </span>
                    </div>
                    <div className="flex gap-4 text-[10px] text-slate-500">
                      <span>Views: {a.views.toLocaleString()}</span>
                    </div>
                    <div className="mt-2 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          a.score >= 70 ? "bg-gradient-to-r from-emerald-500 to-green-400" :
                          a.score >= 50 ? "bg-gradient-to-r from-yellow-500 to-orange-400" :
                          "bg-gradient-to-r from-red-500 to-rose-400"
                        }`}
                        style={{ width: `${a.score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* CEO Recommendations */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-pink-400">🎯</span> CEO Recommendations
              </h3>
              <div className="space-y-3">
                {[
                  { category: "hook", text: "Improve the opening hook within the first 3 seconds.", confidence: 0.90, status: "approved" },
                  { category: "duration", text: "Reduce episode duration by 10-15 seconds.", confidence: 0.85, status: "pending" },
                  { category: "pacing", text: "Increase cut frequency — use faster editing rhythm.", confidence: 0.78, status: "pending" },
                  { category: "character", text: "Introduce a recurring companion character.", confidence: 0.72, status: "rejected" },
                ].map((r, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-violet-400">{r.category}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        r.status === "approved" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        r.status === "rejected" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                        "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                      }`}>{r.status}</span>
                    </div>
                    <p className="text-xs text-slate-300 mb-2">{r.text}</p>
                    <div className="text-[10px] text-slate-500">Confidence: {(r.confidence * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Provider Health Monitor */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-blue-400">🩺</span> Provider Health Monitor
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { provider: "MockInstagramPublisher", platform: "instagram_reel", available: true, latency: 145, success: 99 },
                { provider: "MockYouTubePublisher", platform: "youtube_short", available: true, latency: 230, success: 98 },
              ].map((p) => (
                <div key={p.platform} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="font-semibold text-sm text-white">{p.provider}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{p.platform}</div>
                    </div>
                    <span className={`h-2.5 w-2.5 rounded-full ${p.available ? "bg-emerald-400 shadow-emerald-400/50 shadow-sm" : "bg-red-400"}`} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-2 rounded-lg bg-slate-800/60">
                      <div className="text-slate-500">Latency</div>
                      <div className="text-white font-bold">{p.latency}ms</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-800/60">
                      <div className="text-slate-500">Success Rate</div>
                      <div className="text-emerald-400 font-bold">{p.success}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Operations Timeline */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-slate-400">📋</span> Operations Timeline
            </h3>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {[
                { type: "publish_success", msg: "S01E01 published to Instagram Reel", time: "09:01:23", color: "emerald" },
                { type: "publish_success", msg: "S01E01 published to YouTube Short", time: "09:01:45", color: "emerald" },
                { type: "analytics_snapshot_recorded", msg: "Analytics snapshot recorded for S01E01", time: "10:30:00", color: "blue" },
                { type: "recommendation_generated", msg: "Hook improvement recommendation generated (confidence 90%)", time: "10:30:01", color: "violet" },
                { type: "ceo_decision", msg: "CEO approved: Improve hook sequence to 2 seconds", time: "11:00:00", color: "pink" },
                { type: "publish_success", msg: "S01E02 published to YouTube Short", time: "12:00:00", color: "emerald" },
                { type: "analytics_snapshot_recorded", msg: "Analytics snapshot recorded for S01E02", time: "13:15:00", color: "blue" },
              ].map((e, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                  <span className={`mt-0.5 h-2 w-2 rounded-full flex-shrink-0 ${
                    e.color === "emerald" ? "bg-emerald-400" :
                    e.color === "blue" ? "bg-blue-400" :
                    e.color === "violet" ? "bg-violet-400" :
                    "bg-pink-400"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-slate-300">{e.msg}</div>
                    <div className="text-[10px] text-slate-600 font-mono">{e.type} · {e.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
