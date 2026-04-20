'use client';
import { create } from 'zustand';
import type { Project } from '@/types';
import { projectsApi } from '@/lib/api';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  isLoading: boolean;
  fetchProjects: () => Promise<void>;
  createProject: (name: string, description?: string, repo_url?: string) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  isLoading: false,

  fetchProjects: async () => {
    set({ isLoading: true });
    try {
      const { data } = await projectsApi.list();
      set({ projects: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  createProject: async (name, description, repo_url) => {
    const { data } = await projectsApi.create({ name, description, repo_url });
    set((state) => ({ projects: [data, ...state.projects] }));
  },

  deleteProject: async (id) => {
    await projectsApi.delete(id);
    set((state) => ({ projects: state.projects.filter((p) => p.id !== id) }));
  },

  setCurrentProject: (project) => set({ currentProject: project }),
}));
