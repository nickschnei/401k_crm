'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Briefcase, 
  Search, 
  ShieldAlert, 
  CreditCard, 
  Activity,
  Layers,
  LogOut,
  ChevronDown,
  MapPin,
  FileText
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { authService } from '@/services/api';
import { useRouter } from 'next/navigation';

interface SidebarProps {
  className?: string;
  mobileOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ className = '', mobileOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [width, setWidth] = React.useState(280);
  const [showBillingMenu, setShowBillingMenu] = React.useState(false);
  const isResizing = React.useRef(false);

  const startResizing = React.useCallback((mouseDownEvent: React.MouseEvent) => {
    isResizing.current = true;
    
    const startX = mouseDownEvent.clientX;
    const startWidth = width;

    const doDrag = (mouseMoveEvent: MouseEvent) => {
      if (!isResizing.current) return;
      const newWidth = startWidth + (mouseMoveEvent.clientX - startX);
      if (newWidth >= 200 && newWidth <= 480) {
        setWidth(newWidth);
      }
    };

    const stopDrag = () => {
      isResizing.current = false;
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  }, [width]);

  const { data: user } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authService.me(),
    retry: false,
  });

  const handleLogout = () => {
    // Clear session cookie
    document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push('/login');
    router.refresh();
  };

  if (pathname === '/login') return null;

  const menuItems = [
    { 
      name: 'Pipeline', 
      href: '/pipeline', 
      icon: Briefcase,
      description: 'Prospect CRM flow'
    },
    { 
      name: 'Discovery', 
      href: '/discovery', 
      icon: Search,
      description: 'DOL Filing Search'
    },
    { 
      name: 'Audits', 
      href: '/audits', 
      icon: ShieldAlert,
      description: 'Fiduciary Diagnostics'
    },
    { 
      name: 'Trip Planner', 
      href: '/planner', 
      icon: MapPin,
      description: 'Optimal Route Planner'
    },
  ];

  return (
    <div 
      style={{ '--sidebar-width': `${width}px` } as React.CSSProperties}
      className={`relative w-[280px] lg:w-[var(--sidebar-width)] bg-[#0f172a]/70 backdrop-blur-xl border-r border-slate-800 flex flex-col h-screen text-slate-200 select-none ${className}`}
    >
      {/* Resize Drag Handle */}
      <div 
        onMouseDown={startResizing}
        className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-blue-500/50 active:bg-blue-500 transition-colors z-50 select-none hidden lg:block"
      />

      {/* Title / Brand Header */}
      <div className="p-6 border-b border-slate-800/60 flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-400 via-blue-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Layers className="h-5 w-5 text-white animate-pulse" />
        </div>
        <div>
          <h1 className="font-extrabold text-lg bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
            Prospects CRM
          </h1>
          <p className="text-[10px] text-sky-400 font-semibold uppercase tracking-wider">
            401(k) Suite
          </p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href) || (pathname === '/' && item.href === '/pipeline');
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={onClose}
              className={`group flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600/20 to-indigo-600/10 border border-blue-500/30 text-white shadow-inner shadow-blue-500/5'
                  : 'hover:bg-slate-800/40 border border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className={`p-2 rounded-lg transition-all duration-300 ${
                isActive 
                  ? 'bg-blue-500 text-white shadow-md shadow-blue-500/20' 
                  : 'bg-slate-800/40 text-slate-400 group-hover:text-slate-200 group-hover:bg-slate-800/80'
              }`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-sm tracking-wide">
                  {item.name}
                </span>
                <span className="text-[10px] text-slate-500 group-hover:text-slate-400 transition-colors">
                  {item.description}
                </span>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Footer / Advisor Status Indicator */}
      <div className="p-4 border-t border-slate-800/60 bg-slate-900/30 space-y-3">
        {/* Clickable Billing Popover Menu */}
        {showBillingMenu && (
          <div className="absolute bottom-[136px] left-4 right-4 bg-[#090d16] border border-slate-800 p-4 rounded-xl shadow-2xl z-50 flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <div className="flex items-center justify-between border-b border-slate-850 pb-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                Billing Account
              </span>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold animate-pulse">
                PRO Active
              </span>
            </div>
            <Link
              href="/billing"
              onClick={() => {
                setShowBillingMenu(false);
                if (onClose) onClose();
              }}
              className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-900/50 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/30 text-slate-300 hover:text-white transition-all duration-300"
            >
              <CreditCard className="h-4 w-4 text-blue-400 animate-pulse" />
              <div className="flex flex-col">
                <span className="text-xs font-bold">Billing Dashboard</span>
                <span className="text-[9px] text-slate-500">Manage invoices & plans</span>
              </div>
            </Link>
          </div>
        )}

        <div 
          onClick={() => setShowBillingMenu(!showBillingMenu)}
          className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:bg-slate-900/40 active:scale-[0.98] transition-all flex flex-col gap-2 cursor-pointer group/footer"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 group-hover/footer:text-blue-400 transition-colors">
              Advisor Session
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-full font-semibold group-hover/footer:border-blue-500/20 transition-all">
                Online
              </span>
              <ChevronDown className={`h-3 w-3 text-slate-500 transition-transform duration-300 ${showBillingMenu ? 'rotate-180 text-blue-400' : ''}`} />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Activity className="h-4 w-4 text-emerald-400" />
            <div className="flex flex-col">
              <span className="text-xs font-bold text-slate-300 group-hover/footer:text-white transition-colors">
                {user?.first_name ? `${user.first_name} ${user.last_name}` : 'SaaS Enterprise Node'}
              </span>
              <span className="text-[9px] text-slate-500 truncate max-w-[150px]">
                {user?.email || 'Connected · 8000/api/v1'}
              </span>
            </div>
          </div>
        </div>

        {/* Logout Trigger */}
        <button
          onClick={() => {
            handleLogout();
            if (onClose) onClose();
          }}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/5 border border-transparent hover:border-rose-500/10 transition-all duration-300 font-semibold text-xs cursor-pointer"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out Session</span>
        </button>
      </div>
    </div>
  );
}
