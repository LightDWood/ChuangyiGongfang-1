export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  artifacts: Artifact[];
  created_at: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  type: 'requirement' | 'specification' | 'code' | 'document';
  title: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export interface StreamChunk {
  type: 'token' | 'artifact' | 'error';
  content: string;
  artifact?: Artifact;
}
