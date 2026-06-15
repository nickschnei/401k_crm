'use client';

import React, { useState } from 'react';
import Sidebar from './Sidebar';
import ChatSidebar from './ChatSidebar';
import { Menu, X, Layers } from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const toggleMobileSidebar = () => {
    setIsMobileOpen((prev) => !prev);
  };

  const closeMobileSidebar = () => {
    setIsMobileOpen(false);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#020617] text-slate-100 font-sans">
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={closeMobileSidebar}
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
        />
      )}

      {/* Sidebar - Handles responsive classes internally via classes passed in or state */}
      <Sidebar
        className={`
          max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-50
          transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'max-lg:translate-x-0' : 'max-lg:-translate-x-full'}
          lg:translate-x-0 lg:flex
        `}
        mobileOpen={isMobileOpen}
        onClose={closeMobileSidebar}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {/* Mobile Header Bar */}
        <header className="lg:hidden flex items-center justify-between px-6 py-4 bg-[#0f172a]/70 backdrop-blur-xl border-b border-slate-800/80 z-30 select-none">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleMobileSidebar}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer"
              aria-label="Toggle Navigation Menu"
            >
              {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-sky-400 via-blue-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Layers className="h-4 w-4 text-white" />
              </div>
              <span className="font-extrabold text-sm tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Prospects CRM
              </span>
            </div>
          </div>
          
          <div className="text-[10px] bg-sky-500/10 text-sky-400 border border-sky-500/25 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
            CRM
          </div>
        </header>

        {/* Content Wrapper */}
        <main className="flex-1 h-full overflow-y-auto bg-[#020617] flex flex-col">
          {children}
        </main>
      </div>
      
      {/* Global Chat Copilot Panel */}
      <ChatSidebar />
    </div>
  );
}
