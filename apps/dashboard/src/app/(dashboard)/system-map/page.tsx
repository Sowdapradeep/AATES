"use client";

import React from "react";
import {
  Shield,
  Film,
  BookOpen,
  MessageSquare,
  Image as ImageIcon,
  Video as VideoIcon,
  Mic,
  Share2,
  TrendingUp,
  Clock,
  Cpu
} from "lucide-react";

export default function SystemMapPage() {
  const actors = [
    { name: "CEO Agent", desc: "Oversees production priorities and schedules workflows.", icon: Shield, status: "Active" },
    { name: "Director Agent", desc: "Orchestrates step-by-step asset production pipelines.", icon: Film, status: "Idle" },
    { name: "Story Agent", desc: "Drafts dialogue scripts and plot outlines.", icon: BookOpen, status: "Idle" },
    { name: "Dialogue Agent", desc: "Generates authentic Tamil dialogue variations.", icon: MessageSquare, status: "Idle" },
    { name: "Storyboard Agent", desc: "Coordinates scene illustrations and pacing styles.", icon: ImageIcon, status: "Idle" },
    { name: "Video Agent", desc: "Invokes generative video models for episodic rendering.", icon: VideoIcon, status: "Idle" },
    { name: "Voice Agent", desc: "Performs Tamil text-to-speech audio rendering.", icon: Mic, status: "Idle" },
    { name: "Publisher Agent", desc: "Coordinates automated exports and uploads.", icon: Share2, status: "Idle" },
    { name: "Analytics Agent", desc: "Monitors viewer counts and social signals.", icon: TrendingUp, status: "Active" },
    { name: "Scheduler", desc: "Triggers planned recurring tasks and cycles.", icon: Clock, status: "Active" },
    { name: "Workers", desc: "Runs computationally heavy async jobs on hosts.", icon: Cpu, status: "Active" }
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
          AATES System Map
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Architectural node routing and active execution states of all system orchestrators and agents
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {actors.map((actor) => {
          const Icon = actor.icon;
          return (
            <div key={actor.name} className="glass-card rounded-2xl p-6 border border-slate-800/80 transition-all duration-300 hover:border-violet-500/20">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-violet-600/10 border border-violet-500/20 rounded-xl text-violet-400">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-slate-200">{actor.name}</h3>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase ${
                  actor.status === "Active"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-slate-800 text-slate-400 border border-slate-700"
                }`}>
                  {actor.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{actor.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
