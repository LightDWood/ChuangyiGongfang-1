import { useEffect, useState } from 'react';
import { useSessionStore, useAuthStore } from '../stores';
import MainLayout from '../components/layout/MainLayout';

export default function ChatPage() {
  const { fetchSessions, currentSession } = useSessionStore();
  const { isAuthenticated, checkAuth } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        await checkAuth();
      } catch (err) {
        console.error('Auth check failed:', err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [checkAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions()
        .catch((err) => {
          console.error('Failed to fetch sessions:', err);
          setError('加载会话失败，请刷新重试');
        });
    }
  }, [isAuthenticated, fetchSessions]);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="w-16 h-16 mx-auto text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="mt-4 text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            刷新页面
          </button>
        </div>
      </div>
    );
  }

  return <MainLayout />;
}