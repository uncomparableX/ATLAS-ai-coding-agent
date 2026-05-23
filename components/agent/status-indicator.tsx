"use client";

import { cn } from "@/lib/utils";

interface StatusIndicatorProps {
  status?: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

const statusConfig = {
  idle: {
    label: "Idle",
    color: "bg-muted",
    animation: "none",
  },
  working: {
    label: "Working",
    color: "bg-accent",
    animation: "pulse",
  },
  success: {
    label: "Success",
    color: "bg-terminal-green",
    animation: "none",
  },
  error: {
    label: "Error",
    color: "bg-red-500",
    animation: "none",
  },
};

export function StatusIndicator({ 
  status = "idle", 
  size = "sm", 
  showLabel = false 
}: StatusIndicatorProps) {
  
  // Normalize incoming status from different dashboard states
  let normalized = status.toLowerCase();
  if (normalized === "running") normalized = "working";
  if (normalized === "complete") normalized = "success";
  if (normalized === "failed") normalized = "error";
  if (normalized === "paused") normalized = "idle";

  // Safe fallback lookup to prevent runtime crashes
  const config = statusConfig[normalized as keyof typeof statusConfig] || statusConfig.idle;

  const sizeClasses = {
    sm: "w-2 h-2",
    md: "w-3 h-3",
    lg: "w-4 h-4",
  };

  const currentSize = sizeClasses[size] || sizeClasses.sm;

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex items-center justify-center">
        {config.animation === "pulse" && (
          <div
            className={cn(
              "absolute rounded-full opacity-50 animate-ping",
              config.color,
              currentSize
            )}
          />
        )}
        <div
          className={cn(
            "rounded-full shadow-sm",
            config.color,
            currentSize
          )}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-muted-foreground">
          {config.label}
        </span>
      )}
    </div>
  );
}
