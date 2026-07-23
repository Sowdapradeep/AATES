"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  GitBranch,
  Map,
  Activity,
  Terminal,
  Settings,
  User,
  Film,
  Sparkles,
  Share2,
  LogOut,
  Shield,
  Loader2,
  Search,
  FileText,
  Camera,
  Mic,
  Type,
  Music,
  Image as ImageIcon,
  ShieldCheck,
  Brain,
  Zap,
  Compass,
  BookOpen,
  DollarSign,
  TrendingUp
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const userEmail = "operator@aates.com";

  useEffect(() => {
    const savedToken = localStorage.getItem("aates_token");
    if (!savedToken) {
      router.push("/login");
    } else {
      setToken(savedToken);
    }
    setLoading(false);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("aates_token");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    );
  }

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Live Creation Pipeline", href: "/n8n-graph", icon: GitBranch },
    { name: "AI Research", href: "/research", icon: Search },
    { name: "AI Scripts", href: "/scripts", icon: FileText },
    { name: "AI Images", href: "/images", icon: Camera },
    { name: "AI Voices", href: "/voices", icon: Mic },
    { name: "AI Videos", href: "/videos", icon: Film },
    { name: "AI Subtitles", href: "/subtitles", icon: Type },
    { name: "AI Music", href: "/music", icon: Music },
    { name: "AI Thumbnails", href: "/thumbnails", icon: ImageIcon },
    { name: "AI Quality", href: "/quality", icon: ShieldCheck },
    { name: "Instagram Publish", href: "/publishing/instagram", icon: Share2 },
    { name: "AI Learning", href: "/learning", icon: Brain },
    { name: "AI Automation", href: "/automation", icon: Zap },
    { name: "Narrative Intelligence", href: "/narrative", icon: BookOpen },
    { name: "Financial Governor", href: "/finance", icon: DollarSign },
    { name: "Revenue Engine", href: "/revenue", icon: TrendingUp },
    { name: "Orchestrator", href: "/orchestration", icon: Compass },
    { name: "System Map", href: "/system-map", icon: Map },
    { name: "Validation", href: "/validation", icon: Shield },
    { name: "Scheduler Jobs", href: "/jobs", icon: Activity },
    { name: "System Logs", href: "/logs", icon: Terminal },
    { name: "Settings", href: "/settings", icon: Settings },
    { name: "Profile", href: "/profile", icon: User },
  ];

  const futureModules = [
    { name: "AI Studio", href: "/studio", icon: Film },
    { name: "Prompt Manager", href: "/prompts", icon: Sparkles },
    { name: "Publisher", href: "/publisher", icon: Share2 },
  ];

  return (
    <div className="flex min-h-screen text-slate-100">
      {/* Sidebar */}
      <aside className="glass-panel sticky top-0 h-screen w-64 flex-shrink-0 border-r border-slate-800/60 p-4 flex flex-col">
        <div className="mb-6 flex items-center gap-3 px-2 flex-shrink-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-violet-600 to-pink-500 shadow-md">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
              AATES
            </h1>
            <span className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
              Operating System
            </span>
          </div>
        </div>

        {/* Scrollable Navigation links list */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-1 mb-4 scrollbar-thin scrollbar-thumb-slate-800">
          <div>
            <span className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
              Platform
            </span>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? "bg-gradient-to-r from-violet-600/20 to-pink-500/10 border border-violet-500/20 text-violet-300 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                    }`}
                  >
                    <Icon className={`h-4.5 w-4.5 ${isActive ? "text-violet-400" : "text-slate-400"}`} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div>
            <span className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
              Future Modules
            </span>
            <nav className="space-y-1">
              {futureModules.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? "bg-gradient-to-r from-violet-600/20 to-pink-500/10 border border-violet-500/20 text-violet-300 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                    }`}
                  >
                    <Icon className="h-4.5 w-4.5 text-slate-400" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="pt-4 border-t border-slate-800/60 flex-shrink-0 space-y-2">
          <div className="flex items-center gap-3 px-2 py-2 rounded-xl bg-slate-900/30 border border-slate-800/40">
            <div className="h-8 w-8 rounded-full bg-violet-600/30 border border-violet-500/40 flex items-center justify-center text-xs font-semibold text-violet-300 uppercase">
              OP
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-200 truncate">{userEmail}</p>
              <p className="text-[10px] text-violet-400 font-semibold uppercase">Operator</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
          >
            <LogOut className="h-4.5 w-4.5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="glass-panel sticky top-0 z-10 flex h-16 items-center justify-between border-b border-slate-800/60 px-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-xs font-medium text-emerald-400">System Ready</span>
            </div>
            <span className="text-slate-600">|</span>
            <div className="text-xs text-slate-400 font-medium">
              Universe: <span className="text-violet-400">Kadamban V1</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs bg-slate-950/60 border border-slate-800/80 px-3 py-1 rounded-full text-slate-400 font-mono">
              AWS: Free Tier Env
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}
