'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { discoveryService, DiscoveryFiling } from '@/services/api';
import { 
  Search, 
  ChevronDown, 
  SlidersHorizontal, 
  Activity,
  DollarSign,
  Users,
  Loader2,
  RefreshCw,
  TrendingUp,
  MapPin,
  ShieldAlert,
  Play,
  CheckCircle,
  AlertCircle,
  Database
} from 'lucide-react';
import Link from 'next/link';

export default function DiscoveryPage() {
  const queryClient = useQueryClient();

  // Filters State
  const [search, setSearch] = useState('');
  const [minAssets, setMinAssets] = useState<number>(0);
  const [minParticipants, setMinParticipants] = useState<number>(0);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Advanced Filters
  const [providerFilter, setProviderFilter] = useState('All');
  const [administratorFilter, setAdministratorFilter] = useState('All');

  // Fetch Celery sync status
  const { data: syncStatus, refetch: refetchSyncStatus } = useQuery({
    queryKey: ['discovery-sync-status'],
    queryFn: () => discoveryService.getSyncStatus(),
    refetchInterval: (query) => {
      // Auto-poll status every 3 seconds if background celery worker is active
      const data = query.state.data;
      return data?.is_running ? 3000 : false;
    }
  });

  // Trigger sync Celery worker task mutation
  const syncMutation = useMutation({
    mutationFn: () => discoveryService.triggerSync(),
    onSuccess: () => {
      refetchSyncStatus();
      queryClient.invalidateQueries({ queryKey: ['discovery-filings'] });
    }
  });

  // Query filings
  const { data: filings = [], isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['discovery-filings', search, minAssets, minParticipants, providerFilter, administratorFilter],
    queryFn: () => discoveryService.getFilings({
      search: search || undefined,
      min_assets: minAssets || undefined,
      min_participants: minParticipants || undefined,
      provider: providerFilter === 'All' ? undefined : providerFilter,
      administrator: administratorFilter === 'All' ? undefined : administratorFilter
    }),
  });

  // Calculate metrics
  const filingsCount = filings.length;
  const filingsVolume = filings.reduce((sum, f) => sum + (f.total_assets || 0), 0);
  const avgParticipants = filingsCount > 0 
    ? filings.reduce((sum, f) => sum + (f.participants || 0), 0) / filingsCount
    : 0;

  const formatCurrency = (val: number) => {
    if (!val) return '$0';
    if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${val.toLocaleString()}`;
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
            DOL Registry Discovery
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Search and segment the complete raw Department of Labor Form 5500 database universe.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => refetch()}
            disabled={isLoading || isRefetching}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-300 font-semibold text-xs transition-all duration-300 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefetching || isLoading ? 'animate-spin' : ''}`} />
            Force Reload
          </button>
        </div>
      </div>



      {/* Metrics (Phase 3, Step 3) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metric 1 */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Indexed DOL Filings</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{filingsCount}</h3>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400 animate-pulse">
              <Activity className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            Scanning active registry node in SQLite.
          </div>
        </div>

        {/* Metric 2 */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Filings Asset Volume</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{formatCurrency(filingsVolume)}</h3>
            </div>
            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
              <DollarSign className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            Total capital size analyzed under Fiduciary Act.
          </div>
        </div>

        {/* Metric 3 */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-sky-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-sky-500/5 rounded-full blur-2xl group-hover:bg-sky-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Average Participants Size</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{avgParticipants.toLocaleString(undefined, { maximumFractionDigits: 0 })}</h3>
            </div>
            <div className="p-3 bg-sky-500/10 rounded-xl text-sky-400">
              <Users className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
            Average employee headcount coverage per filing.
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/25 border border-slate-800/60 p-6 rounded-2xl shadow-lg space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search complete registries by corporate sponsor, ZIP, city, state, administrator..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
            />
          </div>

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
        </div>

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

        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 animate-fadeIn">
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
              </select>
            </div>

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

      {/* Discovery Filings List */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl shadow-2xl overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
            <p className="text-slate-400 text-sm font-semibold animate-pulse">Scanning relational DB, unzipping datasets...</p>
          </div>
        ) : filings.length === 0 ? (
          <div className="text-center py-20 px-4 space-y-3">
            <div className="h-12 w-12 rounded-full bg-slate-800/60 text-slate-500 flex items-center justify-center mx-auto">
              <Activity className="h-6 w-6" />
            </div>
            <h4 className="text-slate-300 font-bold text-lg">No raw filings found</h4>
            <p className="text-slate-500 text-xs max-w-sm mx-auto">
              Make sure to trigger the SQLite sync operation first or broaden your filtering options.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/50 border-b border-slate-800/80 text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  <th className="px-6 py-4.5">Employer Sponsor info</th>
                  <th className="px-6 py-4.5">Primary Plan Name</th>
                  <th className="px-6 py-4.5 text-right">Plan assets</th>
                  <th className="px-6 py-4.5 text-right">Participants</th>
                  <th className="px-6 py-4.5">Geographic Location</th>
                  <th className="px-6 py-4.5">Administrator</th>
                  <th className="px-6 py-4.5 text-center">Diagnostics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-sm">
                {filings.map((filing) => (
                  <tr 
                    key={filing.ein} 
                    className="hover:bg-slate-800/20 group transition-all duration-300 border-slate-800/40"
                  >
                    {/* Sponsor & EIN */}
                    <td className="px-6 py-4.5 space-y-1">
                      <div className="font-bold text-white tracking-wide group-hover:text-blue-400 transition-colors">
                        {filing.employer_name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        EIN: {filing.ein.slice(0,2)}-{filing.ein.slice(2)}
                      </div>
                    </td>

                    {/* Plan name */}
                    <td className="px-6 py-4.5">
                      <div className="font-medium text-slate-300 max-w-[200px] truncate">
                        {filing.plan_name || '401(k) Savings Plan'}
                      </div>
                    </td>

                    {/* Assets */}
                    <td className="px-6 py-4.5 text-right font-bold text-slate-200">
                      {formatCurrency(filing.total_assets)}
                    </td>

                    {/* Headcount */}
                    <td className="px-6 py-4.5 text-right font-medium text-slate-400">
                      {filing.participants ? filing.participants.toLocaleString() : '0'}
                    </td>

                    {/* Location */}
                    <td className="px-6 py-4.5 space-y-0.5">
                      <div className="flex items-center gap-1 text-slate-300 font-semibold text-xs">
                        <MapPin className="h-3 w-3 text-sky-400" />
                        {filing.dol_city || 'City'}, {filing.dol_state || 'State'}
                      </div>
                      <div className="text-[10px] text-slate-500 max-w-[150px] truncate pl-4">
                        {filing.dol_address}
                      </div>
                    </td>

                    {/* Administrator */}
                    <td className="px-6 py-4.5">
                      <div className="text-xs text-slate-400 max-w-[150px] truncate font-medium">
                        {filing.administrator || 'TPA Missing'}
                      </div>
                    </td>

                    {/* Fiduciary Diagnostics button */}
                    <td className="px-6 py-4.5 text-center">
                      <Link
                        href={`/audits?ein=${filing.ein}&name=${encodeURIComponent(filing.employer_name)}`}
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
