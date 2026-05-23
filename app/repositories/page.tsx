"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { GlassCard } from "@/components/glass/glass-card";
import { GlowButton } from "@/components/glass/glow-button";
import { Plus, FolderGit2, Ghost } from "lucide-react";

export default function RepositoriesPage() {
  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-background/50">
        <div className="h-14 border-b border-border flex items-center px-6 bg-background/50 backdrop-blur-sm">
          <FolderGit2 className="w-4 h-4 text-accent mr-2" />
          <h1 className="font-semibold tracking-wide">Repositories</h1>
        </div>

        <div className="p-6 max-w-4xl mx-auto w-full mt-10">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold">Workspace Repositories</h2>
              <p className="text-sm text-muted-foreground mt-1">Connect codebases for ATLAS to analyze and modify.</p>
            </div>
            <GlowButton variant="primary">
              <Plus className="w-4 h-4 mr-2" /> Connect Repository
            </GlowButton>
          </div>

          <GlassCard className="p-16 flex flex-col items-center justify-center text-center border-dashed border-white/10">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6">
              <Ghost className="w-8 h-8 text-muted-foreground opacity-50" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No repositories connected</h3>
            <p className="text-sm text-muted-foreground max-w-md mb-8">
              ATLAS needs access to a repository to begin analyzing codebase architecture and executing tasks.
            </p>
            <GlowButton variant="secondary">
              Connect your first repository
            </GlowButton>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
