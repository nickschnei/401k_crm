'use client';

import React, { useState, Suspense } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { prospectsService, auditsService, Prospect } from '@/services/api';
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
  RefreshCw,
  FileText,
  Download,
  Layers,
  Building2,
  FileArchive,
  Upload,
  Check,
  X,
  CheckSquare,
  Square
} from 'lucide-react';
import Link from 'next/link';
import ProspectDrawer from '@/components/ProspectDrawer';

function PipelineContent() {
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

  // Prospect Drawer State
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Bulk Selection & CSV State
  const [selectedEins, setSelectedEins] = useState<string[]>([]);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);

  // Bulk Status Update Mutation
  const bulkStatusMutation = useMutation({
    mutationFn: ({ status }: { status: string }) =>
      prospectsService.bulkUpdateStatus(selectedEins, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prospects'] });
      setSelectedEins([]);
    },
  });

  const handleOpenDrawer = (prospect: Prospect) => {
    setSelectedProspect(prospect);
    setIsDrawerOpen(true);
  };

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

  // Build ZIP download url for all matching prospects
  const getBatchZipUrl = () => {
    const activeEins = prospects.map(p => p.ein);
    return auditsService.getBatchReportsZipUrl(activeEins);
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 border-b border-slate-850 pb-6">
        <div className="space-y-4 flex-1">
          <div>
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
              Pipeline Workspace
            </h2>
            <p className="text-slate-400 text-sm mt-1">
              Enterprise corporate lead prospecting dashboard & fiduciary pipelines.
            </p>
          </div>

          {/* Prominent Middle-Left Download All Button */}
          <div className="pt-2">
            {prospects.length > 0 ? (
              <a
                href={getBatchZipUrl()}
                download
                className="inline-flex items-center gap-2.5 px-6 py-4 bg-gradient-to-r from-red-650 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-extrabold text-sm rounded-xl transition-all duration-300 shadow-xl shadow-red-600/30 hover:shadow-red-600/50 cursor-pointer border border-red-500/40 active:scale-95"
                title="Download branded Fiduciary Diagnostic PDF reports for all filtered plans in a single ZIP package"
              >
                <FileArchive className="h-5 w-5 text-red-200" />
                Download All Branded PDFs (.zip)
              </a>
            ) : (
              <button
                disabled
                className="inline-flex items-center gap-2.5 px-6 py-4 bg-slate-900 border border-slate-800 text-slate-500 font-extrabold text-sm rounded-xl cursor-not-allowed opacity-50"
              >
                <FileArchive className="h-5 w-5" />
                Download All Branded PDFs (.zip)
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 font-bold text-xs rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <Upload className="h-4 w-4" />
              Import CSV
            </button>

            <a
              href={prospectsService.getCsvExportUrl()}
              download
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-bold text-xs rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </a>

            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl font-bold text-xs transition-all shadow-sm cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin text-blue-400' : ''}`} />
              {isRefetching ? 'Syncing...' : 'Refresh Pipeline'}
            </button>
          </div>
        </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
            <span className="text-emerald-400 font-bold">100% indexed</span> in fiduciary database.
          </div>
        </div>

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
                <option value="ADP">ADP Inc.</option>
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

      {/* Main Lead Pipeline Workspace */}
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
                  <th className="px-4 py-4.5 text-center">
                    <input
                      type="checkbox"
                      checked={prospects.length > 0 && selectedEins.length === prospects.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedEins(prospects.map(p => p.ein));
                        } else {
                          setSelectedEins([]);
                        }
                      }}
                      className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-blue-500/40 cursor-pointer"
                    />
                  </th>
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
                    className={`hover:bg-slate-800/20 group transition-all duration-300 border-slate-800/40 ${
                      selectedEins.includes(prospect.ein) ? 'bg-blue-950/20' : ''
                    }`}
                  >
                    <td className="px-4 py-4.5 text-center">
                      <input
                        type="checkbox"
                        checked={selectedEins.includes(prospect.ein)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEins([...selectedEins, prospect.ein]);
                          } else {
                            setSelectedEins(selectedEins.filter(id => id !== prospect.ein));
                          }
                        }}
                        className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-blue-500/40 cursor-pointer"
                      />
                    </td>
                    <td className="px-6 py-4.5 space-y-1">
                      <button
                        onClick={() => handleOpenDrawer(prospect)}
                        className="font-bold text-white tracking-wide hover:text-blue-400 text-left transition-colors flex items-center gap-1.5 cursor-pointer group/name"
                      >
                        {prospect.employer_name}
                        <span className="text-[10px] text-blue-400 opacity-0 group-hover/name:opacity-100 transition-opacity font-semibold">
                          360° Profile →
                        </span>
                      </button>
                      <div className="text-[10px] text-slate-500 font-mono">
                        EIN: {prospect.ein.slice(0,2)}-{prospect.ein.slice(2)}
                      </div>
                    </td>

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

                    <td className="px-6 py-4.5 space-y-0.5">
                      <div className="font-semibold text-slate-300">{prospect.provider || 'Unspecified'}</div>
                      <div className="text-[10px] text-slate-500 truncate max-w-[150px]">
                        {prospect.administrator || 'TPA Missing'}
                      </div>
                    </td>

                    <td className="px-6 py-4.5 text-right font-bold text-slate-200">
                      {formatCurrency(prospect.total_assets)}
                    </td>

                    <td className="px-6 py-4.5 text-right font-medium text-slate-400">
                      {prospect.participants ? prospect.participants.toLocaleString() : '0'}
                    </td>

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

                    <td className="px-6 py-4.5 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {/* 360° Profile Drawer Button */}
                        <button
                          onClick={() => handleOpenDrawer(prospect)}
                          className="px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-blue-300 transition-all cursor-pointer font-bold text-xs flex items-center gap-1"
                          title="Open 360° Prospect Profile Drawer"
                        >
                          <Activity className="h-3.5 w-3.5" />
                          360° View
                        </button>

                        {/* Branded Fiduciary Audit PDF Download */}
                        <a
                          href={auditsService.getReportPdfUrl(prospect.ein)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 hover:bg-red-500/20 transition-all cursor-pointer flex items-center justify-center gap-1 text-xs font-bold active:scale-95"
                          title="Download Branded Fiduciary Diagnostic PDF"
                        >
                          <Download className="h-3.5 w-3.5" />
                          PDF
                        </a>

                        {/* Full Audit View Page */}
                        <Link
                          href={`/audits?ein=${prospect.ein}&name=${encodeURIComponent(prospect.employer_name)}`}
                          className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 hover:text-white transition-all cursor-pointer"
                          title="View Full Audit Page & Pitch"
                        >
                          <ShieldAlert className="h-4 w-4 text-rose-500" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Floating Bulk Action Bar */}
      {selectedEins.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-slate-900 border border-blue-500/40 shadow-2xl rounded-2xl px-6 py-3.5 flex items-center gap-6 animate-bounceIn">
          <div className="flex items-center gap-2">
            <span className="h-6 w-6 rounded-full bg-blue-500 text-white font-extrabold text-xs flex items-center justify-center">
              {selectedEins.length}
            </span>
            <span className="text-xs font-bold text-slate-200">
              prospects selected
            </span>
          </div>

          <div className="h-4 w-px bg-slate-800" />

          {/* Bulk Action Select */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-400">Set Status:</span>
            <select
              defaultValue=""
              onChange={(e) => {
                if (e.target.value) {
                  bulkStatusMutation.mutate({ status: e.target.value });
                }
              }}
              disabled={bulkStatusMutation.isPending}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs font-bold text-blue-400 cursor-pointer focus:outline-none"
            >
              <option value="" disabled>-- Select New Status --</option>
              <option value="Lead">Lead</option>
              <option value="Researching">Researching</option>
              <option value="Cold Called">Cold Called</option>
              <option value="Meeting Set">Meeting Set</option>
              <option value="Disqualified">Disqualified</option>
            </select>
          </div>

          <button
            onClick={() => setSelectedEins([])}
            className="text-xs font-bold text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            Clear Selection
          </button>
        </div>
      )}

      {/* CSV Import Modal */}
      {isImportModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                <Upload className="h-5 w-5 text-blue-400" />
                Import Prospects CSV
              </h3>
              <button
                onClick={() => {
                  setIsImportModalOpen(false);
                  setImportFile(null);
                  setImportMessage(null);
                }}
                className="p-1 text-slate-400 hover:text-white rounded-lg cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Upload a custom 401(k) prospect spreadsheet (.csv). Supported headers include: <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">employer_name</code>, <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">ein</code>, <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">total_assets</code>, <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">participants</code>, <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">provider</code>, <code className="text-blue-300 bg-slate-950 px-1 py-0.5 rounded">contact_name</code>, etc.
            </p>

            <div className="border-2 border-dashed border-slate-800 hover:border-blue-500/50 rounded-2xl p-6 text-center space-y-3 transition-colors bg-slate-950/40">
              <Upload className="h-8 w-8 text-slate-500 mx-auto" />
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-200">
                  {importFile ? importFile.name : 'Select or drag CSV file'}
                </p>
                <p className="text-[11px] text-slate-500">Only .csv files supported</p>
              </div>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-600/20 file:text-blue-300 hover:file:bg-blue-600/30 cursor-pointer"
              />
            </div>

            {importMessage && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs font-bold flex items-center gap-2">
                <Check className="h-4 w-4 text-emerald-400" />
                {importMessage}
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => {
                  const sampleCsv = "employer_name,ein,total_assets,participants,provider,contact_name,contact_email,contact_phone\nAcme Corp,123456789,15000000,250,Fidelity,Jane Doe,jane@acme.com,555-0199";
                  const blob = new Blob([sampleCsv], { type: 'text/csv' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = "sample_prospects_import.csv";
                  a.click();
                }}
                className="text-xs font-bold text-slate-400 hover:text-slate-200 underline cursor-pointer"
              >
                Download Sample CSV
              </button>

              <button
                type="button"
                onClick={async () => {
                  if (!importFile) return;
                  setIsImporting(true);
                  try {
                    const res = await prospectsService.importCsv(importFile);
                    setImportMessage(res.message);
                    queryClient.invalidateQueries({ queryKey: ['prospects'] });
                  } catch (err: any) {
                    setImportMessage(err?.response?.data?.detail || 'Import failed.');
                  } finally {
                    setIsImporting(false);
                  }
                }}
                disabled={!importFile || isImporting}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
              >
                {isImporting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Upload & Process'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Prospect 360° Profile Drawer */}
      <ProspectDrawer
        prospect={selectedProspect}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onStatusChange={() => refetch()}
      />
    </div>
  );
}

export default function PipelinePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    }>
      <PipelineContent />
    </Suspense>
  );
}
