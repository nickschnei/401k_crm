'use client';

import React, { Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/api';
import { 
  BarChart3, 
  TrendingUp, 
  PieChart, 
  Building2, 
  Activity, 
  ShieldAlert, 
  DollarSign, 
  Users, 
  CheckCircle2, 
  Calendar, 
  ArrowUpRight, 
  Loader2, 
  RefreshCw, 
  Briefcase, 
  Layers,
  CheckSquare,
  AlertTriangle,
  Bell
} from 'lucide-react';
import Link from 'next/link';

function AnalyticsContent() {
  const { data: analytics, isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => analyticsService.getSummary(),
  });

  const formatCurrency = (val?: number) => {
    if (!val) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(val);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
        <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm font-semibold animate-pulse">Aggregating CRM metrics & pipeline conversion funnels...</p>
      </div>
    );
  }

  const totalAssets = analytics?.total_assets || 0;
  const totalProspects = analytics?.total_prospects || 0;
  const conversionRate = analytics?.overall_conversion_rate || 0;
  const funnel = analytics?.funnel || [];
  const providers = analytics?.providers || [];
  const activities = analytics?.activities || [];
  const health = analytics?.followup_health || { overdue: 0, today: 0, upcoming: 0, completed: 0 };

  const totalTasks = health.overdue + health.today + health.upcoming + health.completed;
  const taskCompletionRate = totalTasks > 0 ? Math.round((health.completed / totalTasks) * 100) : 100;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Activity & Conversion Analytics
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Real-Time CRM Insights
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Track pipeline conversion funnels, provider displacement opportunities, and sales outreach velocity.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl font-bold text-xs transition-all shadow-sm cursor-pointer self-start md:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefetching ? 'animate-spin text-blue-400' : ''}`} />
          {isRefetching ? 'Refreshing...' : 'Refresh Metrics'}
        </button>
      </div>

      {/* Top Metric Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl space-y-2 shadow-xl relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Pipeline Value</span>
            <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400">
              <DollarSign className="h-5 w-5" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-white tracking-tight">{formatCurrency(totalAssets)}</p>
          <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
            <Building2 className="h-3 w-3 text-slate-400" />
            {totalProspects} Total Corporate Accounts
          </span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl space-y-2 shadow-xl relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Meeting Conversion Rate</span>
            <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-400">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 tracking-tight">{conversionRate}%</p>
          <span className="text-[11px] text-slate-500 font-medium">
            Lead to Meeting Set Conversion Ratio
          </span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl space-y-2 shadow-xl relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Logged Outreach Activities</span>
            <div className="p-2.5 bg-purple-500/10 rounded-xl text-purple-400">
              <Activity className="h-5 w-5" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-white tracking-tight">
            {activities.reduce((acc, curr) => acc + curr.count, 0)}
          </p>
          <span className="text-[11px] text-slate-500 font-medium">
            Total Calls, Emails, Meetings & Notes
          </span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl space-y-2 shadow-xl relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Task Completion Health</span>
            <div className="p-2.5 bg-amber-500/10 rounded-xl text-amber-400">
              <CheckSquare className="h-5 w-5" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-amber-400 tracking-tight">{taskCompletionRate}%</p>
          <span className="text-[11px] text-slate-500 font-medium">
            {health.completed} of {totalTasks} Follow-ups Completed
          </span>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Pipeline Conversion Funnel */}
        <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-400" />
                Pipeline Stage Conversion Funnel
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Volume of corporate 401(k) prospects and total assets at each stage of outreach.
              </p>
            </div>

            <Link
              href="/pipeline"
              className="text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              Manage Pipeline →
            </Link>
          </div>

          <div className="space-y-4">
            {funnel.map((item) => (
              <div key={item.stage} className="space-y-1.5 p-3.5 bg-slate-950/60 border border-slate-800/60 rounded-xl">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-white text-sm">{item.stage}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                      {item.count} Prospects
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-200">{formatCurrency(item.total_assets)}</span>
                    <span className="font-extrabold text-blue-400 font-mono w-12 text-right">{item.percentage}%</span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${
                      item.stage === 'Meeting Set' 
                        ? 'bg-emerald-500' 
                        : item.stage === 'Cold Called'
                        ? 'bg-amber-500'
                        : item.stage === 'Researching'
                        ? 'bg-purple-500'
                        : item.stage === 'Disqualified'
                        ? 'bg-rose-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.max(item.percentage, 4)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Follow-up Task Velocity Widget */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="border-b border-slate-800/60 pb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Bell className="h-5 w-5 text-amber-400" />
              Follow-Up Task Health
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live status breakdown of scheduled follow-ups.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-1">
              <span className="text-[10px] font-extrabold text-rose-400 uppercase tracking-wider">Overdue Tasks</span>
              <p className="text-2xl font-extrabold text-rose-300">{health.overdue}</p>
            </div>
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-1">
              <span className="text-[10px] font-extrabold text-amber-400 uppercase tracking-wider">Due Today</span>
              <p className="text-2xl font-extrabold text-amber-300">{health.today}</p>
            </div>
            <div className="p-3.5 bg-blue-500/10 border border-blue-500/30 rounded-xl space-y-1">
              <span className="text-[10px] font-extrabold text-blue-400 uppercase tracking-wider">Upcoming</span>
              <p className="text-2xl font-extrabold text-blue-300">{health.upcoming}</p>
            </div>
            <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-1">
              <span className="text-[10px] font-extrabold text-emerald-400 uppercase tracking-wider">Completed</span>
              <p className="text-2xl font-extrabold text-emerald-300">{health.completed}</p>
            </div>
          </div>

          {/* Activity Type Breakdown */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider">
              Outreach Channel Distribution
            </h4>
            <div className="space-y-2">
              {activities.map((act) => (
                <div key={act.interaction_type} className="flex items-center justify-between p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs">
                  <span className="font-bold text-slate-300">
                    {act.interaction_type === 'Call' && '📞 Call'}
                    {act.interaction_type === 'Email' && '✉️ Email'}
                    {act.interaction_type === 'Meeting' && '🤝 Meeting'}
                    {act.interaction_type === 'Note' && '📝 Note'}
                  </span>
                  <span className="font-mono font-bold text-white bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {act.count} Logged
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recordkeeper Displacement Matrix */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Building2 className="h-5 w-5 text-purple-400" />
            Top Incumbent Recordkeeper Displacement Opportunities
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Key provider breakdown across your pipeline, highlighting fee drag and fiduciary audit red flags.
          </p>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-950/60 border-b border-slate-800/80 text-[10px] uppercase font-bold tracking-wider text-slate-400">
                <th className="px-5 py-3.5">Recordkeeper / Provider</th>
                <th className="px-5 py-3.5 text-center">Prospect Count</th>
                <th className="px-5 py-3.5 text-right">Total Assets Under Management</th>
                <th className="px-5 py-3.5 text-center">Fiduciary Audit Red Flags</th>
                <th className="px-5 py-3.5 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-xs">
              {providers.map((prov) => (
                <tr key={prov.provider} className="hover:bg-slate-800/20 transition-colors">
                  <td className="px-5 py-3.5 font-bold text-white">
                    {prov.provider}
                  </td>
                  <td className="px-5 py-3.5 text-center font-bold text-slate-300">
                    {prov.count}
                  </td>
                  <td className="px-5 py-3.5 text-right font-bold text-slate-200">
                    {formatCurrency(prov.total_assets)}
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    {prov.red_flag_count > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-rose-500/10 border border-rose-500/30 text-rose-300 font-bold rounded-full text-[10px]">
                        <ShieldAlert className="h-3 w-3 text-rose-400" />
                        {prov.red_flag_count} Plans Flagged
                      </span>
                    ) : (
                      <span className="text-slate-500">None</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <Link
                      href={`/pipeline`}
                      className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 font-bold rounded-lg text-[10px] transition-all"
                    >
                      View Plans →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    }>
      <AnalyticsContent />
    </Suspense>
  );
}
