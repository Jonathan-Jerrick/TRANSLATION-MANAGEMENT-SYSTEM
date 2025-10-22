import { create } from 'zustand';
import { devtools, persist, createJSONStorage } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: 'admin' | 'manager' | 'translator' | 'reviewer' | 'client';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface Project {
  id: string;
  name: string;
  sector: string;
  source_locale: string;
  target_locales: string[];
  status: 'intake' | 'in_progress' | 'completed';
  progress: number;
  created_at: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  assigned_vendor_id?: string;
  assigned_user_id?: string;
  metadata?: Record<string, any>;
}

export interface ProjectDraft {
  name: string;
  sector: string;
  source_locale: string;
  target_locales: string[];
  content: string;
  description?: string;
  client?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  due_date?: string;
  workflow_mode: 'human_post_edit' | 'human_only' | 'nmt_first' | 'full_llm';
}

export interface TranslationSegment {
  id: string;
  source_text: string;
  target_locale: string;
  tm_suggestion?: string;
  tm_score?: number;
  nmt_suggestion?: string;
  post_edit?: string;
  reviewer_notes?: string;
  risk_level?: 'low' | 'medium' | 'high';
  quality_estimate?: number;
  qa_flags: string[];
  term_hits: string[];
  created_at: string;
  updated_at?: string;
}

export interface WebSocketMessage {
  type: string;
  user_id?: string;
  project_id?: string;
  segment_id?: string;
  content?: string;
  timestamp?: number;
  [key: string]: any;
}

type PageState = Record<string, unknown>;

interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;

  // Projects state
  projects: Project[];
  currentProject: Project | null;

  // Translation state
  segments: TranslationSegment[];
  currentSegment: TranslationSegment | null;

  // WebSocket state
  isConnected: boolean;
  collaborators: string[];
  typingUsers: Record<string, string[]>;

  // UI state
  isLoading: boolean;
  error: string | null;
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    timestamp: number;
  }>;

  // Navigation & persistence
  lastVisitedRoute: string;
  pageState: PageState;
  projectDraft: ProjectDraft;

  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  setSegments: (segments: TranslationSegment[]) => void;
  setCurrentSegment: (segment: TranslationSegment | null) => void;
  updateSegment: (segmentId: string, updates: Partial<TranslationSegment>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  setWebSocketConnected: (connected: boolean) => void;
  setCollaborators: (collaborators: string[]) => void;
  setTypingUsers: (segmentId: string, users: string[]) => void;
  clearTypingUsers: (segmentId: string) => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  setLastVisitedRoute: (route: string) => void;
  updatePageState: <T>(key: string, value: Partial<T> | T | ((previous?: T) => T)) => void;
  clearPageState: (key?: string) => void;
  setProjectDraft: (updates: Partial<ProjectDraft> | ((draft: ProjectDraft) => ProjectDraft)) => void;
  resetProjectDraft: () => void;
  logout: () => void;
}

const noopStorage = {
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
  clear: () => undefined,
  key: () => null,
  length: 0,
} as Storage;

const defaultProjectDraft: ProjectDraft = {
  name: '',
  sector: '',
  source_locale: '',
  target_locales: [],
  content: '',
  description: '',
  client: '',
  priority: 'medium',
  due_date: '',
  workflow_mode: 'human_post_edit',
};

const getInitialToken = () =>
  typeof window !== 'undefined' ? window.localStorage.getItem('token') : null;

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: null,
        isAuthenticated: !!getInitialToken(),
        token: getInitialToken(),

        projects: [],
        currentProject: null,

        segments: [],
        currentSegment: null,

        isConnected: false,
        collaborators: [],
        typingUsers: {},

        isLoading: false,
        error: null,
        notifications: [],
        lastVisitedRoute: '/dashboard',
        pageState: {},
        projectDraft: defaultProjectDraft,

        // Actions
        setUser: (user) => set({ user, isAuthenticated: !!user }),

        setToken: (token) => {
          set({ token, isAuthenticated: !!token });
          if (typeof window !== 'undefined') {
            if (token) {
              window.localStorage.setItem('token', token);
            } else {
              window.localStorage.removeItem('token');
            }
          }
        },

        setProjects: (projects) => set({ projects }),

        setCurrentProject: (currentProject) => set({ currentProject }),

        setSegments: (segments) => set({ segments }),

        setCurrentSegment: (currentSegment) => set({ currentSegment }),

        updateSegment: (segmentId, updates) =>
          set((state) => ({
            segments: state.segments.map((segment) =>
              segment.id === segmentId ? { ...segment, ...updates } : segment,
            ),
            currentSegment:
              state.currentSegment?.id === segmentId
                ? { ...state.currentSegment, ...updates }
                : state.currentSegment,
          })),

        setLoading: (isLoading) => set({ isLoading }),

        setError: (error) => set({ error }),

        addNotification: (notification) =>
          set((state) => ({
            notifications: [
              ...state.notifications,
              {
                ...notification,
                id: Math.random().toString(36).slice(2, 11),
                timestamp: Date.now(),
              },
            ],
          })),

        removeNotification: (id) =>
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          })),

        setWebSocketConnected: (isConnected) => set({ isConnected }),

        setCollaborators: (collaborators) => set({ collaborators }),

        setTypingUsers: (segmentId, users) =>
          set((state) => ({
            typingUsers: {
              ...state.typingUsers,
              [segmentId]: users,
            },
          })),

        clearTypingUsers: (segmentId) =>
          set((state) => {
            const newTypingUsers = { ...state.typingUsers };
            delete newTypingUsers[segmentId];
            return { typingUsers: newTypingUsers };
          }),

        handleWebSocketMessage: (message) => {
          const { type, user_id, segment_id, content } = message;

          switch (type) {
            case 'user_joined':
              set((state) => ({
                collaborators: [...state.collaborators, user_id!],
              }));
              break;

            case 'user_left':
              set((state) => ({
                collaborators: state.collaborators.filter((id) => id !== user_id),
              }));
              break;

            case 'segment_updated':
              if (segment_id && content) {
                get().updateSegment(segment_id, { post_edit: content });
              }
              break;

            case 'typing':
              if (segment_id && user_id) {
                const { typingUsers } = get();
                const currentUsers = typingUsers[segment_id] || [];
                const newUsers = message.is_typing
                  ? [...currentUsers.filter((id) => id !== user_id), user_id]
                  : currentUsers.filter((id) => id !== user_id);

                get().setTypingUsers(segment_id, newUsers);
              }
              break;

            default:
              break;
          }
        },

        setLastVisitedRoute: (route) => set({ lastVisitedRoute: route }),

        updatePageState: (key, value) =>
          set((state) => {
            const previous = state.pageState[key];
            let nextValue: unknown;

            if (typeof value === 'function') {
              nextValue = (value as (prev?: unknown) => unknown)(previous);
            } else if (
              value &&
              typeof value === 'object' &&
              !Array.isArray(value) &&
              previous &&
              typeof previous === 'object' &&
              !Array.isArray(previous)
            ) {
              nextValue = { ...previous, ...value };
            } else {
              nextValue = value;
            }

            return {
              pageState: {
                ...state.pageState,
                [key]: nextValue,
              },
            };
          }),

        clearPageState: (key) =>
          set((state) => {
            if (!key) {
              return { pageState: {} };
            }
            const newPageState = { ...state.pageState };
            delete newPageState[key];
            return { pageState: newPageState };
          }),

        setProjectDraft: (updates) =>
          set((state) => {
            const currentDraft = state.projectDraft;
            const nextDraft =
              typeof updates === 'function'
                ? (updates as (draft: ProjectDraft) => ProjectDraft)(currentDraft)
                : { ...currentDraft, ...updates };
            return { projectDraft: nextDraft };
          }),

        resetProjectDraft: () => set({ projectDraft: defaultProjectDraft }),

        logout: () => {
          if (typeof window !== 'undefined') {
            window.localStorage.removeItem('token');
          }
          set({
            user: null,
            isAuthenticated: false,
            token: null,
            projects: [],
            currentProject: null,
            segments: [],
            currentSegment: null,
            isConnected: false,
            collaborators: [],
            typingUsers: {},
            isLoading: false,
            error: null,
            notifications: [],
            lastVisitedRoute: '/login',
            pageState: {},
            projectDraft: defaultProjectDraft,
          });
        },
      }),
      {
        name: 'tms-store',
        storage: createJSONStorage(() =>
          typeof window !== 'undefined' ? window.localStorage : noopStorage,
        ),
        partialize: (state) => ({
          token: state.token,
          user: state.user,
          projects: state.projects,
          currentProject: state.currentProject,
          segments: state.segments,
          currentSegment: state.currentSegment,
          notifications: state.notifications,
          isAuthenticated: state.isAuthenticated,
          lastVisitedRoute: state.lastVisitedRoute,
          pageState: state.pageState,
          projectDraft: state.projectDraft,
        }),
      },
    ),
  ),
);
