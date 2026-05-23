"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { GlassCard } from "@/components/glass/glass-card";
import { Settings, Zap, Palette, Monitor } from "lucide-react";
import { GlowButton } from "@/components/glass/glow-button";

export default function SettingsPage() {
  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-background/50">
        <div className="h-14 border-b border-border flex items-center px-6 bg-background/50 backdrop-blur-sm">
          <Settings className="w-4 h-4 text-accent mr-2" />
          <h1 className="font-semibold tracking-wide">Settings</h1>
        </div>

        <div className="p-6 max-w-3xl mx-auto w-full space-y-6">
          <div className="mb-2">
            <h2 className="text-xl font-bold">Platform Configuration</h2>
            <p className="text-sm text-muted-foreground mt-1">Manage your ATLAS workspace preferences and integrations.</p>
          </div>

          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Zap className="w-5 h-5 text-accent" />
              <h3 className="font-medium text-lg">ATLAS Usage & Limits</h3>
            </div>
            <div className="space-y-6">
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <div>
                  <div className="text-sm font-medium text-foreground">ATLAS Credits</div>
                  <div className="text-xs text-muted-foreground mt-1">Free Tier Active</div>
                </div>
                <div className="text-sm font-mono text-accent">78% Remaining</div>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <div>
                  <div className="text-sm font-medium text-foreground">Daily Usage</div>
                  <div className="text-xs text-muted-foreground mt-1">Requests limit resets in 6 hours</div>
                </div>
                <div className="text-sm font-mono text-muted-foreground">43 / 1000</div>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <div>
                  <div className="text-sm font-medium text-foreground">Connection Status</div>
                  <div className="text-xs text-muted-foreground mt-1">Main Execution Engine</div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
                  <span className="text-sm text-terminal-green">Connected</span>
                </div>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Monitor className="w-5 h-5 text-accent" />
              <h3 className="font-medium text-lg">System Configuration</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-white/5">
                <div>
                  <div className="text-sm font-medium">Auto-Execute Mode</div>
                  <div className="text-xs text-muted-foreground">Allow ATLAS to run commands without prompting</div>
                </div>
                <div className="w-10 h-5 bg-accent/20 rounded-full relative cursor-pointer">
                  <div className="absolute right-1 top-1 w-3 h-3 bg-accent rounded-full" />
                </div>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Palette className="w-5 h-5 text-accent" />
              <h3 className="font-medium text-lg">Appearance</h3>
            </div>
            <div className="flex gap-4">
              <button className="flex-1 border-2 border-accent bg-black/20 rounded-lg p-4 text-sm font-medium text-center">
                Dark Mode
              </button>
              <button className="flex-1 border-2 border-transparent bg-white/5 opacity-50 cursor-not-allowed rounded-lg p-4 text-sm font-medium text-center">
                Light Mode (Soon)
              </button>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
