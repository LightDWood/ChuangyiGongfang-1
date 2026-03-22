import { useEffect, useState } from 'react';
import { useSessionStore } from '../../stores';
import { artifactService } from '../../services/api';
import type { Artifact } from '../../types';

export default function ArtifactPanel() {
  const { currentSession } = useSessionStore();
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedArtifact, setExpandedArtifact] = useState<string | null>(null);

  useEffect(() => {
    if (currentSession) {
      setLoading(true);
      artifactService
        .list(currentSession.id)
        .then(setArtifacts)
        .catch((err) => console.error('Failed to load artifacts:', err))
        .finally(() => setLoading(false));
    } else {
      setArtifacts([]);
      setSelectedArtifact(null);
    }
  }, [currentSession]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('确定删除此产物吗？')) return;
    try {
      await artifactService.delete(id);
      setArtifacts(artifacts.filter((a) => a.id !== id));
      if (selectedArtifact?.id === id) {
        setSelectedArtifact(null);
      }
    } catch (err) {
      console.error('Failed to delete artifact:', err);
    }
  };

  const handleDownload = (artifact: Artifact) => {
    const blob = new Blob([artifact.content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.replace(/\s+/g, '_')}_v${artifact.version}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      requirement: '需求',
      specification: '规格说明',
      code: '代码',
      document: '文档',
    };
    return labels[type] || type;
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      requirement: 'bg-purple-100 text-purple-700',
      specification: 'bg-blue-100 text-blue-700',
      code: 'bg-green-100 text-green-700',
      document: 'bg-orange-100 text-orange-700',
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-700 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            产物列表
          </h2>
          {artifacts.length > 0 && (
            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
              {artifacts.length}
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <svg className="w-8 h-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        ) : artifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4">
            <svg className="w-12 h-12 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm text-center">暂无产物</p>
            <p className="text-xs mt-1 text-center">对话过程中将自动生成</p>
          </div>
        ) : (
          artifacts.map((artifact) => (
            <div
              key={artifact.id}
              onClick={() => setSelectedArtifact(artifact)}
              className={`border-b cursor-pointer transition group ${
                selectedArtifact?.id === artifact.id
                  ? 'bg-blue-50 border-l-4 border-l-blue-500'
                  : 'hover:bg-gray-50 border-l-4 border-l-transparent'
              }`}
            >
              <div className="p-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm truncate text-gray-800">{artifact.title}</p>
                      <span className={`text-xs px-2 py-0.5 rounded ${getTypeColor(artifact.type)}`}>
                        {getTypeLabel(artifact.type)}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        v{artifact.version}
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDate(artifact.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                  {artifact.content.slice(0, 120)}
                  {artifact.content.length > 120 ? '...' : ''}
                </p>

                <div className="flex items-center gap-2 mt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedArtifact(expandedArtifact === artifact.id ? null : artifact.id);
                    }}
                    className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"
                  >
                    {expandedArtifact === artifact.id ? '收起' : '展开'}
                    <svg
                      className={`w-3 h-3 transition-transform ${expandedArtifact === artifact.id ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(artifact);
                    }}
                    className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    下载
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, artifact.id)}
                    className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    删除
                  </button>
                </div>

                {expandedArtifact === artifact.id && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <pre className="text-xs whitespace-pre-wrap text-gray-600 max-h-64 overflow-y-auto">
                      {artifact.content}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {selectedArtifact && (
        <div className="border-t bg-gray-50 p-3 max-h-48 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-sm text-gray-700">{selectedArtifact.title}</h3>
            <button
              onClick={() => setSelectedArtifact(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <pre className="text-xs bg-white p-2 rounded border border-gray-200 whitespace-pre-wrap text-gray-600">
            {selectedArtifact.content}
          </pre>
        </div>
      )}
    </div>
  );
}