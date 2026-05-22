"use client";

import { Shell } from "@/components/layout/shell";
import { Sidebar } from "@/components/layout/sidebar";
import { FileTree } from "@/components/code/file-tree";
import { GlassCard } from "@/components/glass/glass-card";
import { useState } from "react";
import { useParams } from "next/navigation";
import { FileNode } from "@/types";
import { motion } from "framer-motion";
import {
  Search,
  GitBranch,
  Star,
  GitFork,
  FileCode,
  Folder,
} from "lucide-react";

const mockRepo: FileNode[] = [
  {
    id: "1",
    name: "src",
    type: "directory",
    path: "src",
    children: [
      {
        id: "2",
        name: "auth",
        type: "directory",
        path: "src/auth",
        children: [
          {
            id: "3",
            name: "oauth.ts",
            type: "file",
            path: "src/auth/oauth.ts",
            language: "typescript",
            size: 2847,
          },
          {
            id: "4",
            name: "jwt.ts",
            type: "file",
            path: "src/auth/jwt.ts",
            language: "typescript",
            size: 1234,
          },
        ],
      },
      {
        id: "5",
        name: "components",
        type: "directory",
        path: "src/components",
        children: [
          {
            id: "6",
            name: "Button.tsx",
            type: "file",
            path: "src/components/Button.tsx",
            language: "tsx",
            size: 892,
          },
          {
            id: "7",
            name: "Input.tsx",
            type: "file",
            path: "src/components/Input.tsx",
            language: "tsx",
            size: 654,
          },
        ],
      },
      {
        id: "8",
        name: "app.ts",
        type: "file",
        path: "src/app.ts",
        language: "typescript",
        size: 3421,
      },
    ],
  },
  {
    id: "9",
    name: "package.json",
    type: "file",
    path: "package.json",
    language: "json",
    size: 2847,
  },
  {
    id: "10",
    name: "README.md",
    type: "file",
    path: "README.md",
    language: "markdown",
    size: 4521,
  },
];

export default function RepoPage() {
  const params = useParams();
  const repoId = params?.id as string;

  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <Shell>
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Repo Header */}
        <div className="h-14 border-b border-border flex items-center justify-between px-6 bg-background/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <GitBranch className="w-4 h-4 text-accent" />
            <span className="font-semibold">acme/webapp</span>
            <span className="text-xs text-muted-foreground px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
              main
            </span>
            <span className="text-xs text-accent">
              Repo #{repoId}
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Star className="w-3.5 h-3.5" /> 1.2k
            </span>
            <span className="flex items-center gap-1">
              <GitFork className="w-3.5 h-3.5" /> 234
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="px-6 py-3 border-b border-border">
          <div className="glass-panel flex items-center gap-3 px-4 py-2 max-w-2xl">
            <Search className="w-4 h-4 text-muted-foreground" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Semantic search across codebase..."
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/50"
            />
            <kbd className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded border border-white/10 text-muted-foreground">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* File Tree */}
          <div className="w-72 border-r border-border overflow-auto p-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4 px-2">
              <Folder className="w-3.5 h-3.5" />
              <span className="font-medium">EXPLORER</span>
            </div>

            <FileTree
              nodes={mockRepo}
              onSelect={setSelectedFile}
              selectedPath={selectedFile?.path}
            />
          </div>

          {/* Code View */}
          <div className="flex-1 overflow-auto p-6">
            {selectedFile ? (
              <motion.div
                key={selectedFile.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-accent" />
                    <span className="font-mono text-sm">
                      {selectedFile.path}
                    </span>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    {selectedFile.size} bytes • {selectedFile.language}
                  </div>
                </div>

                <GlassCard className="p-4">
                  <pre className="font-mono text-sm text-foreground/80 leading-relaxed overflow-x-auto">
                    <code>{`// ${selectedFile.name}
import { OAuth2Strategy } from 'passport-oauth2';
import { Request } from 'express';

export class GoogleOAuthStrategy extends OAuth2Strategy {
  constructor() {
    super(
      {
        clientID: process.env.GOOGLE_CLIENT_ID!,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
        callbackURL: '/auth/google/callback',
      },
      this.verify.bind(this)
    );
  }

  async verify(
    accessToken: string,
    refreshToken: string,
    profile: any,
    done: Function
  ) {
    try {
      const user = await this.findOrCreateUser(profile);
      return done(null, user);
    } catch (error) {
      return done(error, false);
    }
  }
}`}</code>
                  </pre>
                </GlassCard>
              </motion.div>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                Select a file to view its contents
              </div>
            )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
