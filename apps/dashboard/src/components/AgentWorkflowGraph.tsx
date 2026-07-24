"use client";

import React, { useState, useEffect } from "react";
import { Play, RotateCcw, CheckCircle2, Cpu, Sparkles, Activity, Layers, Share2, DollarSign, BookOpen, ShieldCheck, Film, Zap, Search, Music, Image, Volume2, FileText, Video, Instagram, Brain } from "lucide-react";

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
      fetch("/api/v1/revenue/pipeline-status")
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
      name: "Automation Agent",
      sub: "AI Policy Scheduler",
      role: "Trigger Daemon",
      status: "completed",
      kpi: liveTelemetry?.is_worker_alive ? "Daemon Online" : "60s interval",
      x: 40,
      y: 180,
      iconName: "zap"
    },
    {
      id: "node-2",
      name: "CEO Orchestrator",
      sub: "Cognitive Event Bus",
      role: "CEO Agent",
      status: "completed",
      kpi: liveTelemetry?.latest_job_id || "job_auto_active",
      x: 220,
      y: 180,
      iconName: "layers"
    },
    {
      id: "node-3",
      name: "Financial Governor",
      sub: "Cost & Budget Auth",
      role: "Business Agent",
      status: "completed",
      kpi: `$${liveTelemetry?.daily_spent_usd || 0.10} spent / $10 cap`,
      x: 400,
      y: 100,
      iconName: "dollar"
    },
    {
      id: "node-4",
      name: "Creative Director",
      sub: "Bedrock Nova Reasoning",
      role: "Lore Guardian",
      status: "current",
      kpi: liveTelemetry?.latest_episode_title ? liveTelemetry.latest_episode_title.slice(0, 18) + "..." : "Nova Pro Reasoning",
      x: 400,
      y: 260,
      iconName: "book"
    },
    {
      id: "node-prep-1",
      name: "Research Agent",
      sub: "Market & Topic Research",
      role: "Trend Analyst",
      status: "pending",
      kpi: "Trends Evaluated",
      x: 580,
      y: 180,
      iconName: "search"
    },
    {
      id: "node-prep-2",
      name: "Script Agent",
      sub: "Tamil Screenplay Writer",
      role: "Creative Writer",
      status: "pending",
      kpi: "Screenplay Outlined",
      x: 760,
      y: 180,
      iconName: "filetext"
    },
    {
      id: "node-gen-1",
      name: "Image Agent",
      sub: "Stable Image Generation",
      role: "Visual Lead",
      status: "pending",
      kpi: "Scene Frames Done",
      x: 940,
      y: 60,
      iconName: "image"
    },
    {
      id: "node-gen-2",
      name: "Voice Agent",
      sub: "Dialogue Speech Synthesis",
      role: "Voice Actor",
      status: "pending",
      kpi: "TTS Audios Ready",
      x: 940,
      y: 180,
      iconName: "volume2"
    },
    {
      id: "node-gen-3",
      name: "Music Agent",
      sub: "Backtrack Composer",
      role: "Music Director",
      status: "pending",
      kpi: "Soundtracks Synced",
      x: 940,
      y: 300,
      iconName: "music"
    },
    {
      id: "node-post-1",
      name: "Subtitle Agent",
      sub: "SRT Timing Generator",
      role: "Sync Specialist",
      status: "pending",
      kpi: "Tamil SRT Timed",
      x: 1120,
      y: 60,
      iconName: "filetext"
    },
    {
      id: "node-post-2",
      name: "Video Compositor",
      sub: "FFmpeg Rendering Engine",
      role: "Video Editor",
      status: "pending",
      kpi: "MP4 Rendered",
      x: 1120,
      y: 180,
      iconName: "film"
    },
    {
      id: "node-post-3",
      name: "Thumbnail Agent",
      sub: "Card Cover Designer",
      role: "Graphic Lead",
      status: "pending",
      kpi: "Thumbnails Created",
      x: 1120,
      y: 300,
      iconName: "image"
    },
    {
      id: "node-qa",
      name: "Quality QA Guard",
      sub: "Compliance & Safety",
      role: "Audit Inspector",
      status: "pending",
      kpi: "QA Checks Passed",
      x: 1300,
      y: 180,
      iconName: "shield"
    },
    {
      id: "node-5c",
      name: "Learning Agent",
      sub: "Feedback & Ingestion",
      role: "Audience Lead",
      status: "pending",
      kpi: liveTelemetry?.latest_viral_hook ? liveTelemetry.latest_viral_hook.slice(0, 15) + "..." : "#AATES #Shorts",
      x: 1480,
      y: 180,
      iconName: "brain"
    },
    {
      id: "node-6",
      name: "YouTube Publisher",
      sub: "YouTube Shorts Upload",
      role: "Publishing Lead",
      status: "pending",
      kpi: `${liveTelemetry?.published_today || 1}/${liveTelemetry?.daily_publishing_cap || 1} Uploaded`,
      x: 1660,
      y: 100,
      iconName: "share"
    },
    {
      id: "node-pub-ig",
      name: "Instagram Publisher",
      sub: "Instagram Reels Upload",
      role: "Publishing Lead",
      status: "pending",
      kpi: "Reels Posted",
      x: 1660,
      y: 260,
      iconName: "instagram"
    }
  ];

  // Map execution status using Real-Time Backend Telemetry
  const nodes = initialNodes.map((node, idx) => {
    let status: "completed" | "current" | "pending" = "pending";

    if (isLiveConnected && liveTelemetry && liveTelemetry.nodes_status) {
      let statusKey = node.id;
      if (node.id === "node-prep-1" || node.id === "node-prep-2") {
        statusKey = "node-4";
      } else if (node.id === "node-gen-1" || node.id === "node-gen-2" || node.id === "node-gen-3" || node.id === "node-post-2" || node.id === "node-post-3" || node.id === "node-qa") {
        statusKey = "node-5a";
      } else if (node.id === "node-post-1") {
        statusKey = "node-5b";
      } else if (node.id === "node-pub-ig") {
        statusKey = "node-6";
      }

      if (liveTelemetry.current_active_node === statusKey) {
        status = "current";
      } else if (liveTelemetry.nodes_status[statusKey] === "completed") {
        status = "completed";
      } else if (liveTelemetry.nodes_status[statusKey] === "current") {
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
      case "search": return <Search className={cls} />;
      case "filetext": return <FileText className={cls} />;
      case "image": return <Image className={cls} />;
      case "volume2": return <Volume2 className={cls} />;
      case "music": return <Music className={cls} />;
      case "film": return <Film className={cls} />;
      case "shield": return <ShieldCheck className={cls} />;
      case "sparkles": return <Sparkles className={cls} />;
      case "share": return <Share2 className={cls} />;
      case "instagram": return <Instagram className={cls} />;
      case "brain": return <Brain className={cls} />;
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
        className="relative w-full overflow-x-auto rounded-2xl border border-slate-800 p-4 min-h-[460px] bg-slate-950"
        style={{
          backgroundImage: "radial-gradient(#334155 1.5px, transparent 1.5px)",
          backgroundSize: "24px 24px"
        }}
      >
        {/* SVG Bezier Edges Layer */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ minWidth: "1850px" }}>
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
            d="M 200 215 L 220 215"
            fill="none"
            stroke={nodes[0].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[0].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 2 -> Node 3 */}
          <path
            d="M 380 215 C 390 215, 390 135, 400 135"
            fill="none"
            stroke={nodes[1].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[1].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 2 -> Node 4 */}
          <path
            d="M 380 215 C 390 215, 390 295, 400 295"
            fill="none"
            stroke={nodes[1].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[1].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 3 -> Research Node */}
          <path
            d="M 560 135 C 570 135, 570 215, 580 215"
            fill="none"
            stroke={nodes[2].status === "completed" ? "#10b981" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[2].status === "completed" ? "url(#arrow-green)" : "url(#arrow-gray)"}
          />

          {/* Node 4 -> Research Node */}
          <path
            d="M 560 295 C 570 295, 570 215, 580 215"
            fill="none"
            stroke={nodes[3].status === "completed" ? "#10b981" : nodes[3].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[3].status === "completed" ? "url(#arrow-green)" : nodes[3].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Research -> Script */}
          <path
            d="M 740 215 L 760 215"
            fill="none"
            stroke={nodes[4].status === "completed" ? "#10b981" : nodes[4].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[4].status === "completed" ? "url(#arrow-green)" : nodes[4].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Script -> Image Agent */}
          <path
            d="M 920 215 C 930 215, 930 95, 940 95"
            fill="none"
            stroke={nodes[5].status === "completed" ? "#10b981" : nodes[5].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[5].status === "completed" ? "url(#arrow-green)" : nodes[5].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Script -> Voice Agent */}
          <path
            d="M 920 215 L 940 215"
            fill="none"
            stroke={nodes[5].status === "completed" ? "#10b981" : nodes[5].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[5].status === "completed" ? "url(#arrow-green)" : nodes[5].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Script -> Music Agent */}
          <path
            d="M 920 215 C 930 215, 930 335, 940 335"
            fill="none"
            stroke={nodes[5].status === "completed" ? "#10b981" : nodes[5].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[5].status === "completed" ? "url(#arrow-green)" : nodes[5].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Image Agent -> Subtitle Agent */}
          <path
            d="M 1100 95 L 1120 95"
            fill="none"
            stroke={nodes[6].status === "completed" ? "#10b981" : nodes[6].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[6].status === "completed" ? "url(#arrow-green)" : nodes[6].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Voice Agent -> Video Compositor */}
          <path
            d="M 1100 215 L 1120 215"
            fill="none"
            stroke={nodes[7].status === "completed" ? "#10b981" : nodes[7].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[7].status === "completed" ? "url(#arrow-green)" : nodes[7].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Music Agent -> Thumbnail Agent */}
          <path
            d="M 1100 335 L 1120 335"
            fill="none"
            stroke={nodes[8].status === "completed" ? "#10b981" : nodes[8].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[8].status === "completed" ? "url(#arrow-green)" : nodes[8].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Subtitle Agent -> Quality QA */}
          <path
            d="M 1280 95 C 1290 95, 1290 215, 1300 215"
            fill="none"
            stroke={nodes[9].status === "completed" ? "#10b981" : nodes[9].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[9].status === "completed" ? "url(#arrow-green)" : nodes[9].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Video Compositor -> Quality QA */}
          <path
            d="M 1280 215 L 1300 215"
            fill="none"
            stroke={nodes[10].status === "completed" ? "#10b981" : nodes[10].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[10].status === "completed" ? "url(#arrow-green)" : nodes[10].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Thumbnail Agent -> Quality QA */}
          <path
            d="M 1280 335 C 1290 335, 1290 215, 1300 215"
            fill="none"
            stroke={nodes[11].status === "completed" ? "#10b981" : nodes[11].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[11].status === "completed" ? "url(#arrow-green)" : nodes[11].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Quality QA -> Marketing Engine */}
          <path
            d="M 1460 215 L 1480 215"
            fill="none"
            stroke={nodes[12].status === "completed" ? "#10b981" : nodes[12].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2.5"
            markerEnd={nodes[12].status === "completed" ? "url(#arrow-green)" : nodes[12].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Marketing Engine -> YouTube */}
          <path
            d="M 1640 215 C 1650 215, 1650 135, 1660 135"
            fill="none"
            stroke={nodes[13].status === "completed" ? "#10b981" : nodes[13].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[13].status === "completed" ? "url(#arrow-green)" : nodes[13].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />

          {/* Marketing Engine -> Instagram */}
          <path
            d="M 1640 215 C 1650 215, 1650 295, 1660 295"
            fill="none"
            stroke={nodes[13].status === "completed" ? "#10b981" : nodes[13].status === "current" ? "#3b82f6" : "#475569"}
            strokeWidth="2"
            markerEnd={nodes[13].status === "completed" ? "url(#arrow-green)" : nodes[13].status === "current" ? "url(#arrow-blue)" : "url(#arrow-gray)"}
          />
        </svg>

        {/* Canvas Nodes Layer */}
        <div className="relative min-w-[1850px] h-[350px]">
          {nodes.map((node) => {
            const isCompleted = node.status === "completed";
            const isCurrent = node.status === "current";

            return (
              <div
                key={node.id}
                style={{ left: `${node.x}px`, top: `${node.y - 35}px` }}
                className={`absolute w-[160px] p-3 rounded-xl border transition-all duration-500 shadow-2xl flex flex-col justify-between ${
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
                    <h3 className={`text-[11px] font-bold truncate ${isCompleted ? "text-emerald-300" : isCurrent ? "text-blue-200" : "text-slate-200"}`}>
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
