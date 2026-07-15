"use client";

import React from "react";
import { Share2 } from "lucide-react";

export default function PublisherPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <div className="p-4 bg-violet-600/10 border border-violet-500/20 rounded-2xl text-violet-400">
        <Share2 className="h-12 w-12" />
      </div>
      <h1 className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
        Autonomous Publisher
      </h1>
      <p className="text-sm text-slate-400 max-w-md leading-relaxed">
        Automated YouTube, Instagram, and TikTok social export scheduling controllers will load here during Phase 2.
      </p>
    </div>
  );
}
