import { useState, useEffect } from 'react';
import { useSessionStore } from '../../stores';
import SessionList from '../conversation/SessionList';
import ChatPanel from '../conversation/ChatPanel';
import ArtifactPanel from '../artifacts/ArtifactPanel';
import Header from './Header';

export default function MainLayout() {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const { currentSession } = useSessionStore();

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setLeftSidebarOpen(false);
        setRightSidebarOpen(false);
      } else {
        setLeftSidebarOpen(true);
        setRightSidebarOpen(true);
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <div
          className={`${
            leftSidebarOpen ? 'w-64' : 'w-0'
          } transition-all duration-300 ease-in-out border-r bg-white overflow-hidden flex-shrink-0 ${
            isMobile && leftSidebarOpen ? 'fixed inset-y-14 left-0 z-50 w-64' : ''
          }`}
        >
          <SessionList />
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between border-b bg-white px-4 py-2">
            <button
              onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
              title="切换左侧面板"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
                title="切换右侧面板"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                </svg>
              </button>
            </div>
          </div>

          {currentSession ? (
            <ChatPanel />
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 bg-gray-50">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p className="text-lg">选择或创建一个会话开始</p>
                <p className="text-sm mt-2">点击左侧「新建会话」按钮</p>
              </div>
            </div>
          )}
        </div>

        {currentSession && (
          <div
            className={`${
              rightSidebarOpen ? 'w-80' : 'w-0'
            } transition-all duration-300 ease-in-out border-l bg-white overflow-hidden flex-shrink-0 ${
              isMobile && rightSidebarOpen ? 'fixed inset-y-14 right-0 z-50 w-80' : ''
            }`}
          >
            <ArtifactPanel />
          </div>
        )}

        {isMobile && (leftSidebarOpen || rightSidebarOpen) && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => {
              setLeftSidebarOpen(false);
              setRightSidebarOpen(false);
            }}
          />
        )}
      </div>
    </div>
  );
}