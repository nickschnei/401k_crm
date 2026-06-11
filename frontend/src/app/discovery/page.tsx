'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { discoveryService, DiscoveryFiling } from '@/services/api';
import { 
  Search, 
  ChevronDown, 
  Activity,
  DollarSign,
  Users,
  Loader2,
  RefreshCw,
  MapPin,
  ShieldAlert,
  X,
  Sparkles,
  Info
} from 'lucide-react';
import Link from 'next/link';

// Static choices
const US_STATES = [
  { value: 'AK', label: 'Alaska (AK)' },
  { value: 'AL', label: 'Alabama (AL)' },
  { value: 'AR', label: 'Arkansas (AR)' },
  { value: 'AZ', label: 'Arizona (AZ)' },
  { value: 'CA', label: 'California (CA)' },
  { value: 'CO', label: 'Colorado (CO)' },
  { value: 'CT', label: 'Connecticut (CT)' },
  { value: 'DE', label: 'Delaware (DE)' },
  { value: 'FL', label: 'Florida (FL)' },
  { value: 'GA', label: 'Georgia (GA)' },
  { value: 'HI', label: 'Hawaii (HI)' },
  { value: 'IA', label: 'Iowa (IA)' },
  { value: 'ID', label: 'Idaho (ID)' },
  { value: 'IL', label: 'Illinois (IL)' },
  { value: 'IN', label: 'Indiana (IN)' },
  { value: 'KS', label: 'Kansas (KS)' },
  { value: 'KY', label: 'Kentucky (KY)' },
  { value: 'LA', label: 'Louisiana (LA)' },
  { value: 'MA', label: 'Massachusetts (MA)' },
  { value: 'MD', label: 'Maryland (MD)' },
  { value: 'ME', label: 'Maine (ME)' },
  { value: 'MI', label: 'Michigan (MI)' },
  { value: 'MN', label: 'Minnesota (MN)' },
  { value: 'MO', label: 'Missouri (MO)' },
  { value: 'MS', label: 'Mississippi (MS)' },
  { value: 'MT', label: 'Montana (MT)' },
  { value: 'NC', label: 'North Carolina (NC)' },
  { value: 'ND', label: 'North Dakota (ND)' },
  { value: 'NE', label: 'Nebraska (NE)' },
  { value: 'NH', label: 'New Hampshire (NH)' },
  { value: 'NJ', label: 'New Jersey (NJ)' },
  { value: 'NM', label: 'New Mexico (NM)' },
  { value: 'NV', label: 'Nevada (NV)' },
  { value: 'NY', label: 'New York (NY)' },
  { value: 'OH', label: 'Ohio (OH)' },
  { value: 'OK', label: 'Oklahoma (OK)' },
  { value: 'OR', label: 'Oregon (OR)' },
  { value: 'PA', label: 'Pennsylvania (PA)' },
  { value: 'RI', label: 'Rhode Island (RI)' },
  { value: 'SC', label: 'South Carolina (SC)' },
  { value: 'SD', label: 'South Dakota (SD)' },
  { value: 'TN', label: 'Tennessee (TN)' },
  { value: 'TX', label: 'Texas (TX)' },
  { value: 'UT', label: 'Utah (UT)' },
  { value: 'VA', label: 'Virginia (VA)' },
  { value: 'VT', label: 'Vermont (VT)' },
  { value: 'WA', label: 'Washington (WA)' },
  { value: 'WI', label: 'Wisconsin (WI)' },
  { value: 'WV', label: 'West Virginia (WV)' },
  { value: 'WY', label: 'Wyoming (WY)' }
];

const ASSET_RANGES = [
  { value: 'under_1m', label: 'Under $1M' },
  { value: '1m_to_5m', label: '$1M - $5M (Schedule I/SF)' },
  { value: '5m_to_25m', label: '$5M - $25M (Schedule H)' },
  { value: '25m_to_100m', label: '$25M - $100M' },
  { value: 'over_100m', label: '$100M+ Mega Plans' }
];

const PARTICIPANT_RANGES = [
  { value: 'under_50', label: 'Under 50' },
  { value: '50_to_100', label: '50 - 100' },
  { value: '100_to_500', label: '100 - 500' },
  { value: '500_to_1000', label: '500 - 1,000' },
  { value: 'over_1000', label: '1,000+ Enterprise' }
];

const SCHEDULE_TYPES = [
  { value: 'H', label: 'Schedule H (Large Plans)' },
  { value: 'I', label: 'Schedule I (Small Plans)' },
  { value: 'SF', label: 'Schedule SF (Short Form)' },
  { value: 'None', label: 'No Schedule (None)' }
];

const PROVIDERS = [
  { value: 'fidelity', label: 'Fidelity Investments' },
  { value: 'vanguard', label: 'Vanguard Group' }
];

const COMMON_ADMINISTRATORS = [
  { value: 'GUIDELINE RK, LLC', label: 'Guideline RK' },
  { value: 'ERISA FIDUCIARY SERVICES, INC.', label: 'ERISA Fiduciary Services' },
  { value: 'ADMINISTRATIVE GROUP, LLC DBA TAG RESOURCES', label: 'TAG Resources' },
  { value: '401GO, INC.', label: '401Go Inc.' },
  { value: 'FUTUREPLAN FIDUCIARY SERVICES LLC', label: 'FuturePlan Fiduciary' },
  { value: 'GUIDELINE, INC.', label: 'Guideline Inc.' },
  { value: 'NORTHEAST RETIREMENT SERVICES, LLC', label: 'Northeast Retirement' },
  { value: 'HEALTHEQUITY RETIREMENT SERVICES', label: 'HealthEquity Retirement' }
];

// MultiSelectDropdown Component
interface MultiSelectDropdownProps {
  label: string;
  options: { label: string; value: string }[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  showSearch?: boolean;
}

function MultiSelectDropdown({
  label,
  options,
  selectedValues,
  onChange,
  showSearch = false,
}: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOption = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((v) => v !== value));
    } else {
      onChange([...selectedValues, value]);
    }
  };

  const handleSelectAll = () => {
    onChange(options.map((o) => o.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const filteredOptions = showSearch
    ? options.filter((o) => o.label.toLowerCase().includes(searchTerm.toLowerCase()))
    : options;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between gap-2 px-4 py-3 bg-slate-950/60 border rounded-xl hover:bg-slate-900/60 text-xs font-semibold tracking-wide transition-all cursor-pointer select-none w-full lg:w-48 text-left ${
          selectedValues.length > 0
            ? 'border-blue-500/50 bg-blue-500/10 text-white shadow-lg shadow-blue-500/5'
            : 'border-slate-800 text-slate-300'
        }`}
      >
        <span className="truncate">
          {selectedValues.length === 0
            ? label
            : `${label} (${selectedValues.length})`}
        </span>
        <ChevronDown className={`h-3 w-3 text-slate-500 transition-transform duration-300 shrink-0 ${isOpen ? 'rotate-180 text-blue-400' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 bg-[#090d16]/95 border border-slate-800 rounded-xl shadow-2xl p-3 z-50 flex flex-col gap-2 max-h-80 animate-in fade-in slide-in-from-top-1 duration-250 backdrop-blur-xl">
          {showSearch && (
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/30"
              />
            </div>
          )}

          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold border-b border-slate-850 pb-1.5 px-1 select-none">
            <button type="button" onClick={handleSelectAll} className="hover:text-blue-400 cursor-pointer">
              Select All
            </button>
            <button type="button" onClick={handleClearAll} className="hover:text-blue-400 cursor-pointer">
              Clear All
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1 max-h-48 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
            {filteredOptions.length === 0 ? (
              <div className="text-center py-4 text-xs text-slate-500 font-medium">
                No options found
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isChecked = selectedValues.includes(opt.value);
                return (
                  <label
                    key={opt.value}
                    className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-900/60 rounded-lg cursor-pointer select-none text-xs text-slate-300 hover:text-white transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleOption(opt.value)}
                      className="rounded border-slate-800 bg-slate-950 text-blue-500 focus:ring-0 focus:ring-offset-0 cursor-pointer h-3.5 w-3.5"
                    />
                    <span className="truncate">{opt.label}</span>
                  </label>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DiscoveryPage() {
  const queryClient = useQueryClient();

  // Filters State
  const [search, setSearch] = useState('');
  const [selectedStates, setSelectedStates] = useState<string[]>([]);
  const [selectedAssetRanges, setSelectedAssetRanges] = useState<string[]>([]);
  const [selectedParticipantRanges, setSelectedParticipantRanges] = useState<string[]>([]);
  const [selectedSchedules, setSelectedSchedules] = useState<string[]>([]);
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [selectedAdministrators, setSelectedAdministrators] = useState<string[]>([]);

  // Fetch Celery sync status
  const { data: syncStatus, refetch: refetchSyncStatus } = useQuery({
    queryKey: ['discovery-sync-status'],
    queryFn: () => discoveryService.getSyncStatus(),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.is_running ? 3000 : false;
    }
  });

  // Query filings
  const { data: filings = [], isLoading, isRefetching, refetch } = useQuery({
    queryKey: [
      'discovery-filings', 
      search, 
      selectedStates, 
      selectedAssetRanges, 
      selectedParticipantRanges, 
      selectedSchedules, 
      selectedProviders, 
      selectedAdministrators
    ],
    queryFn: () => discoveryService.getFilings({
      search: search || undefined,
      state: selectedStates.length > 0 ? selectedStates.join(',') : undefined,
      asset_ranges: selectedAssetRanges.length > 0 ? selectedAssetRanges.join(',') : undefined,
      participant_ranges: selectedParticipantRanges.length > 0 ? selectedParticipantRanges.join(',') : undefined,
      schedule_type: selectedSchedules.length > 0 ? selectedSchedules.join(',') : undefined,
      provider: selectedProviders.length > 0 ? selectedProviders.join(',') : undefined,
      administrator: selectedAdministrators.length > 0 ? selectedAdministrators.join(',') : undefined
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

  // Check if any filters are active
  const hasActiveFilters = 
    search !== '' ||
    selectedStates.length > 0 ||
    selectedAssetRanges.length > 0 ||
    selectedParticipantRanges.length > 0 ||
    selectedSchedules.length > 0 ||
    selectedProviders.length > 0 ||
    selectedAdministrators.length > 0;

  // Clear all filters
  const clearAllFilters = () => {
    setSearch('');
    setSelectedStates([]);
    setSelectedAssetRanges([]);
    setSelectedParticipantRanges([]);
    setSelectedSchedules([]);
    setSelectedProviders([]);
    setSelectedAdministrators([]);
  };

  // Helper to remove a single filter item
  const removeFilterItem = (type: string, value: string) => {
    if (type === 'search') setSearch('');
    else if (type === 'state') setSelectedStates(selectedStates.filter(v => v !== value));
    else if (type === 'assets') setSelectedAssetRanges(selectedAssetRanges.filter(v => v !== value));
    else if (type === 'participants') setSelectedParticipantRanges(selectedParticipantRanges.filter(v => v !== value));
    else if (type === 'schedule') setSelectedSchedules(selectedSchedules.filter(v => v !== value));
    else if (type === 'provider') setSelectedProviders(selectedProviders.filter(v => v !== value));
    else if (type === 'administrator') setSelectedAdministrators(selectedAdministrators.filter(v => v !== value));
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

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metric 1 */}
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30">
          <div className="absolute top-0 right-0 h-24 w-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors duration-500" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Indexed DOL Filings</span>
              <h3 className="text-4xl font-extrabold text-white tracking-tight">{filingsCount}</h3>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
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

      {/* Advanced Filter Interface */}
      <div className="bg-slate-900/25 border border-slate-800/60 p-6 rounded-2xl shadow-lg space-y-5">
        <div className="flex flex-col gap-4">
          {/* Main text search bar */}
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search complete registries by corporate sponsor, ZIP, city, state, administrator..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
            />
          </div>

          {/* Row of multi-select filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider select-none mr-2">
              Segment By:
            </span>

            {/* States Location multi-select */}
            <MultiSelectDropdown
              label="Location (State)"
              options={US_STATES}
              selectedValues={selectedStates}
              onChange={setSelectedStates}
              showSearch
            />

            {/* Asset size multi-select */}
            <MultiSelectDropdown
              label="Plan Size (Assets)"
              options={ASSET_RANGES}
              selectedValues={selectedAssetRanges}
              onChange={setSelectedAssetRanges}
            />

            {/* Participants headcount multi-select */}
            <MultiSelectDropdown
              label="Participants"
              options={PARTICIPANT_RANGES}
              selectedValues={selectedParticipantRanges}
              onChange={setSelectedParticipantRanges}
            />

            {/* Form type schedule type multi-select */}
            <MultiSelectDropdown
              label="Form Schedule"
              options={SCHEDULE_TYPES}
              selectedValues={selectedSchedules}
              onChange={setSelectedSchedules}
            />

            {/* Provider multi-select */}
            <MultiSelectDropdown
              label="Provider"
              options={PROVIDERS}
              selectedValues={selectedProviders}
              onChange={setSelectedProviders}
            />

            {/* Administrator TPA multi-select */}
            <MultiSelectDropdown
              label="Administrator"
              options={COMMON_ADMINISTRATORS}
              selectedValues={selectedAdministrators}
              onChange={setSelectedAdministrators}
            />
          </div>
        </div>

        {/* Active badges bar */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2 items-center pt-2 border-t border-slate-850 animate-in fade-in duration-300">
            <span className="text-[10px] font-extrabold text-blue-400 uppercase tracking-wider select-none mr-1">
              Active Filters:
            </span>

            {search && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold select-none">
                Query: &quot;{search}&quot;
                <button type="button" onClick={() => removeFilterItem('search', '')} className="hover:text-white cursor-pointer ml-0.5">
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}

            {selectedStates.map(state => (
              <span key={state} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold select-none">
                State: {state}
                <button type="button" onClick={() => removeFilterItem('state', state)} className="hover:text-white cursor-pointer ml-0.5">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}

            {selectedAssetRanges.map(range => {
              const label = ASSET_RANGES.find(o => o.value === range)?.label || range;
              return (
                <span key={range} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold select-none">
                  Assets: {label}
                  <button type="button" onClick={() => removeFilterItem('assets', range)} className="hover:text-white cursor-pointer ml-0.5">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}

            {selectedParticipantRanges.map(range => {
              const label = PARTICIPANT_RANGES.find(o => o.value === range)?.label || range;
              return (
                <span key={range} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-semibold select-none">
                  Headcount: {label}
                  <button type="button" onClick={() => removeFilterItem('participants', range)} className="hover:text-white cursor-pointer ml-0.5">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}

            {selectedSchedules.map(sched => {
              const label = SCHEDULE_TYPES.find(o => o.value === sched)?.label || sched;
              return (
                <span key={sched} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-semibold select-none">
                  Schedule: {sched}
                  <button type="button" onClick={() => removeFilterItem('schedule', sched)} className="hover:text-white cursor-pointer ml-0.5">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}

            {selectedProviders.map(p => {
              const label = PROVIDERS.find(o => o.value === p)?.label || p;
              return (
                <span key={p} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold select-none">
                  Provider: {label}
                  <button type="button" onClick={() => removeFilterItem('provider', p)} className="hover:text-white cursor-pointer ml-0.5">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}

            {selectedAdministrators.map(a => {
              const label = COMMON_ADMINISTRATORS.find(o => o.value === a)?.label || a;
              return (
                <span key={a} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20 text-xs font-semibold select-none">
                  Admin: {label}
                  <button type="button" onClick={() => removeFilterItem('administrator', a)} className="hover:text-white cursor-pointer ml-0.5">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              );
            })}

            <button 
              type="button"
              onClick={clearAllFilters}
              className="text-[10px] text-rose-400 hover:text-rose-300 font-bold uppercase tracking-wider cursor-pointer ml-2 hover:underline"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Discovery Filings List */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl shadow-2xl overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
            <p className="text-slate-400 text-sm font-semibold animate-pulse">Scanning relational DB, filtering filings...</p>
          </div>
        ) : filings.length === 0 ? (
          <div className="text-center py-20 px-4 space-y-3">
            <div className="h-12 w-12 rounded-full bg-slate-800/60 text-slate-500 flex items-center justify-center mx-auto">
              <Activity className="h-6 w-6" />
            </div>
            <h4 className="text-slate-300 font-bold text-lg">No raw filings found</h4>
            <p className="text-slate-500 text-xs max-w-sm mx-auto">
              No plan filings match the active search criteria. Try broadening your filter options or click &quot;Clear All&quot;.
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
