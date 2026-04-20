'use client';
import { create } from 'zustand';
import type { AgentRun, WebSocketMessage } from '@/types';

interface AgentState {
  runs: AgentRun[];
  currentRun: AgentRun | null;
  isRunning: boolean;
  streamMessages: WebSocketMessage[];
  setRuns: (runs: AgentRun[]) => void;
  addRun: (run: AgentRun) => void;
  setCurrentRun: (run: AgentRun | null) => void;
  setIsRunning: (running: boolean) => void;
  addStreamMessage: (msg: WebSocketMessage) => void;
  clearStream: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  runs: [],
  currentRun: null,
  isRunning: false,
  streamMessages: [],

  setRuns: (runs) => set({ runs }),
  addRun: (run) => set((state) => ({ runs: [run, ...state.runs] })),
  setCurrentRun: (run) => set({ currentRun: run }),
  setIsRunning: (running) => set({ isRunning: running }),
  addStreamMessage: (msg) => set((state) => ({ streamMessages: [...state.streamMessages, msg] })),
  clearStream: () => set({ streamMessages: [] }),
}));
