"use client";

import React from "react";
import { Film } from "lucide-react";

export default function StudioPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <div className="p-4 bg-violet-600/10 border border-violet-500/20 rounded-2xl text-violet-400">
        <Film className="h-12 w-12 animate-bounce" />
      </div>
      <h1 className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
        AATES AI Studio
      </h1>
      <p className="text-sm text-slate-400 max-w-md leading-relaxed">
        Autonomous scene production, audio matching, and rendering workflows will load here during Phase 2.
      </p>
    </div>
  );
}
