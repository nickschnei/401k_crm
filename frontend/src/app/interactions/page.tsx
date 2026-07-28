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
  X
} from 'lucide-react';

function InteractionsContent() {
  const queryClient = useQueryClient();

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [prospectFilter, setProspectFilter] = useState('All');

  // Form State (Create / Edit)
  const [prospectId, setProspectId] = useState('');
  const [contactName, setContactName] = useState('');
  const [interactionType, setInteractionType] = useState('Call');
  const [notes, setNotes] = useState('');
  const [interactionDate, setInteractionDate] = useState(
    new Date().toISOString().slice(0, 16) // Default local datetime string
  );
  
  // Edit Modal State
  const [editingInteraction, setEditingInteraction] = useState<Interaction | null>(null);
  const [editContactName, setEditContactName] = useState('');
  const [editInteractionType, setEditInteractionType] = useState('Call');
  const [editNotes, setEditNotes] = useState('');
  const [editInteractionDate, setEditInteractionDate] = useState('');

  // Fetch all prospects (for the dropdown list)
  const { data: prospects = [] } = useQuery({
    queryKey: ['prospects'],
    queryFn: () => prospectsService.getProspects(),
  });

  // Fetch all interactions
  const { data: interactions = [], isLoading, isRefetching, refetch } = useQuery({
    queryKey: ['interactions'],
    queryFn: () => interactionService.getInteractions(),
  });

  // Create Interaction Mutation
  const createMutation = useMutation({
    mutationFn: (req: {
      prospect_id?: string;
      contact_name: string;
      interaction_type: string;
      notes: string;
      interaction_date?: string;
    }) => interactionService.createInteraction(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
      // Reset form
      setProspectId('');
      setContactName('');
      setInteractionType('Call');
      setNotes('');
      setInteractionDate(new Date().toISOString().slice(0, 16));
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
    const selected = prospects.find(p => p.ein === id || p.employer_name === id); // Sourced by either
    
    // In our api response, getProspects returns list where Prospect has ein/employer_name/contact_name.
    // Let's resolve the actual prospect details.
    if (selected && selected.contact_name) {
      setContactName(selected.contact_name);
    } else {
      // Find prospect by employer name or EIN matches
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

    // Find actual Prospect model ID using EIN/Name
    const matchingProspect = prospects.find(p => p.ein === prospectId || p.employer_name === prospectId);
    
    createMutation.mutate({
      prospect_id: matchingProspect ? matchingProspect.ein : undefined, // In SQLite database models, prospect_id points to the prospect's uuid, but prospects list from API uses 'ein' as unique keys in the table rows.
      contact_name: contactName,
      interaction_type: interactionType,
      notes: notes,
      interaction_date: new Date(interactionDate).toISOString(),
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
      },
    });
  };

  const openEditModal = (interaction: Interaction) => {
    setEditingInteraction(interaction);
    setEditContactName(interaction.contact_name);
    setEditInteractionType(interaction.interaction_type);
    setEditNotes(interaction.notes);
    setEditInteractionDate(new Date(interaction.interaction_date).toISOString().slice(0, 16));
  };

  // Metrics calculations
  const totalLogs = interactions.length;
  const callsCount = interactions.filter(i => i.interaction_type === 'Call').length;
  const emailsCount = interactions.filter(i => i.interaction_type === 'Email').length;
  const meetingsCount = interactions.filter(i => i.interaction_type === 'Meeting').length;

  // Filtered interactions
  const filteredInteractions = interactions.filter(item => {
    const matchesSearch = 
      item.contact_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.notes.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.employer_name && item.employer_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = typeFilter === 'All' || item.interaction_type === typeFilter;
    const matchesProspect = prospectFilter === 'All' || item.ein === prospectFilter || item.prospect_id === prospectFilter;

    return matchesSearch && matchesType && matchesProspect;
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
            Interaction Log Workspace
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Record, track, and manage client communications and notes for active prospects.
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

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-sky-500/30">
          <div className="absolute top-0 right-0 h-20 w-20 bg-sky-500/5 rounded-full blur-xl" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Total Logs</span>
              <h3 className="text-3xl font-extrabold text-white tracking-tight">{totalLogs}</h3>
            </div>
            <div className="p-2.5 bg-sky-500/10 rounded-xl text-sky-400">
              <FileText className="h-5 w-5" />
            </div>
          </div>
        </div>

        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30">
          <div className="absolute top-0 right-0 h-20 w-20 bg-blue-500/5 rounded-full blur-xl" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Calls Made</span>
              <h3 className="text-3xl font-extrabold text-white tracking-tight">{callsCount}</h3>
            </div>
            <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400">
              <Phone className="h-5 w-5" />
            </div>
          </div>
        </div>

        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-purple-500/30">
          <div className="absolute top-0 right-0 h-20 w-20 bg-purple-500/5 rounded-full blur-xl" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Emails Sent</span>
              <h3 className="text-3xl font-extrabold text-white tracking-tight">{emailsCount}</h3>
            </div>
            <div className="p-2.5 bg-purple-500/10 rounded-xl text-purple-400">
              <Mail className="h-5 w-5" />
            </div>
          </div>
        </div>

        <div className="relative group overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 p-6 rounded-2xl shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-emerald-500/30">
          <div className="absolute top-0 right-0 h-20 w-20 bg-emerald-500/5 rounded-full blur-xl" />
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">Meetings Set</span>
              <h3 className="text-3xl font-extrabold text-white tracking-tight">{meetingsCount}</h3>
            </div>
            <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-400">
              <Users className="h-5 w-5" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Left Column: Log Form */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-6">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus className="h-5 w-5 text-blue-400" />
              Log New Interaction
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Add details about your latest client interaction.
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
                rows={5}
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm resize-none"
                required
              />
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
                  placeholder="Search logs by keyword or contact person..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
                />
              </div>

              <div className="w-full md:w-48">
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

              <div className="w-full md:w-48">
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
                {filteredInteractions.map((item) => (
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
                            title="Edit notes"
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
                    </div>
                  </div>
                ))}
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
                  Edit Interaction Log
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
                  rows={5}
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500/50 text-sm resize-none"
                  required
                />
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
