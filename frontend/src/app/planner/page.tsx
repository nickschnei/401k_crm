'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { prospectsService, tripService, TripResponse, TripStop } from '@/services/api';
import { 
  MapPin, 
  Navigation, 
  Map as MapIcon, 
  Clock, 
  Check, 
  Plus, 
  Minus, 
  Loader2, 
  Compass, 
  Search,
  Filter,
  MousePointerClick
} from 'lucide-react';
import dynamic from 'next/dynamic';

// Dynamically import map component to prevent SSR 'window is not defined' Leaflet errors
const TripMap = dynamic(() => import('@/components/TripMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[450px] bg-slate-950/60 border border-slate-850 rounded-2xl flex flex-col items-center justify-center gap-3">
      <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
      <span className="text-slate-400 text-xs font-semibold animate-pulse">Initializing map viewport...</span>
    </div>
  )
});

export default function PlannerPage() {
  const [startLocation, setStartLocation] = useState('30 Lisbon Street, Lewiston, ME');
  const [selectedEins, setSelectedEins] = useState<string[]>([]);
  const [roundTrip, setRoundTrip] = useState(true);
  const [optimizedRoute, setOptimizedRoute] = useState<TripResponse | null>(null);
  
  // Search & tab filter states
  const [searchText, setSearchText] = useState('');
  const [selectedTab, setSelectedTab] = useState('All');

  // 1. Fetch CRM prospects list
  const { data: prospects = [], isLoading: isLoadingProspects } = useQuery({
    queryKey: ['prospects-planner'],
    queryFn: () => prospectsService.getProspects()
  });

  // 2. Route Optimization Mutation
  const optimizeMutation = useMutation({
    mutationFn: () => tripService.planTrip({
      start_location: startLocation,
      eins: selectedEins,
      round_trip: roundTrip
    }),
    onSuccess: (data) => {
      setOptimizedRoute(data);
    }
  });

  // Filtering calculations
  const filteredProspects = prospects.filter(p => {
    const matchesSearch = 
      (p.employer_name?.toLowerCase().includes(searchText.toLowerCase()) || false) ||
      (p.ein?.includes(searchText) || false) ||
      (p.provider?.toLowerCase().includes(searchText.toLowerCase()) || false);
      
    const matchesTab = selectedTab === 'All' || p.status === selectedTab;
    return matchesSearch && matchesTab;
  });

  const toggleProspect = (ein: string) => {
    setSelectedEins(prev => 
      prev.includes(ein) 
        ? prev.filter(item => item !== ein) 
        : [...prev, ein]
    );
  };

  const handleSelectFiltered = () => {
    const filteredEins = filteredProspects.map(p => p.ein);
    const allFilteredSelected = filteredEins.every(ein => selectedEins.includes(ein));
    
    if (allFilteredSelected) {
      // Deselect all filtered
      setSelectedEins(prev => prev.filter(ein => !filteredEins.includes(ein)));
    } else {
      // Select all filtered (union with existing selection)
      setSelectedEins(prev => {
        const newSelection = [...prev];
        filteredEins.forEach(ein => {
          if (!newSelection.includes(ein)) {
            newSelection.push(ein);
          }
        });
        return newSelection;
      });
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'Meeting Set':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'Cold Called':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'Researching':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'Lead':
        return 'bg-slate-500/10 text-slate-400 border-slate-700/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-700/30';
    }
  };

  const formatDuration = (totalMinutes: number) => {
    const hours = Math.floor(totalMinutes / 60);
    const minutes = Math.round(totalMinutes % 60);
    if (hours === 0) return `${minutes} mins`;
    return `${hours} hr ${minutes} mins`;
  };

  // Status Tab Counts
  const getTabCount = (tabName: string) => {
    if (tabName === 'All') return prospects.length;
    return prospects.filter(p => p.status === tabName).length;
  };

  const tabs = ['All', 'Meeting Set', 'Cold Called', 'Researching', 'Lead'];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
          Fiduciary Itinerary Planner
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Select target company audits, configure your starting base, and solve the Traveling Salesperson routing optimization.
        </p>
      </div>

      {/* Main Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Configuration Controls (lg:col-span-5) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Start Location Card */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl space-y-4">
            <div className="flex items-center gap-2 text-indigo-400">
              <Navigation className="h-5 w-5" />
              <h3 className="font-bold text-sm uppercase tracking-wider text-slate-200">Start Location</h3>
            </div>
            
            <div className="space-y-2">
              <label className="text-xs text-slate-500 font-bold uppercase tracking-wider">Starting Address / ZIP</label>
              <input
                type="text"
                value={startLocation}
                onChange={(e) => setStartLocation(e.target.value)}
                placeholder="Enter street, city, state or ZIP..."
                className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 text-sm transition-all"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-400 font-semibold">Round Trip Route</span>
              <button
                type="button"
                onClick={() => setRoundTrip(!roundTrip)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none cursor-pointer ${roundTrip ? 'bg-indigo-600' : 'bg-slate-800'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${roundTrip ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>
          </div>

          {/* Prospects Multi-Selector Card */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl flex flex-col min-h-[550px] max-h-[680px]">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-indigo-400">
                <MapPin className="h-5 w-5" />
                <h3 className="font-bold text-sm uppercase tracking-wider text-slate-200">Target Prospects</h3>
              </div>
              <span className="text-xs bg-slate-850 px-2 py-0.5 rounded-md font-mono text-indigo-400 font-bold">
                {selectedEins.length} selected
              </span>
            </div>

            {/* Search Input */}
            <div className="relative mb-3">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by company or EIN..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-650 focus:outline-none focus:border-indigo-500/50 text-xs transition-all"
              />
            </div>

            {/* Status Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto pb-2 border-b border-slate-850 mb-3 scrollbar-thin">
              {tabs.map((tab) => {
                const count = getTabCount(tab);
                const isActive = selectedTab === tab;
                return (
                  <button
                    key={tab}
                    onClick={() => setSelectedTab(tab)}
                    className={`px-3 py-1.5 rounded-lg text-2xs font-bold whitespace-nowrap cursor-pointer transition-all border ${
                      isActive 
                        ? 'bg-indigo-600/15 border-indigo-500/30 text-indigo-300' 
                        : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {tab} <span className="opacity-60 ml-0.5">({count})</span>
                  </button>
                );
              })}
            </div>

            {/* Quick Actions Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-850/50 mb-3">
              <span className="text-2xs text-slate-500 font-semibold">
                Showing {filteredProspects.length} targets
              </span>
              
              <button 
                onClick={handleSelectFiltered}
                disabled={filteredProspects.length === 0}
                className="flex items-center gap-1 text-2xs font-bold text-sky-400 hover:text-sky-300 transition-colors cursor-pointer disabled:opacity-30"
              >
                <MousePointerClick className="h-3 w-3" />
                {filteredProspects.every(p => selectedEins.includes(p.ein)) 
                  ? 'Deselect Tab' 
                  : 'Select Tab'}
              </button>
            </div>

            {/* Scrollable list */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
              {isLoadingProspects ? (
                <div className="flex items-center justify-center py-20 gap-2">
                  <Loader2 className="h-4 w-4 text-indigo-500 animate-spin" />
                  <span className="text-slate-500 text-xs font-medium">Loading CRM dataset...</span>
                </div>
              ) : filteredProspects.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
                  <Filter className="h-6 w-6 text-slate-700" />
                  <p className="text-slate-500 text-xs font-semibold">No matching prospects found.</p>
                </div>
              ) : (
                filteredProspects.map((p) => {
                  const isSelected = selectedEins.includes(p.ein);
                  return (
                    <div
                      key={p.ein}
                      onClick={() => toggleProspect(p.ein)}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-300 cursor-pointer ${
                        isSelected 
                          ? 'bg-indigo-600/10 border-indigo-500/35 hover:bg-indigo-600/15' 
                          : 'bg-slate-950/40 border-slate-850 hover:bg-slate-800/30'
                      }`}
                    >
                      <div className="space-y-1 flex-1 min-w-0 pr-3">
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-xs text-slate-200 truncate">{p.employer_name}</h4>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold border uppercase tracking-wider ${getStatusStyle(p.status)}`}>
                            {p.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                          <span className="font-mono">EIN: {p.ein}</span>
                          <span>·</span>
                          <span className="truncate">{p.provider || 'No Provider'}</span>
                        </div>
                      </div>
                      
                      <div className={`h-5 w-5 rounded-lg border flex items-center justify-center transition-all ${
                        isSelected 
                          ? 'bg-indigo-500 border-indigo-400 text-white' 
                          : 'border-slate-800 text-transparent'
                      }`}>
                        <Check className="h-3 w-3" />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Optimization trigger */}
            <div className="pt-4 border-t border-slate-850 mt-4">
              <button
                onClick={() => optimizeMutation.mutate()}
                disabled={selectedEins.length === 0 || optimizeMutation.isPending}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 text-white font-bold text-sm py-3 rounded-xl shadow-lg transition-all duration-300 active:scale-[0.98] cursor-pointer disabled:opacity-50"
              >
                {optimizeMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-white" />
                    Solving Routing Model...
                  </>
                ) : (
                  <>
                    <Compass className="h-4 w-4 text-white" />
                    Optimize Visits Route
                  </>
                )}
              </button>
            </div>
          </div>

        </div>

        {/* Right Column: Map & Optimized Timelines (lg:col-span-7) */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Map View Card */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center gap-2 text-indigo-400 mb-4">
              <MapIcon className="h-5 w-5" />
              <h3 className="font-bold text-sm uppercase tracking-wider text-slate-200">Interactive Map View</h3>
            </div>
            
            <div className="h-[480px] w-full rounded-xl overflow-hidden relative">
              <TripMap stops={optimizedRoute?.stops || []} />
            </div>
          </div>

          {/* Optimized Route Timeline Details */}
          {optimizedRoute && (
            <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl space-y-6 animate-fadeIn">
              
              {/* Route Summary Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-b border-slate-850 pb-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
                    <Compass className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Total Route Distance</p>
                    <p className="text-xl font-extrabold text-white">{optimizedRoute.total_distance_miles} miles</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                    <Clock className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Est. Total Duration (incl. meetings)</p>
                    <p className="text-xl font-extrabold text-white">{formatDuration(optimizedRoute.total_duration_minutes)}</p>
                  </div>
                </div>
              </div>

              {/* Stop-by-Stop Timeline */}
              <div className="space-y-4">
                <h4 className="font-bold text-sm uppercase tracking-wider text-slate-300">Optimized Visit Order</h4>
                
                <div className="relative pl-6 border-l-2 border-indigo-600/30 space-y-6 ml-3">
                  {optimizedRoute.stops.map((stop, i) => {
                    const isStart = i === 0;
                    const isReturn = i === optimizedRoute.stops.length - 1 && stop.name === "Return to Start";
                    
                    let badgeColor = 'bg-indigo-600 border-indigo-400 text-white';
                    let badgeText = `${i}`;
                    
                    if (isStart) {
                      badgeColor = 'bg-emerald-500 border-emerald-400 text-white';
                      badgeText = 'Start';
                    } else if (isReturn) {
                      badgeColor = 'bg-rose-500 border-rose-400 text-white';
                      badgeText = 'End';
                    }

                    return (
                      <div key={i} className="relative">
                        {/* Bullet Badge */}
                        <div className={`absolute -left-[38px] top-0.5 h-6 w-11 rounded-full border text-[10px] font-extrabold flex items-center justify-center uppercase tracking-wider ${badgeColor}`}>
                          {badgeText}
                        </div>

                        {/* Leg Info Card */}
                        <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-xl space-y-2 hover:border-slate-800 transition-colors">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                            <h5 className="font-extrabold text-xs text-slate-200">{stop.name}</h5>
                            {i > 0 && (
                              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-semibold max-sm:self-start">
                                +{stop.distance_from_last} mi · ~{Math.round(stop.leg_duration_minutes)} min drive
                              </span>
                            )}
                          </div>
                          
                          <p className="text-[11px] text-slate-500">{stop.address}</p>
                          
                          {/* meeting details for client stops */}
                          {!isStart && !isReturn && (
                            <div className="flex items-center gap-1 text-[10px] text-indigo-400 font-semibold pt-1 border-t border-slate-900 mt-2">
                              <Clock className="h-3 w-3" />
                              <span>45-minute on-site fiduciary meeting scheduled</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>
          )}

        </div>
      </div>
    </div>
  );
}
