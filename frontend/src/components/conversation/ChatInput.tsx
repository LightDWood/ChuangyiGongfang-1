import { useState, useRef, useEffect, useCallback } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export default function ChatInput({
  onSend,
  disabled = false,
  loading = false,
  placeholder = '输入您的需求...',
  maxLength = 2000,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 40), 200);
      textarea.style.height = `${newHeight}px`;
    }
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [value, adjustHeight]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled || loading) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setValue('');
    textareaRef.current?.focus();
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-2 border rounded-lg bg-white p-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= maxLength) {
              setValue(e.target.value);
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || loading}
          className="flex-1 resize-none border-0 focus:outline-none min-h-[40px] max-h-[200px] py-1.5 text-sm disabled:bg-gray-50 disabled:cursor-not-allowed"
          style={{ height: 'auto' }}
          rows={1}
        />
        <div className="flex items-center gap-1 flex-shrink-0">
          {value.length > 0 && (
            <button
              onClick={handleClear}
              disabled={disabled || loading}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
              title="清空"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <button
            onClick={handleSubmit}
            disabled={!value.trim() || disabled || loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-1.5 text-sm font-medium"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>生成中</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <span>发送</span>
              </>
            )}
          </button>
        </div>
      </div>
      <div className="flex justify-between text-xs text-gray-400 px-1">
        <span>Enter 发送，Shift+Enter 换行</span>
        <span className={value.length > maxLength * 0.9 ? 'text-orange-500' : ''}>
          {value.length}/{maxLength}
        </span>
      </div>
    </div>
  );
}