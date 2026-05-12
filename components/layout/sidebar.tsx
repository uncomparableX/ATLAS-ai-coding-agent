"use client";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/lib/stores/ui-store";
import { motion } from "framer-motion";
import {
  GitBranch,
  LayoutDashboard,
  MessageSquare,
  Settings,
  BarChart3,
  Plus,
  Search,
} from "lucide-react";
import { GlowButton } from "@/components/glass/glow-button";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: GitBranch, label: "Repositories", href: "/repo" },
  { icon: MessageSquare, label: "Agents", href: "/agent" },
  { icon: BarChart3, label: "Analytics", href: "/analytics" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarOpen ? 260 : 72 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="glass-panel border-r border-border flex flex-col shrink-0 z-20"
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-secondary flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          {sidebarOpen && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-semibold text-foreground"
            >
              Agentic
            </motion.span>
          )}
        </div>
      </div>

      {/* New Task */}
      <div className="p-3">
        <GlowButton
          variant="primary"
          size={sidebarOpen ? "md" : "sm"}
          className={cn("w-full justify-center", !sidebarOpen && "px-2")}
        >
          <Plus className="w-4 h-4 shrink-0" />
          {sidebarOpen && <span>New Task</span>}
        </GlowButton>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        {navItems.map((item) => (
          <a
            key={item.label}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]",
              "group"
            )}
          >
            <item.icon className="w-4 h-4 shrink-0 group-hover:text-accent transition-colors" />
            {sidebarOpen && <span>{item.label}</span>}
          </a>
        ))}
      </nav>

      {/* Search */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] text-muted-foreground text-sm">
          <Search className="w-4 h-4 shrink-0" />
          {sidebarOpen && (
            <>
              <span className="flex-1">Search...</span>
              <kbd className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
                ⌘K
              </kbd>
            </>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
