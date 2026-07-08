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
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import dynamic from 'next/dynamic';

// Dynamically import map component with ssr: false to prevent SSR 'window is not defined' Leaflet errors
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

  const toggleProspect = (ein: string) => {
    setSelectedEins(prev => 
      prev.includes(ein) 
        ? prev.filter(item => item !== ein) 
        : [...prev, ein]
    );
  };

  const handleSelectAll = () => {
    if (selectedEins.length === prospects.length) {
      setSelectedEins([]);
    } else {
      setSelectedEins(prospects.map(p => p.ein));
    }
  };

  const formatDuration = (totalMinutes: number) => {
    const hours = Math.floor(totalMinutes / 60);
    const minutes = Math.round(totalMinutes % 60);
    if (hours === 0) return `${minutes} mins`;
    return `${hours} hr ${minutes} mins`;
  };

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
        {/* Left Column: Configuration Controls (lg:col-span-4) */}
        <div className="lg:col-span-4 space-y-6">
          
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
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl flex flex-col max-h-[480px]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-indigo-400">
                <MapPin className="h-5 w-5" />
                <h3 className="font-bold text-sm uppercase tracking-wider text-slate-200">Target Prospects</h3>
              </div>
              <button 
                onClick={handleSelectAll}
                className="text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors cursor-pointer"
              >
                {selectedEins.length === prospects.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            {/* Scrollable list */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {isLoadingProspects ? (
                <div className="flex items-center justify-center py-10 gap-2">
                  <Loader2 className="h-4 w-4 text-indigo-500 animate-spin" />
                  <span className="text-slate-500 text-xs font-medium">Loading CRM data...</span>
                </div>
              ) : prospects.length === 0 ? (
                <p className="text-slate-500 text-xs text-center py-10">No prospects available in CRM.</p>
              ) : (
                prospects.map((p) => {
                  const isSelected = selectedEins.includes(p.ein);
                  return (
                    <div
                      key={p.ein}
                      onClick={() => toggleProspect(p.ein)}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-300 cursor-pointer ${
                        isSelected 
                          ? 'bg-indigo-600/10 border-indigo-500/30 hover:bg-indigo-600/15' 
                          : 'bg-slate-950/40 border-slate-850 hover:bg-slate-800/30'
                      }`}
                    >
                      <div className="space-y-0.5 flex-1 min-w-0 pr-3">
                        <h4 className="font-bold text-xs text-slate-200 truncate">{p.employer_name}</h4>
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

        {/* Right Column: Map & Optimized Timelines (lg:col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Map View Card */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center gap-2 text-indigo-400 mb-4">
              <MapIcon className="h-5 w-5" />
              <h3 className="font-bold text-sm uppercase tracking-wider text-slate-200">Interactive Map View</h3>
            </div>
            
            <div className="h-[450px] w-full rounded-xl overflow-hidden relative">
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
