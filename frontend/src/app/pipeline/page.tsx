'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { prospectsService, Prospect } from '@/services/api';
import { 
  Search, 
  ChevronDown, 
  SlidersHorizontal, 
  Sparkles, 
  ShieldAlert, 
  Mail, 
  Phone, 
  User, 
  Activity,
  DollarSign,
  Users,
  Calendar,
  Loader2,
  RefreshCw
} from 'lucide-react';
import Link from 'next/link';

export default function PipelinePage() {
  const queryClient = useQueryClient();

  // Filters State
  const [search, setSearch] = useState('');
  const [minAssets, setMinAssets] = useState<number>(0);
  const [minParticipants, setMinParticipants] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState('All');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Advanced Filters
  const [providerFilter, setProviderFilter] = useState('All');
  const [administratorFilter, setAdministratorFilter] = useState('All');

  // Fetch prospects query
  const { data: prospects = [], isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['prospects', search, minAssets, minParticipants, statusFilter, providerFilter, administratorFilter],
    queryFn: () => prospectsService.getProspects({
      search: search || undefined,
      min_assets: minAssets || undefined,
      min_participants: minParticipants || undefined,
      status: statusFilter === 'All' ? undefined : statusFilter,
      provider: providerFilter === 'All' ? undefined : providerFilter,
      administrator: administratorFilter === 'All' ? undefined : administratorFilter
    }),
  });

  // Enrich prospect contact info mutation
  const enrichMutation = useMutation({
    mutationFn: (ein: string) => prospectsService.enrichProspect(ein),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prospects'] });
    }
  });

  // Update status mutation to fully wire prospectsService CRUD endpoints
  const statusMutation = useMutation({
    mutationFn: ({ ein, status, notes }: { ein: string; status: string; notes: string }) =>
      prospectsService.updateProspectStatus(ein, status, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prospects'] });
    }
  });

  // Calculate metrics
  const totalProspects = prospects.length;
  const totalAssets = prospects.reduce((sum, p) => sum + (p.total_assets || 0), 0);
  const meetingsSet = prospects.filter(p => p.status === 'Meeting Set').length;

  const formatCurrency = (val: number) => {
    if (!val) return '$0';
    if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${val.toLocaleString()}`;
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'Lead': 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
      'Researching': 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
      'Cold Called': 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
      'Meeting Set': 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      'Disqualified': 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
    };
    return styles[status] || 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
            Pipeline Workspace
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Enterprise corporate lead prospecting dashboard & fiduciary pipelines.
          </p>
        </div>

        <button 
          onClick={() => refetch()}
          disabled={isLoading || isRefetching}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-300 font-semibold text-xs transition-all duration-300 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefetching || isLoading ? 'animate-spin' : ''}`} />
          Force Reload
        </button>
      </div>

      {/* Metric Cards (Phase 3, Step 1) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Total Prospects */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Active Leads</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{totalProspects}</h3>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
              <Users className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            <span className="text-emerald-400 font-bold">100% compliant</span> with primary excel index.
          </div>
        </div>

        {/* Card 2: Total Assets */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Assets Under Advisement</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{formatCurrency(totalAssets)}</h3>
            </div>
            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
              <DollarSign className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            <span className="text-sky-400 font-bold">Avg {(totalAssets / (totalProspects || 1) / 1e6).toFixed(1)}M</span> asset size per filing.
          </div>
        </div>

        {/* Card 3: Meetings Set */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-emerald-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Meetings Scheduled</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{meetingsSet}</h3>
            </div>
            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
              <Calendar className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            <span className="text-emerald-400 font-bold">{((meetingsSet / (totalProspects || 1)) * 100).toFixed(0)}% conversion</span> rate from active leads.
          </div>
        </div>
      </div>

      {/* Live Search & Filtering Options */}
      <div className="bg-slate-900/25 border border-slate-800/60 p-6 rounded-2xl shadow-lg space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search bar */}
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search prospects by Employer, EIN, Broker, TPA..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
            />
          </div>

          {/* Min Assets */}
          <div className="w-full lg:w-48">
            <select
              value={minAssets}
              onChange={(e) => setMinAssets(Number(e.target.value))}
              className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
            >
              <option value={0}>Min Assets: Any</option>
              <option value={1000000}>$1M+ Assets</option>
              <option value={5000000}>$5M+ Assets (Schedule H)</option>
              <option value={10000000}>$10M+ Assets</option>
              <option value={50000000}>$50M+ Assets</option>
            </select>
          </div>

          {/* Min Participants */}
          <div className="w-full lg:w-48">
            <select
              value={minParticipants}
              onChange={(e) => setMinParticipants(Number(e.target.value))}
              className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
            >
              <option value={0}>Min Headcount: Any</option>
              <option value={100}>100+ Participants</option>
              <option value={500}>500+ Participants</option>
              <option value={1000}>1,000+ Participants</option>
              <option value={5000}>5,000+ Participants</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-full lg:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
            >
              <option value="All">Status: All</option>
              <option value="Lead">Lead</option>
              <option value="Researching">Researching</option>
              <option value="Cold Called">Cold Called</option>
              <option value="Meeting Set">Meeting Set</option>
              <option value="Disqualified">Disqualified</option>
            </select>
          </div>
        </div>

        {/* Advanced Filters Expand Toggle */}
        <div>
          <button 
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors cursor-pointer"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            {showAdvanced ? 'Hide Advanced Filters' : 'Show Advanced Filters'}
            <ChevronDown className={`h-3 w-3 transform transition-transform duration-300 ${showAdvanced ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Advanced Filter Content */}
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 animate-fadeIn">
            {/* Broker Provider */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Broker / Provider</label>
              <select
                value={providerFilter}
                onChange={(e) => setProviderFilter(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
              >
                <option value="All">All Providers</option>
                <option value="Vanguard">Vanguard</option>
                <option value="Fidelity">Fidelity Investments</option>
                <option value="Empower">Empower Retirement</option>
                <option value="ADP">ADP Inc.</option>
              </select>
            </div>

            {/* Administrator */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Plan Administrator (TPA)</label>
              <select
                value={administratorFilter}
                onChange={(e) => setAdministratorFilter(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
              >
                <option value="All">All Administrators</option>
                <option value="ADP">ADP LLC</option>
                <option value="Ascensus">Ascensus</option>
                <option value="Paychex">Paychex</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Interactive Table List (Phase 3, Step 2) */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl shadow-2xl overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
            <p className="text-slate-400 text-sm font-semibold animate-pulse">Scanning relational DB, unzipping datasets...</p>
          </div>
        ) : prospects.length === 0 ? (
          <div className="text-center py-20 px-4 space-y-3">
            <div className="h-12 w-12 rounded-full bg-slate-800/60 text-slate-500 flex items-center justify-center mx-auto">
              <Activity className="h-6 w-6" />
            </div>
            <h4 className="text-slate-300 font-bold text-lg">No prospects match filter criteria</h4>
            <p className="text-slate-500 text-xs max-w-sm mx-auto">
              Broaden your search or check if the backend sync is fully completed to populate DOL filings.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/50 border-b border-slate-800/80 text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  <th className="px-6 py-4.5">Employer & plan info</th>
                  <th className="px-6 py-4.5">Pipeline status</th>
                  <th className="px-6 py-4.5">Key provider (TPA)</th>
                  <th className="px-6 py-4.5 text-right">Plan assets</th>
                  <th className="px-6 py-4.5 text-right">Headcount</th>
                  <th className="px-6 py-4.5">Decision Maker Contact</th>
                  <th className="px-6 py-4.5 text-center">Fiduciary Audits</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-sm">
                {prospects.map((prospect) => (
                  <tr 
                    key={prospect.ein} 
                    className="hover:bg-slate-800/20 group transition-all duration-300 border-slate-800/40"
                  >
                    {/* Employer name & EIN */}
                    <td className="px-6 py-4.5 space-y-1">
                      <div className="font-bold text-white tracking-wide group-hover:text-blue-400 transition-colors">
                        {prospect.employer_name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        EIN: {prospect.ein.slice(0,2)}-{prospect.ein.slice(2)}
                      </div>
                    </td>

                    {/* Status Badge Dropdown */}
                    <td className="px-6 py-4.5">
                      <select
                        value={prospect.status || 'Lead'}
                        onChange={(e) => {
                          statusMutation.mutate({ 
                            ein: prospect.ein, 
                            status: e.target.value, 
                            notes: prospect.notes || '' 
                          });
                        }}
                        disabled={statusMutation.isPending && statusMutation.variables?.ein === prospect.ein}
                        className={`px-2 py-1.5 rounded-full text-xs font-bold tracking-wide shadow-sm bg-slate-950 border border-slate-800 cursor-pointer focus:outline-none focus:border-blue-500/50 transition-all ${getStatusBadge(prospect.status)}`}
                      >
                        <option value="Lead" className="bg-slate-950 text-blue-400">Lead</option>
                        <option value="Researching" className="bg-slate-950 text-purple-400">Researching</option>
                        <option value="Cold Called" className="bg-slate-950 text-amber-400">Cold Called</option>
                        <option value="Meeting Set" className="bg-slate-950 text-emerald-400">Meeting Set</option>
                        <option value="Disqualified" className="bg-slate-950 text-rose-400">Disqualified</option>
                      </select>
                    </td>

                    {/* Provider/Administrator */}
                    <td className="px-6 py-4.5 space-y-0.5">
                      <div className="font-semibold text-slate-300">{prospect.provider || 'Unspecified'}</div>
                      <div className="text-[10px] text-slate-500 truncate max-w-[150px]">
                        {prospect.administrator || 'TPA Missing'}
                      </div>
                    </td>

                    {/* Assets */}
                    <td className="px-6 py-4.5 text-right font-bold text-slate-200">
                      {formatCurrency(prospect.total_assets)}
                    </td>

                    {/* Headcount */}
                    <td className="px-6 py-4.5 text-right font-medium text-slate-400">
                      {prospect.participants ? prospect.participants.toLocaleString() : '0'}
                    </td>

                    {/* Decision maker Contact Enrichment */}
                    <td className="px-6 py-4.5">
                      {prospect.contact_name ? (
                        <div className="space-y-1 max-w-[200px]">
                          <div className="flex items-center gap-1.5 text-slate-300 font-semibold text-xs">
                            <User className="h-3 w-3 text-blue-400" />
                            {prospect.contact_name}
                          </div>
                          {prospect.contact_email && (
                            <div className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-slate-400 transition-colors truncate">
                              <Mail className="h-2.5 w-2.5 text-slate-500" />
                              {prospect.contact_email}
                            </div>
                          )}
                          {prospect.contact_phone && (
                            <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
                              <Phone className="h-2.5 w-2.5 text-slate-500" />
                              {prospect.contact_phone}
                            </div>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => enrichMutation.mutate(prospect.ein)}
                          disabled={enrichMutation.isPending && enrichMutation.variables === prospect.ein}
                          className="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-blue-600/10 to-indigo-600/10 hover:from-blue-600/20 hover:to-indigo-600/20 border border-blue-500/20 rounded-lg text-blue-400 font-semibold text-xs transition-all duration-300 cursor-pointer disabled:opacity-50"
                        >
                          {enrichMutation.isPending && enrichMutation.variables === prospect.ein ? (
                            <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
                          ) : (
                            <Sparkles className="h-3 w-3 text-blue-400 group-hover:animate-pulse" />
                          )}
                          Enrich Contact
                        </button>
                      )}
                    </td>

                    {/* Audit action link */}
                    <td className="px-6 py-4.5 text-center">
                      <Link
                        href={`/audits?ein=${prospect.ein}&name=${encodeURIComponent(prospect.employer_name)}`}
                        className="inline-flex items-center justify-center p-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-400 hover:text-red-400 hover:border-red-500/30 transition-all duration-300 shadow-md group-hover:scale-105"
                      >
                        <ShieldAlert className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
