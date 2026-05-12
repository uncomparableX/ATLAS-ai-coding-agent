"use client";

import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { LogEntry } from "@/types";

interface TerminalProps {
  logs: LogEntry[];
  title?: string;
  className?: string;
  maxHeight?: string;
  live?: boolean;
}

const levelColors = {
  info: "text-terminal-blue",
  warn: "text-terminal-yellow",
  error: "text-error",
  debug: "text-terminal-purple",
  success: "text-terminal-green",
};

const levelIcons = {
  info: "ℹ",
  warn: "⚠",
  error: "✖",
  debug: "◆",
  success: "✓",
};

export function Terminal({
  logs,
  title = "agent.log",
  className,
  maxHeight = "300px",
  live = true,
}: TerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (!isHovered && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isHovered]);

  return (
    <div
      className={cn(
        "glass-panel flex flex-col overflow-hidden font-mono text-xs",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-black/20">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          </div>
          <span className="text-muted-foreground ml-2">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {live && (
            <span className="flex items-center gap-1.5 text-terminal-green">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-terminal-green opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-terminal-green" />
              </span>
              LIVE
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        ref={scrollRef}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="flex-1 overflow-auto p-4 space-y-1"
        style={{ maxHeight }}
      >
        <AnimatePresence initial={false}>
          {logs.map((log, i) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-start gap-2 hover:bg-white/[0.02] rounded px-1 -mx-1"
            >
              <span className="text-muted-foreground/50 shrink-0 select-none">
                {log.timestamp.toLocaleTimeString("en-US", {
                  hour12: false,
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
              <span className={cn("shrink-0", levelColors[log.level])}>
                {levelIcons[log.level]}
              </span>
              <span className={cn("break-all", levelColors[log.level])}>
                <span className="text-muted-foreground/70">[{log.source}]</span>{" "}
                {log.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        {live && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="inline-block w-2 h-4 bg-accent mt-1"
          />
        )}
      </div>
    </div>
  );
}
