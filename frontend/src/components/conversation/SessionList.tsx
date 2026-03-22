import { useState } from 'react';
import { useSessionStore } from '../../stores';
import { sessionService } from '../../services/api';
import type { Session } from '../../types';

export default function SessionList() {
  const { sessions, currentSession, createSession, selectSession } = useSessionStore();
  const [newTitle, setNewTitle] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setLoading(true);
    try {
      const session = await createSession(newTitle.trim());
      selectSession(session);
      setNewTitle('');
      setShowInput(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, session: Session) => {
    e.stopPropagation();
    if (!window.confirm(`确定删除会话「${session.title}」？`)) return;
    try {
      await sessionService.delete(session.id);
      const { currentSession: current } = useSessionStore.getState();
      if (current?.id === session.id) {
        useSessionStore.setState({ currentSession: null, messages: [] });
      }
      useSessionStore.setState((state) => ({
        sessions: state.sessions.filter((s) => s.id !== session.id),
      }));
    } catch (err) {
      console.error('删除会话失败:', err);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b bg-gray-50">
        {showInput ? (
          <div className="space-y-2">
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleCreate();
                }
                if (e.key === 'Escape') {
                  setShowInput(false);
                  setNewTitle('');
                }
              }}
              placeholder="输入会话标题..."
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              autoFocus
              maxLength={100}
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={loading || !newTitle.trim()}
                className="flex-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm transition"
              >
                {loading ? '创建中...' : '创建'}
              </button>
              <button
                onClick={() => {
                  setShowInput(false);
                  setNewTitle('');
                }}
                className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm transition"
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowInput(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm font-medium"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建会话
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4">
            <svg className="w-12 h-12 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm text-center">暂无会话记录</p>
            <p className="text-xs mt-1">点击上方按钮创建</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => selectSession(session)}
              onMouseEnter={() => setHoveredSession(session.id)}
              onMouseLeave={() => setHoveredSession(null)}
              className={`p-3 cursor-pointer border-b transition group relative ${
                currentSession?.id === session.id
                  ? 'bg-blue-50 border-l-4 border-l-blue-500'
                  : 'hover:bg-gray-50 border-l-4 border-l-transparent'
              }`}
            >
              <div className="flex justify-between items-start pr-6">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate text-gray-800">{session.title}</p>
                  <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatTime(session.updated_at)}
                  </p>
                </div>
              </div>

              <button
                onClick={(e) => handleDelete(e, session)}
                className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md hover:bg-red-100 text-gray-400 hover:text-red-500 transition opacity-0 group-hover:opacity-100 ${
                  hoveredSession === session.id ? 'opacity-100' : ''
                }`}
                title="删除会话"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}