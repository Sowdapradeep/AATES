"use client";

import React, { useEffect, useState } from "react";
import { BookOpen, Sparkles, User, MapPin, Activity, AlertTriangle } from "lucide-react";

export default function NarrativeIntelligencePage() {
  const [universe, setUniverse] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/v1/narrative/universes")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.length > 0) {
          setUniverse(data[0]);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BookOpen className="h-7 w-7 text-pink-500" />
            Narrative Intelligence v2
          </h1>
          <p className="text-sm text-slate-400">
            Autonomous AI reasoning engine over persistent ORM story canon & character entities.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-400">Master Universe</span>
            <Sparkles className="h-5 w-5 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {universe ? universe.name : "AATES Tamil Realm"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Genre: {universe ? universe.genre : "Epic Drama"}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-400">Continuity Audit</span>
            <Activity className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">100% Canon Passed</div>
          <div className="text-xs text-slate-500 mt-1">ORM entity constraint verification active</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-400">Memory Embeddings</span>
            <BookOpen className="h-5 w-5 text-violet-400" />
          </div>
          <div className="text-xl font-bold text-white">AWS Titan v2 (1536-dim)</div>
          <div className="text-xs text-slate-500 mt-1">pgvector semantic memory search</div>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <h2 className="text-lg font-semibold text-white mb-4">Reasoning Engine Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="font-semibold text-pink-400 mb-1">1. Character Intelligence</div>
            <div className="text-xs text-slate-400">Tracks goals, fears, motivations & emotional growth.</div>
          </div>
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="font-semibold text-amber-400 mb-1">2. Relationship Intelligence</div>
            <div className="text-xs text-slate-400">Evolves tension scores (0.0 to 1.0) & rivalries.</div>
          </div>
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="font-semibold text-emerald-400 mb-1">3. Continuity Reasoning</div>
            <div className="text-xs text-slate-400">Prevents deceased characters & timeline collisions.</div>
          </div>
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
            <div className="font-semibold text-violet-400 mb-1">4. Creative Director AI</div>
            <div className="text-xs text-slate-400">Reasons first over ORM canon before compiling blueprint.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
