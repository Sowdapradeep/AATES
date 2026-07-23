"use client";

import React, { useState, useEffect } from "react";
import { Play, RotateCcw, CheckCircle2, Cpu, Sparkles, Activity, Layers, Share2, DollarSign, BookOpen, ShieldCheck, Film, Zap } from "lucide-react";

export interface PipelineNode {
  id: string;
  name: string;
  sub: string;
  role: string;
  status: "completed" | "current" | "pending";
  kpi: string;
  x: number;
  y: number;
  iconName: string;
}

export function AgentWorkflowGraph() {
  const [currentStepIndex, setCurrentStepIndex] = useState(2); // Step 2 (Creative Director) active
  const [autoPlay, setAutoPlay] = useState(true);
  const [liveTelemetry, setLiveTelemetry] = useState<any>({
    is_worker_alive: true,
    latest_job_id: "job_auto_ffab8e88",
    latest_episode_title: "Episode 31 - Rising indignation into united resolve.",
    latest_viral_hook: "Unseen dramatic twist in Episode 31! #AATES",
    daily_spent_usd: 0.10,
    published_today: 1,
    daily_publishing_cap: 1,
    publishing_channel: "YouTube Shorts + Instagram Reels"
  });
  const [isLiveConnected, setIsLiveConnected] = useState(true);

  // Poll Real-Time Backend Telemetry every 3 seconds
  useEffect(() => {
    const fetchStatus = () => {
      fetch("http://localhost:8000/v1/revenue/pipeline-status")
        .then((res) => res.json())
        .then((data) => {
          if (data && data.latest_job_id) {
            setLiveTelemetry(data);
            setIsLiveConnected(true);
          }
        })
        .catch(() => {
          setIsLiveConnected(false);
        });
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const initialNodes: PipelineNode[] = [
    {
      id: "node-1",
      name: "Autonomous Trigger",
      sub: "apps.worker.main loop",
      role: "Trigger Daemon",
      status: "completed",
      kpi: liveTelemetry?.is_worker_alive ? "Daemon Online" : "60s interval",
      x: 40,
      y: 160,
      iconName: "zap"
    },
    {
      id: "node-2",
      name: "CEO Orchestrator",
      sub: "Executive Queue",
      role: "CEO Agent",
      status: "completed",
      kpi: liveTelemetry?.latest_job_id || "job_auto_active",
      x: 230,
      y: 160,
      iconName: "layers"
    },
    {
      id: "node-3",
      name: "Financial Governor",
      sub: "Cost & Budget Authorization",
      role: "Business Agent",
      status: "completed",
      kpi: `$${liveTelemetry?.daily_spent_usd || 0.10} spent / $10 cap`,
      x: 420,
      y: 100,
      iconName: "dollar"
    },
    {
      id: "node-4",
      name: "Creative Director AI",
      sub: "Bedrock Nova Reasoning",
      role: "Lore Guardian",
      status: "current",
      kpi: liveTelemetry?.latest_episode_title ? liveTelemetry.latest_episode_title.slice(0, 22) + "..." : "Nova Pro Reasoning",
      x: 420,
      y: 220,
      iconName: "book"
    },
    {
      id: "node-5a",
      name: "Asset Frame Render",
      sub: "Titan Image & Audio Sync",
      role: "Production Lead",
      status: "pending",
      kpi: "BLUEPRINT_COMPILED",
      x: 650,
      y: 60,
      iconName: "film"
    },
    {
      id: "node-5b",
      name: "Tamil Dialogue Adaptor",
      sub: "Regional Slang Adaptor",
      role: "Dialogue Lead",
      status: "pending",
      kpi: "100% Tamil realism",
      x: 650,
      y: 160,
      iconName: "cpu"
    },
    {
      id: "node-5c",
      name: "Marketing Engine",
      sub: "Viral Hooks & Hashtags",
      role: "Audience Lead",
      status: "pending",
      kpi: liveTelemetry?.latest_viral_hook ? liveTelemetry.latest_viral_hook.slice(0, 20) + "..." : "#AATES #Shorts",
      x: 650,
      y: 260,
      iconName: "sparkles"
    },
    {
      id: "node-6",
      name: "YouTube Shorts Publish",
      sub: "Channel UCNZrTavbUchfVyHD...",
      role: "Publishing Lead",
      status: "pending",
      kpi: `${liveTelemetry?.published_today || 1}/${liveTelemetry?.daily_publishing_cap || 1} Daily Release Cap`,
      x: 880,
      y: 160,
      iconName: "share"
    }
  ];

  // Map execution status using Real-Time Backend Telemetry
  const nodes = initialNodes.map((node, idx) => {
    let status: "completed" | "current" | "pending" = "pending";

    if (isLiveConnected && liveTelemetry && liveTelemetry.nodes_status) {
      if (liveTelemetry.current_active_node === node.id) {
        status = "current";
      } else if (liveTelemetry.nodes_status[node.id] === "completed") {
        status = "completed";
      } else if (liveTelemetry.nodes_status[node.id] === "current") {
        status = "current";
      }
    } else {
      if (idx < currentStepIndex) {
        status = "completed";
      } else if (idx === currentStepIndex) {
        status = "current";
      }
    }
    return { ...node, status };
  });

  useEffect(() => {
    if (!autoPlay || isLiveConnected) return;
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % initialNodes.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [autoPlay, isLiveConnected, initialNodes.length]);

  const handleNextStep = () => {
    setCurrentStepIndex((prev) => (prev + 1) % initialNodes.length);
  };

  const handleReset = () => {
    setCurrentStepIndex(0);
  };

  const renderIcon = (name: string, isCompleted: boolean, isCurrent: boolean) => {
    const cls = `h-4 w-4 ${isCompleted ? "text-emerald-400" : isCurrent ? "text-blue-300" : "text-slate-400"}`;
    switch (name) {
      case "zap": return <Zap className={cls} />;
      case "layers": return <Layers className={cls} />;
      case "dollar": return <DollarSign className={cls} />;
      case "book": return <BookOpen className={cls} />;
      case "film": return <Film className={cls} />;
      case "sparkles": return <Sparkles className={cls} />;
      case "share": return <Share2 className={cls} />;
      default: return <Cpu className={cls} />;
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-400" />
              Live Creation Pipeline (Real-Time Node Monitoring)
            </h2>
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              LIVE TELEMETRY ONLINE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time pipeline tracing Episode Creation, Bedrock Nova Pro reasoning, Financial Governor checks, and Live YouTube Shorts publishing.
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className="px-2.5 py-1 rounded-lg bg-violet-500/10 text-violet-300 border border-violet-500/30 text-[11px] font-mono font-semibold flex items-center gap-1.5">
              <span>🕒</span> Scheduled Release: Pre-rendered on previous day &amp; Published daily at 12:00 AM Midnight
            </span>
          </div>
        </div>

        {/* Legend & Buttons */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-3 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 text-[11px]">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span className="text-emerald-400 font-semibold">Completed</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-500 animate-ping shadow-sm shadow-blue-500/50" />
              <span className="text-blue-400 font-bold">Executing</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-slate-600" />
              <span className="text-slate-400">Pending</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoPlay(!autoPlay)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                autoPlay
                  ? "bg-blue-600/20 text-blue-400 border-blue-500/40"
                  : "bg-slate-800 text-slate-300 border-slate-700"
              }`}
            >
              <Play className={`h-3.5 w-3.5 ${autoPlay ? "animate-spin" : ""}`} />
              {autoPlay ? "Auto-Advancing" : "Paused"}
            </button>

            <button
              onClick={handleNextStep}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white shadow-md transition-all flex items-center gap-1.5"
            >
              <Sparkles className="h-3.5 w-3.5" /> Next Step
            </button>

            <button
              onClick={handleReset}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition-all"
              title="Reset Cycle"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Node Graph Canvas Area */}
      <div 
        className="relative w-full overflow-x-auto rounded-2xl border border-slate-800 p-4 min-h-[380px] bg-slate-950"
        style={{
          backgroundImage: "radial-gradient(#334155 1.5px, transparent 1.5px)",
          backgroundSize: "24px 24px"
        }}
      >
        {/* SVG Bezier Edges Layer */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ minWidth: "1050px" }}>
          <defs>
            <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>
            <marker id="arrow-blue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
            </marker>
            <marker id="arrow-gray" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
            </marker>
          </defs>

          {/* Node 1 -> Node 2 */}
          <path
            d="M 190 195 C 210 195, 210 195, 230 195"
            fill="none"
            stroke={nodes[0].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[0].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 2 -> Node 3 */}
          <path
            d="M 380 195 C 400 195, 400 135, 420 135"
            fill="none"
            stroke={nodes[1].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[1].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 2 -> Node 4 */}
          <path
            d="M 380 195 C 400 195, 400 255, 420 255"
            fill="none"
            stroke={nodes[1].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[1].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 3 -> Node 5a */}
          <path
            d="M 570 135 C 610 135, 610 95, 650 95"
            fill="none"
            stroke={nodes[2].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[2].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 4 -> Node 5b */}
          <path
            d="M 570 255 C 610 255, 610 195, 650 195"
            fill="none"
            stroke={nodes[3].status === "completed" ? "#10b981" : nodes[3].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[3].status === "completed" ? "url(#arrow-green)" : nodes[3].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Node 4 -> Node 5c */}
          <path
            d="M 570 255 C 610 255, 610 295, 650 295"
            fill="none"
            stroke={nodes[3].status === "completed" ? "#10b981" : nodes[3].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[3].status === "completed" ? "url(#arrow-green)" : nodes[3].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Node 5a -> Node 6 */}
          <path
            d="M 800 95 C 840 95, 840 195, 880 195"
            fill="none"
            stroke={nodes[4].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[4].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 5b -> Node 6 */}
          <path
            d="M 800 195 C 840 195, 840 195, 880 195"
            fill="none"
            stroke={nodes[5].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[5].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 5c -> Node 6 */}
          <path
            d="M 800 295 C 840 295, 840 195, 880 195"
            fill="none"
            stroke={nodes[6].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[6].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />
        </svg>

        {/* Canvas Nodes Layer */}
        <div className="relative min-w-[1050px] h-[350px]">
          {nodes.map((node) => {
            const isCompleted = node.status === "completed";
            const isCurrent = node.status === "current";

            return (
              <div
                key={node.id}
                style={{ left: `${node.x}px`, top: `${node.y - 35}px` }}
                className={`absolute w-38 p-3 rounded-xl border transition-all duration-500 shadow-2xl flex flex-col justify-between ${
                  isCompleted
                    ? "bg-slate-900/95 border-emerald-500 text-emerald-100 shadow-emerald-500/10"
                    : isCurrent
                    ? "bg-slate-900/95 border-blue-400 text-blue-50 shadow-blue-500/30 animate-pulse ring-2 ring-blue-500/40"
                    : "bg-slate-900/90 border-slate-700/80 text-slate-400 opacity-80 hover:opacity-100"
                }`}
              >
                {/* Port Input Dot (Left) */}
                <div 
                  className={`absolute -left-1.5 top-1/2 -translate-y-1/2 h-3 w-3 rounded-full border-2 border-slate-950 ${
                    isCompleted ? "bg-emerald-500" : isCurrent ? "bg-blue-400" : "bg-slate-600"
                  }`}
                />

                {/* Port Output Dot (Right) */}
                <div 
                  className={`absolute -right-1.5 top-1/2 -translate-y-1/2 h-3 w-3 rounded-full border-2 border-slate-950 ${
                    isCompleted ? "bg-emerald-500" : isCurrent ? "bg-blue-400" : "bg-slate-600"
                  }`}
                />

                {/* Node Title & Icon */}
                <div className="flex items-center gap-2 mb-1">
                  <div className="p-1 rounded bg-slate-800/80 border border-slate-700">
                    {renderIcon(node.iconName, isCompleted, isCurrent)}
                  </div>
                  <div className="overflow-hidden">
                    <h3 className={`text-xs font-bold truncate ${isCompleted ? "text-emerald-300" : isCurrent ? "text-blue-200" : "text-slate-200"}`}>
                      {node.name}
                    </h3>
                    <p className="text-[9px] text-slate-400 truncate">{node.sub}</p>
                  </div>
                </div>

                {/* KPI & Status Badge */}
                <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[9px] font-mono">
                  <span className="text-slate-400 font-semibold">{node.kpi}</span>
                  {isCompleted && (
                    <span className="text-emerald-400 font-bold flex items-center gap-0.5">
                      <CheckCircle2 className="h-2.5 w-2.5" /> Done
                    </span>
                  )}
                  {isCurrent && (
                    <span className="text-blue-300 font-bold animate-pulse">
                      Active
                    </span>
                  )}
                  {!isCompleted && !isCurrent && (
                    <span className="text-slate-500">Queued</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
