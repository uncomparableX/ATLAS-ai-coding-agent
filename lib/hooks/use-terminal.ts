"use client";

import { useState, useCallback } from "react";
import { LogEntry } from "@/types";

export function useTerminal(maxLines = 1000) {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = useCallback(
    (entry: Omit<LogEntry, "id" | "timestamp">) => {
      const newLog: LogEntry = {
        ...entry,
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date(),
      };

      setLogs((prev) => {
        const updated = [...prev, newLog];
        if (updated.length > maxLines) {
          return updated.slice(updated.length - maxLines);
        }
        return updated;
      });
    },
    [maxLines]
  );

  const clearLogs = useCallback(() => setLogs([]), []);

  return { logs, addLog, clearLogs };
}
