'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Sparkles, Trash2, ShieldAlert, Loader2 } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  isError?: boolean;
}

const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
};

export default function ChatSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'agent',
      text: 'Hello! I am your 401(k) and ERISA compliance copilot. Ask me questions about Form 5500 filing schedules, compliance dates, fiduciary red flags, or plan auditing rules.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const promptText = input.trim();
    if (!promptText || isLoading) return;

    setInput('');
    setIsLoading(true);

    const userMessageId = Math.random().toString();
    const newUserMessage: Message = {
      id: userMessageId,
      sender: 'user',
      text: promptText,
    };

    setMessages((prev) => [...prev, newUserMessage]);

    const assistantMsgId = Math.random().toString();

    try {
      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getCookie('auth_token') || ''}`,
        },
        body: JSON.stringify({ prompt: promptText }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to get response');
      }

      // Add placeholder agent message
      setMessages((prev) => [
        ...prev,
        { id: assistantMsgId, sender: 'agent', text: '' },
      ]);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error('Response stream reader not available.');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, text: msg.text + chunk }
              : msg
          )
        );
      }
    } catch (err: any) {
      // Clean up empty placeholder assistant message if it exists
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId));
      
      // Inject error notification bubble
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          sender: 'agent',
          text: err.message || 'An unexpected error occurred during connection.',
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'agent',
        text: 'Hello! I am your 401(k) and ERISA compliance copilot. Ask me questions about Form 5500 filing schedules, compliance dates, fiduciary red flags, or plan auditing rules.',
      },
    ]);
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white flex items-center justify-center shadow-2xl shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105 active:scale-95 transition-all duration-300 z-50 cursor-pointer border border-indigo-400/25"
        aria-label="Toggle Copilot Chat"
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6 animate-pulse" />}
      </button>

      {/* Slide-out Sidebar Panel */}
      <div
        className={`fixed inset-y-0 right-0 w-[420px] max-w-[calc(100vw-1rem)] bg-[#0b1329]/95 backdrop-blur-2xl border-l border-slate-800/80 shadow-2xl z-45 flex flex-col transition-all duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header Section */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-md">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-white tracking-wide">
                ERISA Copilot
              </h2>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  Compliance Agent
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={clearHistory}
              title="Clear chat history"
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/50 transition-colors cursor-pointer"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 select-text">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            
            if (msg.isError) {
              return (
                <div key={msg.id} className="flex flex-col items-center justify-center p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs gap-2 select-text">
                  <ShieldAlert className="h-4 w-4 text-rose-400" />
                  <p className="text-center font-semibold leading-relaxed">
                    {msg.text}
                  </p>
                </div>
              );
            }

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`px-4 py-2.5 rounded-2xl max-w-[85%] text-sm leading-relaxed whitespace-pre-wrap select-text ${
                    isUser
                      ? 'bg-gradient-to-r from-blue-600/80 to-indigo-600/80 border border-blue-500/20 text-white rounded-tr-none shadow-md shadow-indigo-500/5'
                      : 'bg-slate-900 border border-slate-800/80 text-slate-100 rounded-tl-none'
                  }`}
                >
                  {msg.text || (
                    <span className="flex items-center gap-1.5 text-slate-500 font-semibold text-xs animate-pulse">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                      Analyzing...
                    </span>
                  )}
                </div>
                <span className="text-[9px] text-slate-500 mt-1 px-1 font-bold uppercase tracking-wider">
                  {isUser ? 'You' : 'Copilot'}
                </span>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={handleSend}
          className="p-4 border-t border-slate-800/80 bg-slate-900/20"
        >
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Ask about Form 5500, vesting, compliance..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700/80 focus:border-indigo-500/50 rounded-xl py-3 pl-4 pr-12 text-sm text-slate-200 placeholder-slate-500 focus:outline-none transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 active:scale-95 transition-all disabled:opacity-50 disabled:bg-slate-800 disabled:text-slate-500 cursor-pointer"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 px-1 font-semibold uppercase tracking-wider select-none">
            <span>Enterprise Guard Active</span>
            <span>gemini-3.5-flash</span>
          </div>
        </form>
      </div>
    </>
  );
}
