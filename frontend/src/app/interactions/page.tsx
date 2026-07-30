'use client';

import React, { useState, Suspense } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { prospectsService, interactionService, Interaction, Prospect } from '@/services/api';
import { 
  Search, 
  ChevronDown, 
  Sparkles, 
  Mail, 
  Phone, 
  User, 
  Activity,
  Calendar,
  Loader2,
  RefreshCw,
  FileText,
  Plus,
  Trash2,
  Edit2,
  Clock,
  MessageSquare,
  Users,
  Building2,
  X,
  CheckCircle2,
  Circle,
  AlertTriangle,
  Bell,
  CheckSquare
} from 'lucide-react';

function InteractionsContent() {
  const queryClient = useQueryClient();

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [prospectFilter, setProspectFilter] = useState('All');
  const [followupCategory, setFollowupCategory] = useState<'All' | 'Overdue' | 'Today' | 'Upcoming' | 'Completed'>('All');

  // Form State (Create)
  const [prospectId, setProspectId] = useState('');
  const [contactName, setContactName] = useState('');
  const [interactionType, setInteractionType] = useState('Call');
  const [notes, setNotes] = useState('');
  const [interactionDate, setInteractionDate] = useState(
    new Date().toISOString().slice(0, 16)
  );
  const [enableFollowup, setEnableFollowup] = useState(false);
  const [followupDate, setFollowupDate] = useState('');
  const [followupNotes, setFollowupNotes] = useState('');
  
  // Edit Modal State
  const [editingInteraction, setEditingInteraction] = useState<Interaction | null>(null);
  const [editContactName, setEditContactName] = useState('');
  const [editInteractionType, setEditInteractionType] = useState('Call');
  const [editNotes, setEditNotes] = useState('');
  const [editInteractionDate, setEditInteractionDate] = useState('');
  const [editEnableFollowup, setEditEnableFollowup] = useState(false);
  const [editFollowupDate, setEditFollowupDate] = useState('');
  const [editFollowupCompleted, setEditFollowupCompleted] = useState(false);
  const [editFollowupNotes, setEditFollowupNotes] = useState('');

  // Fetch prospects
  const { data: prospects = [] } = useQuery({
    queryKey: ['prospects'],
    queryFn: () => prospectsService.getProspects(),
  });

  // Fetch interactions
  const { data: interactions = [], isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['interactions'],
    queryFn: () => interactionService.getInteractions(),
  });

  // Create Interaction Mutation
  const createMutation = useMutation({
    mutationFn: (req: any) => interactionService.createInteraction(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
      // Reset form
      setProspectId('');
      setContactName('');
      setInteractionType('Call');
      setNotes('');
      setInteractionDate(new Date().toISOString().slice(0, 16));
      setEnableFollowup(false);
      setFollowupDate('');
      setFollowupNotes('');
    },
  });

  // Update Interaction Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, req }: { id: string; req: any }) =>
      interactionService.updateInteraction(id, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
      setEditingInteraction(null);
    },
  });

  // Toggle Follow-up Mutation
  const toggleFollowupMutation = useMutation({
    mutationFn: ({ id, completed }: { id: string; completed?: boolean }) =>
      interactionService.toggleFollowup(id, completed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
  });

  // Delete Interaction Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => interactionService.deleteInteraction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
  });

  // Auto-fill contact name when prospect is selected
  const handleProspectChange = (id: string) => {
    setProspectId(id);
    const selected = prospects.find(p => p.ein === id || p.employer_name === id);
    if (selected && selected.contact_name) {
      setContactName(selected.contact_name);
    } else {
      const match = prospects.find(p => p.employer_name === id || p.ein === id);
      if (match && match.contact_name) {
        setContactName(match.contact_name);
      } else {
        setContactName('');
      }
    }
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactName.trim() || !notes.trim()) return;

    const matchingProspect = prospects.find(p => p.ein === prospectId || p.employer_name === prospectId);
    
    createMutation.mutate({
      prospect_id: matchingProspect ? matchingProspect.ein : undefined,
      contact_name: contactName,
      interaction_type: interactionType,
      notes: notes,
      interaction_date: new Date(interactionDate).toISOString(),
      followup_date: enableFollowup && followupDate ? new Date(followupDate).toISOString() : undefined,
      followup_notes: enableFollowup && followupNotes ? followupNotes : undefined,
    });
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingInteraction) return;

    updateMutation.mutate({
      id: editingInteraction.id,
      req: {
        contact_name: editContactName,
        interaction_type: editInteractionType,
        notes: editNotes,
        interaction_date: new Date(editInteractionDate).toISOString(),
        followup_date: editEnableFollowup && editFollowupDate ? new Date(editFollowupDate).toISOString() : null,
        followup_completed: editFollowupCompleted,
        followup_notes: editEnableFollowup && editFollowupNotes ? editFollowupNotes : null,
      },
    });
  };

  const openEditModal = (interaction: Interaction) => {
    setEditingInteraction(interaction);
    setEditContactName(interaction.contact_name);
    setEditInteractionType(interaction.interaction_type);
    setEditNotes(interaction.notes);
    setEditInteractionDate(new Date(interaction.interaction_date).toISOString().slice(0, 16));
    setEditEnableFollowup(!!interaction.followup_date);
    setEditFollowupDate(
      interaction.followup_date ? new Date(interaction.followup_date).toISOString().slice(0, 16) : ''
    );
    setEditFollowupCompleted(interaction.followup_completed || false);
    setEditFollowupNotes(interaction.followup_notes || '');
  };

  // Follow-up Helper Logic
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);

  const getFollowupStatus = (interaction: Interaction) => {
    if (!interaction.followup_date) return null;
    if (interaction.followup_completed) return 'Completed';

    const fDate = new Date(interaction.followup_date);
    if (fDate < todayStart) return 'Overdue';
    if (fDate >= todayStart && fDate <= todayEnd) return 'Today';
    return 'Upcoming';
  };

  // Follow-up Counts
  const followupsList = interactions.filter(i => i.followup_date);
  const overdueCount = followupsList.filter(i => getFollowupStatus(i) === 'Overdue').length;
  const todayCount = followupsList.filter(i => getFollowupStatus(i) === 'Today').length;
  const upcomingCount = followupsList.filter(i => getFollowupStatus(i) === 'Upcoming').length;
  const completedCount = followupsList.filter(i => i.followup_completed).length;

  // Filtered interactions for timeline
  const filteredInteractions = interactions.filter(item => {
    const matchesSearch = 
      item.contact_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.notes.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.employer_name && item.employer_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = typeFilter === 'All' || item.interaction_type === typeFilter;
    const matchesProspect = prospectFilter === 'All' || item.ein === prospectFilter || item.prospect_id === prospectFilter;
    
    let matchesFollowup = true;
    if (followupCategory !== 'All') {
      const status = getFollowupStatus(item);
      matchesFollowup = status === followupCategory;
    }

    return matchesSearch && matchesType && matchesProspect && matchesFollowup;
  });

  const getTypeBadgeColor = (type: string) => {
    const styles: Record<string, string> = {
      'Call': 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
      'Email': 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
      'Meeting': 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      'Note': 'bg-slate-500/10 text-slate-400 border border-slate-500/20',
    };
    return styles[type] || 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 border-b border-slate-850 pb-6">
        <div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
            Interaction Logs & Task Reminders
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Track prospect communications, schedule follow-up reminders, and manage your action queue.
          </p>
        </div>

        <button 
          onClick={() => refetch()}
          disabled={isLoading || isRefetching}
          className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-300 font-semibold text-xs transition-all duration-300 cursor-pointer disabled:opacity-50 self-start md:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefetching || isLoading ? 'animate-spin' : ''}`} />
          Force Reload
        </button>
      </div>

      {/* Action Queue & Reminders Banner */}
      <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-500/10 rounded-xl text-amber-400">
              <Bell className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Follow-Up Action Queue</h3>
              <p className="text-xs text-slate-400">Filter your communications by scheduled follow-up status</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFollowupCategory('All')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                followupCategory === 'All'
                  ? 'bg-slate-800 text-white border border-slate-700'
                  : 'bg-slate-950/40 text-slate-400 hover:text-slate-200 border border-slate-850'
              }`}
            >
              All Logs ({interactions.length})
            </button>
            <button
              onClick={() => setFollowupCategory('Overdue')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                followupCategory === 'Overdue'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  : 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20'
              }`}
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Overdue ({overdueCount})
            </button>
            <button
              onClick={() => setFollowupCategory('Today')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                followupCategory === 'Today'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20'
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              Due Today ({todayCount})
            </button>
            <button
              onClick={() => setFollowupCategory('Upcoming')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                followupCategory === 'Upcoming'
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                  : 'bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20'
              }`}
            >
              <Calendar className="h-3.5 w-3.5" />
              Upcoming ({upcomingCount})
            </button>
            <button
              onClick={() => setFollowupCategory('Completed')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                followupCategory === 'Completed'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20'
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Completed ({completedCount})
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Left Column: Log Form */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus className="h-5 w-5 text-blue-400" />
              Log Interaction & Reminder
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Record interaction details and set an optional follow-up task.
            </p>
          </div>

          <form onSubmit={handleCreateSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5" />
                Select Prospect / Employer
              </label>
              <select
                value={prospectId}
                onChange={(e) => handleProspectChange(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
                required
              >
                <option value="">-- Choose Corporate Account --</option>
                {prospects.map((p) => (
                  <option key={p.ein} value={p.ein}>
                    {p.employer_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <User className="h-3.5 w-3.5" />
                Talked To (Contact Name)
              </label>
              <input
                type="text"
                placeholder="Name of contact person"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" />
                Interaction Type
              </label>
              <div className="grid grid-cols-4 gap-2">
                {['Call', 'Email', 'Meeting', 'Note'].map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setInteractionType(type)}
                    className={`py-2 rounded-xl text-xs font-bold border transition-all duration-300 cursor-pointer ${
                      interactionType === type 
                        ? 'bg-blue-600/20 border-blue-500 text-blue-400 font-extrabold shadow-sm'
                        : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                    }`}
                  >
                    {type === 'Call' && '📞 '}
                    {type === 'Email' && '✉️ '}
                    {type === 'Meeting' && '🤝 '}
                    {type === 'Note' && '📝 '}
                    {type}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                Date & Time
              </label>
              <input
                type="datetime-local"
                value={interactionDate}
                onChange={(e) => setInteractionDate(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="h-3.5 w-3.5" />
                Interaction Notes
              </label>
              <textarea
                placeholder="Record details of what was discussed, follow-up items, etc."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm resize-none"
                required
              />
            </div>

            {/* Follow-up Section Toggle */}
            <div className="pt-2 border-t border-slate-850 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Bell className="h-3.5 w-3.5" />
                  Schedule Follow-Up Task?
                </span>
                <input
                  type="checkbox"
                  checked={enableFollowup}
                  onChange={(e) => setEnableFollowup(e.target.checked)}
                  className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-amber-500/40 cursor-pointer"
                />
              </div>

              {enableFollowup && (
                <div className="space-y-3 p-3.5 bg-slate-950/40 border border-amber-500/20 rounded-xl animate-fadeIn">
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-300">Follow-Up Date & Time</label>
                    <input
                      type="datetime-local"
                      value={followupDate}
                      onChange={(e) => setFollowupDate(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-amber-500/50"
                      required={enableFollowup}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-300">Follow-Up Task Note</label>
                    <input
                      type="text"
                      placeholder="e.g. Call back to present fee analysis"
                      value={followupNotes}
                      onChange={(e) => setFollowupNotes(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-amber-500/50"
                    />
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={createMutation.isPending}
              className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-sm rounded-xl transition-all duration-300 shadow-xl shadow-blue-600/20 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer border border-blue-500/30"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving interaction...
                </>
              ) : (
                'Save Interaction Log'
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Timeline & Filters */}
        <div className="lg:col-span-2 space-y-6">
          {/* Filters Bar */}
          <div className="bg-slate-900/25 border border-slate-800/60 p-6 rounded-2xl shadow-lg space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search logs or task notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
                />
              </div>

              <div className="w-full md:w-44">
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
                >
                  <option value="All">Type: All</option>
                  <option value="Call">Call</option>
                  <option value="Email">Email</option>
                  <option value="Meeting">Meeting</option>
                  <option value="Note">Note</option>
                </select>
              </div>

              <div className="w-full md:w-44">
                <select
                  value={prospectFilter}
                  onChange={(e) => setProspectFilter(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
                >
                  <option value="All">Prospect: All</option>
                  {prospects.map((p) => (
                    <option key={p.ein} value={p.ein}>
                      {p.employer_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Timeline Feed */}
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3 bg-slate-900/20 border border-slate-800/40 rounded-2xl">
                <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                <p className="text-slate-400 text-xs font-semibold">Reading interaction log database...</p>
              </div>
            ) : filteredInteractions.length === 0 ? (
              <div className="text-center py-16 px-4 bg-slate-900/20 border border-slate-800/40 rounded-2xl space-y-3">
                <Activity className="h-10 w-10 text-slate-600 mx-auto" />
                <h4 className="text-slate-300 font-bold">No interactions found</h4>
                <p className="text-slate-500 text-xs max-w-xs mx-auto">
                  Log a communication on the left or change your filters to view past client notes.
                </p>
              </div>
            ) : (
              <div className="relative border-l border-slate-800 ml-4 pl-6 space-y-6">
                {filteredInteractions.map((item) => {
                  const followupStatus = getFollowupStatus(item);

                  return (
                    <div key={item.id} className="relative group/card">
                      {/* Bullet marker on timeline */}
                      <div className="absolute -left-[31px] top-1.5 h-4 w-4 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center z-10 group-hover/card:border-blue-500 transition-colors">
                        <div className="h-1.5 w-1.5 rounded-full bg-slate-500 group-hover/card:bg-blue-500 transition-colors" />
                      </div>

                      {/* Log Card */}
                      <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-5 rounded-2xl shadow-lg transition-all duration-300 hover:border-slate-700/80 hover:bg-slate-900/60">
                        <div className="flex justify-between items-start gap-4">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-extrabold text-white text-sm tracking-wide">
                                {item.employer_name || 'General Prospect Log'}
                              </span>
                              <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${getTypeBadgeColor(item.interaction_type)}`}>
                                {item.interaction_type}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-3 text-[10px] text-slate-500 font-medium">
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3 text-slate-600" />
                                Spoke with: <strong className="text-slate-400 font-bold">{item.contact_name}</strong>
                              </span>
                              <span className="flex items-center gap-1 font-mono">
                                <Clock className="h-3 w-3 text-slate-600" />
                                {new Date(item.interaction_date).toLocaleString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                          </div>

                          {/* Card Action Buttons */}
                          <div className="flex items-center gap-1.5 opacity-0 group-hover/card:opacity-100 transition-opacity duration-300">
                            <button
                              onClick={() => openEditModal(item)}
                              className="p-1.5 bg-slate-950 border border-slate-850 rounded-lg text-slate-400 hover:text-white transition-all cursor-pointer"
                              title="Edit log"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm('Delete this interaction log?')) {
                                  deleteMutation.mutate(item.id);
                                }
                              }}
                              disabled={deleteMutation.isPending}
                              className="p-1.5 bg-slate-950 border border-slate-850 rounded-lg text-slate-500 hover:text-rose-400 transition-all cursor-pointer disabled:opacity-50"
                              title="Delete log"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Notes Body */}
                        <div className="mt-4 text-slate-350 text-xs leading-relaxed border-t border-slate-850/50 pt-3 whitespace-pre-wrap">
                          {item.notes}
                        </div>

                        {/* Follow-up Reminder Badge & Completion Checkbox */}
                        {item.followup_date && (
                          <div className="mt-4 pt-3 border-t border-slate-850/40 flex items-center justify-between gap-3">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleFollowupMutation.mutate({ id: item.id })}
                                className="text-slate-400 hover:text-emerald-400 transition-colors cursor-pointer"
                                title={item.followup_completed ? 'Mark incomplete' : 'Mark completed'}
                              >
                                {item.followup_completed ? (
                                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                ) : (
                                  <Circle className="h-4 w-4 text-slate-500 hover:text-emerald-400" />
                                )}
                              </button>

                              <span className={`text-[11px] font-semibold flex items-center gap-1.5 ${
                                item.followup_completed
                                  ? 'line-through text-slate-500'
                                  : followupStatus === 'Overdue'
                                  ? 'text-rose-400'
                                  : followupStatus === 'Today'
                                  ? 'text-amber-400 font-bold'
                                  : 'text-blue-400'
                              }`}>
                                <Bell className="h-3 w-3" />
                                Follow-up: {new Date(item.followup_date).toLocaleString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                                {item.followup_notes && ` — "${item.followup_notes}"`}
                              </span>
                            </div>

                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wider ${
                              item.followup_completed
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : followupStatus === 'Overdue'
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse'
                                : followupStatus === 'Today'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            }`}>
                              {followupStatus}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Interaction Modal */}
      {editingInteraction && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-6 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start border-b border-slate-850 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Edit2 className="h-5 w-5 text-blue-400" />
                  Edit Interaction & Follow-Up
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {editingInteraction.employer_name || 'General log'}
                </p>
              </div>
              <button 
                onClick={() => setEditingInteraction(null)}
                className="p-1 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <User className="h-3.5 w-3.5" />
                  Talked To (Contact Name)
                </label>
                <input
                  type="text"
                  value={editContactName}
                  onChange={(e) => setEditContactName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5" />
                  Interaction Type
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {['Call', 'Email', 'Meeting', 'Note'].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setEditInteractionType(type)}
                      className={`py-2 rounded-xl text-xs font-bold border transition-all duration-300 cursor-pointer ${
                        editInteractionType === type 
                          ? 'bg-blue-600/20 border-blue-500 text-blue-400 font-extrabold shadow-sm'
                          : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                      }`}
                    >
                      {type === 'Call' && '📞 '}
                      {type === 'Email' && '✉️ '}
                      {type === 'Meeting' && '🤝 '}
                      {type === 'Note' && '📝 '}
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  Date & Time
                </label>
                <input
                  type="datetime-local"
                  value={editInteractionDate}
                  onChange={(e) => setEditInteractionDate(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5" />
                  Interaction Notes
                </label>
                <textarea
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500/50 text-sm resize-none"
                  required
                />
              </div>

              {/* Edit Follow-up section */}
              <div className="pt-2 border-t border-slate-850 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Bell className="h-3.5 w-3.5" />
                    Follow-Up Task Enabled
                  </span>
                  <input
                    type="checkbox"
                    checked={editEnableFollowup}
                    onChange={(e) => setEditEnableFollowup(e.target.checked)}
                    className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-amber-500/40 cursor-pointer"
                  />
                </div>

                {editEnableFollowup && (
                  <div className="space-y-3 p-3.5 bg-slate-950/40 border border-amber-500/20 rounded-xl">
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-slate-300">Follow-Up Date & Time</label>
                      <input
                        type="datetime-local"
                        value={editFollowupDate}
                        onChange={(e) => setEditFollowupDate(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-amber-500/50"
                        required={editEnableFollowup}
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-slate-300">Follow-Up Note</label>
                      <input
                        type="text"
                        value={editFollowupNotes}
                        onChange={(e) => setEditFollowupNotes(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-amber-500/50"
                      />
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                      <input
                        type="checkbox"
                        id="edit-completed"
                        checked={editFollowupCompleted}
                        onChange={(e) => setEditFollowupCompleted(e.target.checked)}
                        className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-emerald-500/40 cursor-pointer"
                      />
                      <label htmlFor="edit-completed" className="text-xs font-semibold text-slate-300 cursor-pointer">
                        Mark task as completed
                      </label>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingInteraction(null)}
                  className="flex-1 py-3 bg-slate-950 border border-slate-800 text-slate-400 hover:text-white font-bold text-sm rounded-xl transition-all duration-300 cursor-pointer text-center active:scale-[0.98]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-sm rounded-xl transition-all duration-300 shadow-xl shadow-blue-600/20 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer border border-blue-500/30"
                >
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function InteractionsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    }>
      <InteractionsContent />
    </Suspense>
  );
}
