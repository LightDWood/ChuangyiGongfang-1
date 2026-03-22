import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Session, Message } from '../types';
import { authService, sessionService, messageService } from '../services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      login: async (username: string, password: string) => {
        const response = await authService.login(username, password);
        localStorage.setItem('access_token', response.access_token);
        set({ user: response.user, isAuthenticated: true });
      },
      register: async (username: string, email: string, password: string) => {
        await authService.register(username, email, password);
      },
      logout: async () => {
        try {
          await authService.logout();
        } catch {
        }
        localStorage.removeItem('access_token');
        set({ user: null, isAuthenticated: false });
      },
      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }
        try {
          const user = await authService.getMe();
          set({ user, isAuthenticated: true });
        } catch {
          localStorage.removeItem('access_token');
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

interface SessionState {
  sessions: Session[];
  currentSession: Session | null;
  messages: Message[];
  loading: boolean;
  fetchSessions: () => Promise<void>;
  createSession: (title: string) => Promise<Session>;
  selectSession: (session: Session) => void;
  fetchMessages: (sessionId: string) => Promise<void>;
  addMessage: (message: Message) => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  loading: false,
  fetchSessions: async () => {
    set({ loading: true });
    try {
      const sessions = await sessionService.list();
      set({ sessions, loading: false });
    } catch {
      set({ loading: false });
    }
  },
  createSession: async (title: string) => {
    const session = await sessionService.create(title);
    set((state) => ({ sessions: [session, ...state.sessions] }));
    return session;
  },
  selectSession: (session: Session) => {
    set({ currentSession: session });
    get().fetchMessages(session.id);
  },
  fetchMessages: async (sessionId: string) => {
    const messages = await messageService.list(sessionId) as Message[];
    const normalizedMessages = messages.map((msg: Message) => ({
      ...msg,
      artifacts: msg.artifacts || [],
    }));
    set({ messages: normalizedMessages });
  },
  addMessage: (message: Message) => {
    set((state) => ({ messages: [...state.messages, message] }));
  },
}));
