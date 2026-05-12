import { create } from "zustand";
import { persist } from "zustand/middleware";
import { AgentTask, AgentMessage, AgentStatus, LogEntry, Thought } from "@/types";

interface AgentStore {
  tasks: AgentTask[];
  messages: AgentMessage[];
  status: AgentStatus;
  selectedTaskId: string | null;
  isStreaming: boolean;
  
  // Actions
  addTask: (task: AgentTask) => void;
  updateTask: (id: string, updates: Partial<AgentTask>) => void;
  selectTask: (id: string | null) => void;
  addMessage: (message: AgentMessage) => void;
  appendToLastMessage: (content: string) => void;
  setStreaming: (streaming: boolean) => void;
  addLog: (taskId: string, log: LogEntry) => void;
  addThought: (taskId: string, thought: Thought) => void;
  updateStatus: (status: Partial<AgentStatus>) => void;
}

export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({
      tasks: [],
      messages: [],
      status: { state: "idle", progress: 0, lastActivity: new Date() },
      selectedTaskId: null,
      isStreaming: false,

      addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
      
      updateTask: (id, updates) =>
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === id ? { ...t, ...updates, updatedAt: new Date() } : t
          ),
        })),

      selectTask: (id) => set({ selectedTaskId: id }),
      
      addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
      
      appendToLastMessage: (content) =>
        set((state) => {
          const messages = [...state.messages];
          const last = messages[messages.length - 1];
          if (last && last.role === "agent") {
            last.content += content;
          }
          return { messages };
        }),
      
      setStreaming: (streaming) => set({ isStreaming: streaming }),
      
      addLog: (taskId, log) =>
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === taskId ? { ...t, logs: [...t.logs, log] } : t
          ),
        })),
      
      addThought: (taskId, thought) =>
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === taskId ? { ...t, thoughts: [...t.thoughts, thought] } : t
          ),
        })),
      
      updateStatus: (status) =>
        set((state) => ({
          status: { ...state.status, ...status, lastActivity: new Date() },
        })),
    }),
    { name: "agent-store" }
  )
);
