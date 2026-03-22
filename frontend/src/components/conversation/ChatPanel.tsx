import { useState, useRef, useEffect, useCallback } from 'react';
import { useSessionStore } from '../../stores';
import { messageService } from '../../services/api';
import type { Message, StreamChunk } from '../../types';
import ChatInput from './ChatInput';

interface StreamingMessage {
  id: string;
  session_id: string;
  role: 'assistant';
  content: string;
  artifacts: never[];
  created_at: string;
}

export default function ChatPanel() {
  const { currentSession, messages, addMessage } = useSessionStore();
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSend = async (content: string) => {
    if (!currentSession || streaming) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      session_id: currentSession.id,
      role: 'user',
      content,
      artifacts: [],
      created_at: new Date().toISOString(),
    };
    addMessage(userMessage);
    setStreaming(true);
    setStreamingContent('');

    try {
      const eventSource = messageService.stream(currentSession.id, content);
      eventSourceRef.current = eventSource;

      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantMessage: StreamingMessage = {
        id: assistantMessageId,
        session_id: currentSession.id,
        role: 'assistant',
        content: '',
        artifacts: [],
        created_at: new Date().toISOString(),
      };

      const handleToken = (data: StreamChunk) => {
        setStreamingContent((prev) => prev + data.content);
      };

      const handleArtifact = (data: StreamChunk) => {
        if (data.artifact) {
          const artifactMessage: Message = {
            id: `artifact-${Date.now()}`,
            session_id: currentSession.id,
            role: 'assistant',
            content: `生成了产物: ${data.artifact.title}`,
            artifacts: [data.artifact],
            created_at: new Date().toISOString(),
          };
          addMessage(artifactMessage);
        }
      };

      const handleThinking = (data: StreamChunk) => {
        if (data.content) {
          setStreamingContent((prev) => prev + data.content + '\n');
        }
      };

      const handleAmbiguity = (data: StreamChunk) => {
        if (data.points) {
          setStreamingContent((prev) => prev + `发现歧义点: ${data.points!.join(', ')}\n`);
        }
      };

      const handleDone = () => {
        eventSource.close();
        eventSourceRef.current = null;
        if (streamingContent) {
          const finalMessage: Message = {
            id: assistantMessageId,
            session_id: currentSession.id,
            role: 'assistant',
            content: streamingContent,
            artifacts: [],
            created_at: assistantMessage.created_at,
          };
          addMessage(finalMessage);
          setStreamingContent('');
        }
        setStreaming(false);
      };

      eventSource.addEventListener('token', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleToken(data);
        } catch (parseError) {
          console.error('Failed to parse token data:', parseError);
        }
      });

      eventSource.addEventListener('artifact', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleArtifact(data);
        } catch (parseError) {
          console.error('Failed to parse artifact data:', parseError);
        }
      });

      eventSource.addEventListener('thinking', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleThinking(data);
        } catch (parseError) {
          console.error('Failed to parse thinking data:', parseError);
        }
      });

      eventSource.addEventListener('requirement_identified', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleThinking(data);
        } catch (parseError) {
          console.error('Failed to parse requirement_identified data:', parseError);
        }
      });

      eventSource.addEventListener('questions_ready', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleThinking(data);
        } catch (parseError) {
          console.error('Failed to parse questions_ready data:', parseError);
        }
      });

      eventSource.addEventListener('options_ready', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleThinking(data);
        } catch (parseError) {
          console.error('Failed to parse options_ready data:', parseError);
        }
      });

      eventSource.addEventListener('ambiguity_detected', (event) => {
        try {
          const data: StreamChunk = JSON.parse((event as MessageEvent).data);
          handleAmbiguity(data);
        } catch (parseError) {
          console.error('Failed to parse ambiguity_detected data:', parseError);
        }
      });

      eventSource.addEventListener('done', () => {
        handleDone();
      });

      eventSource.onerror = () => {
        eventSource.close();
        eventSourceRef.current = null;
        setStreaming(false);
        if (streamingContent) {
          const finalMessage: Message = {
            id: assistantMessageId,
            session_id: currentSession.id,
            role: 'assistant',
            content: streamingContent,
            artifacts: [],
            created_at: assistantMessage.created_at,
          };
          addMessage(finalMessage);
          setStreamingContent('');
        }
      };
    } catch (error) {
      console.error('Failed to send message:', error);
      setStreaming(false);
      setStreamingContent('');
    }
  };

  const handleClearChat = () => {
    if (window.confirm('确定清空当前会话的所有消息吗？')) {
      useSessionStore.setState({ messages: [] });
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !streamingContent && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-center">开始与智能体对话</p>
            <p className="text-sm mt-2 text-center max-w-md">
              描述您的需求，智能体将帮助您分析和收敛需求
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white rounded-br-md'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md'
              }`}
            >
              <div className="flex items-start gap-2">
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  {msg.artifacts?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-2">
                        <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        包含 {msg.artifacts?.length} 个产物
                      </p>
                      {msg.artifacts.map((artifact) => (
                        <div key={artifact.id} className="bg-gray-50 rounded-lg p-2 text-xs">
                          <p className="font-medium text-gray-700">{artifact.title}</p>
                          <p className="text-gray-500 truncate mt-1">{artifact.content.slice(0, 100)}...</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <p className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'} text-right`}>
                {new Date(msg.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-2xl px-4 py-3 shadow-sm bg-white border border-gray-200 rounded-bl-md">
              <div className="flex items-start gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{streamingContent}</p>
                  <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
                </div>
              </div>
            </div>
          </div>
        )}

        {streaming && !streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-2xl px-4 py-3 shadow-sm bg-white border border-gray-200 rounded-bl-md">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
                <p className="text-sm text-gray-500">智能体正在思考...</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t bg-white">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={handleClearChat}
            disabled={messages.length === 0}
            className="text-xs text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            清空对话
          </button>
          <span className="text-xs text-gray-400">
            {currentSession?.title || '未选择会话'}
          </span>
        </div>
        <ChatInput
          onSend={handleSend}
          disabled={!currentSession}
          loading={streaming}
          placeholder={currentSession ? '输入您的需求...' : '请先选择或创建会话'}
        />
      </div>
    </div>
  );
}