'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  prospectsService, 
  auditsService, 
  interactionService, 
  agentService,
  Prospect, 
  Interaction 
} from '@/services/api';
import { 
  X, 
  Building2, 
  DollarSign, 
  Users, 
  ShieldAlert, 
  FileText, 
  Download, 
  Copy, 
  Check, 
  Activity, 
  Calendar, 
  Clock, 
  Plus, 
  Phone, 
  Mail, 
  MessageSquare, 
  Loader2, 
  Sparkles, 
  MapPin, 
  Briefcase, 
  Bell, 
  ExternalLink, 
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  User
} from 'lucide-react';

interface ProspectDrawerProps {
  prospect: Prospect | null;
  isOpen: boolean;
  onClose: () => void;
  onStatusChange?: (ein: string, newStatus: string) => void;
}

export default function ProspectDrawer({
  prospect,
  isOpen,
  onClose,
  onStatusChange,
}: ProspectDrawerProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'pitch'>('overview');
  const [copiedPitch, setCopiedPitch] = useState(false);

  // Status Change State
  const [status, setStatus] = useState(prospect?.status || 'Lead');
  const [statusNotes, setStatusNotes] = useState('');

  // Inline Log Form State
  const [contactName, setContactName] = useState(prospect?.contact_name || '');
  const [interactionType, setInteractionType] = useState('Call');
  const [notes, setNotes] = useState('');
  const [enableFollowup, setEnableFollowup] = useState(false);
  const [followupDate, setFollowupDate] = useState('');
  const [followupNotes, setFollowupNotes] = useState('');

  useEffect(() => {
    if (prospect) {
      setStatus(prospect.status);
      setContactName(prospect.contact_name || '');
    }
  }, [prospect]);

  const cleanEin = prospect ? prospect.ein.replace(/\D/g, '').padStart(9, '0') : '';

  // Fetch audit metrics for this prospect
  const { data: audit, isLoading: isAuditLoading } = useQuery({
    queryKey: ['audit', cleanEin],
    queryFn: () => auditsService.getAudit(cleanEin),
    enabled: isOpen && !!cleanEin,
  });

  // Fetch interactions for this prospect
  const { data: interactions = [], isLoading: isInteractionsLoading } = useQuery({
    queryKey: ['interactions', cleanEin],
    queryFn: () => interactionService.getInteractions(cleanEin),
    enabled: isOpen && !!cleanEin,
  });

  // Fetch AI pitch
  const { data: pitch, isLoading: isPitchLoading } = useQuery({
    queryKey: ['pitch', cleanEin],
    queryFn: () => auditsService.generatePitch(cleanEin, prospect?.employer_name || ''),
    enabled: isOpen && !!cleanEin && activeTab === 'pitch',
  });

  // Fetch AI Next Action Recommendation
  const { data: nextAction } = useQuery({
    queryKey: ['nextAction', cleanEin],
    queryFn: () => agentService.getNextAction(cleanEin),
    enabled: isOpen && !!cleanEin && activeTab === 'overview',
  });

  const [isPolishing, setIsPolishing] = useState(false);

  // Status Update Mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ newStatus, note }: { newStatus: string; note: string }) =>
      prospectsService.updateProspectStatus(cleanEin, newStatus, note),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['prospects'] });
      if (onStatusChange) onStatusChange(cleanEin, variables.newStatus);
    },
  });

  // Create Interaction Mutation
  const createInteractionMutation = useMutation({
    mutationFn: (req: any) => interactionService.createInteraction(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions', cleanEin] });
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
      // Reset inline form
      setNotes('');
      setEnableFollowup(false);
      setFollowupDate('');
      setFollowupNotes('');
    },
  });

  // Toggle Followup Mutation
  const toggleFollowupMutation = useMutation({
    mutationFn: ({ id, completed }: { id: string; completed?: boolean }) =>
      interactionService.toggleFollowup(id, completed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions', cleanEin] });
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
  });

  if (!isOpen || !prospect) return null;

  const handleStatusSelect = (newStatus: string) => {
    setStatus(newStatus);
    updateStatusMutation.mutate({ newStatus, note: `Status changed to ${newStatus}` });
  };

  const handleInlineInteractionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;

    createInteractionMutation.mutate({
      prospect_id: cleanEin,
      contact_name: contactName || prospect.contact_name || 'Primary Contact',
      interaction_type: interactionType,
      notes: notes,
      interaction_date: new Date().toISOString(),
      followup_date: enableFollowup && followupDate ? new Date(followupDate).toISOString() : undefined,
      followup_notes: enableFollowup && followupNotes ? followupNotes : undefined,
    });
  };

  const handleCopyPitch = () => {
    if (!pitch) return;
    const textToCopy = `${pitch.subject}\n\n${pitch.body}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedPitch(true);
    setTimeout(() => setCopiedPitch(false), 2500);
  };

  const formattedAssets = prospect.total_assets
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(prospect.total_assets))
    : audit?.total_assets
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(audit.total_assets))
    : '$0';

  const activeParticipants = prospect.participants || audit?.active_participants || 0;
  const avgAssetsPerParticipant = activeParticipants > 0 && (prospect.total_assets || audit?.total_assets)
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(
        Number(prospect.total_assets || audit?.total_assets) / activeParticipants
      )
    : 'N/A';

  const feeBps = audit?.fee_ratio ? Math.round(audit.fee_ratio * 10000) : null;
  const hasFeeFlag = audit?.fee_red_flag || (feeBps && feeBps > 60);
  const hasPartFlag = audit?.participation_red_flag || (audit?.participation_rate && audit.participation_rate < 0.7);
  const hasComplianceFlag = audit?.compliance_failed;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm animate-fadeIn flex justify-end">
      <div 
        className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col justify-between animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 space-y-4 bg-slate-900/80 backdrop-blur-md">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-white tracking-tight">
                  {prospect.employer_name}
                </h2>
                <span className="text-xs font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                  EIN: {prospect.ein}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400 font-medium">
                {prospect.industry && (
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5 text-slate-500" />
                    {prospect.industry}
                  </span>
                )}
                {prospect.provider && (
                  <span className="flex items-center gap-1">
                    <Building2 className="h-3.5 w-3.5 text-slate-500" />
                    {prospect.provider}
                  </span>
                )}
              </div>
            </div>

            <button 
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Quick Action Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            {/* Status Select */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Status:</span>
              <select
                value={status}
                onChange={(e) => handleStatusSelect(e.target.value)}
                disabled={updateStatusMutation.isPending}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs font-bold text-slate-200 focus:outline-none focus:border-blue-500/50 cursor-pointer"
              >
                <option value="Lead">Lead</option>
                <option value="Researching">Researching</option>
                <option value="Cold Called">Cold Called</option>
                <option value="Meeting Set">Meeting Set</option>
                <option value="Disqualified">Disqualified</option>
              </select>
            </div>

            {/* Diagnostic PDF Action Button */}
            <a
              href={auditsService.getReportPdfUrl(cleanEin)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 font-extrabold text-xs rounded-xl transition-all shadow-sm cursor-pointer"
            >
              <Download className="h-3.5 w-3.5" />
              Download Diagnostic PDF
            </a>
          </div>

          {/* Drawer Nav Tabs */}
          <div className="flex border-b border-slate-800 gap-6 pt-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-3 text-xs font-bold border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-400 font-extrabold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="h-4 w-4" />
              5500 Overview & Metrics
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`pb-3 text-xs font-bold border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'activity'
                  ? 'border-blue-500 text-blue-400 font-extrabold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Activity & Logs ({interactions.length})
            </button>
            <button
              onClick={() => setActiveTab('pitch')}
              className={`pb-3 text-xs font-bold border-b-2 transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'pitch'
                  ? 'border-blue-500 text-blue-400 font-extrabold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="h-4 w-4 text-purple-400" />
              AI Outreach Pitch
            </button>
          </div>
        </div>

        {/* Drawer Body Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6 animate-fadeIn">
              {/* AI Strategic Sales Next Action Card */}
              {nextAction && (
                <div className="bg-gradient-to-r from-purple-950/40 via-slate-950 to-indigo-950/40 border border-purple-500/30 p-4 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-extrabold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                      AI Strategic Sales Recommendation
                    </span>
                    <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full ${
                      nextAction.urgency === 'High' 
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
                        : nextAction.urgency === 'Medium'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {nextAction.urgency} Urgency
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white tracking-tight">{nextAction.recommended_action}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">{nextAction.reasoning}</p>
                </div>
              )}

              {/* Financial Metrics Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Total Plan Assets</span>
                  <p className="text-2xl font-extrabold text-white">{formattedAssets}</p>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Active Participants</span>
                  <p className="text-2xl font-extrabold text-white">{activeParticipants.toLocaleString()}</p>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Avg Asset / Employee</span>
                  <p className="text-xl font-bold text-slate-200">{avgAssetsPerParticipant}</p>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Plan Admin Fee Bps</span>
                  <p className={`text-xl font-bold ${hasFeeFlag ? 'text-rose-400 font-extrabold' : 'text-slate-200'}`}>
                    {feeBps ? `${feeBps} bps` : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Fiduciary Audit Red Flags */}
              <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-xl space-y-3">
                <h4 className="text-xs font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  Fiduciary Diagnostic Findings
                </h4>

                <div className="space-y-2">
                  {hasFeeFlag ? (
                    <div className="flex items-start gap-2.5 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
                      <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-bold">Excessive Fee Ratio Alert:</strong> Plan fee ratio ({feeBps} bps) exceeds the 60 bps institutional benchmark. High potential for vendor fee compression.
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 p-2.5 bg-slate-900 border border-slate-850 rounded-lg text-slate-400 text-xs">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                      Plan fee ratio is within standard institutional guidelines.
                    </div>
                  )}

                  {hasPartFlag ? (
                    <div className="flex items-start gap-2.5 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 text-xs">
                      <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-bold">Participation Gap Alert:</strong> Active participant engagement is below the 70% benchmark target. Candidate for auto-enrollment design.
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 p-2.5 bg-slate-900 border border-slate-850 rounded-lg text-slate-400 text-xs">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                      Employee participation rate meets benchmark target.
                    </div>
                  )}

                  {hasComplianceFlag ? (
                    <div className="flex items-start gap-2.5 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg text-purple-300 text-xs">
                      <ShieldAlert className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-bold">Compliance Testing Failure:</strong> Historic Form 5500 records show corrective distributions for non-discrimination testing failures.
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>

              {/* Company & Contact Information */}
              <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-xl space-y-4">
                <h4 className="text-xs font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                  <User className="h-4 w-4 text-blue-400" />
                  Contact & Plan Administrator Info
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-500 font-medium">Primary Contact:</span>
                    <p className="text-slate-200 font-bold mt-0.5">{prospect.contact_name || 'Not Specified'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 font-medium">Contact Email:</span>
                    <p className="text-slate-200 font-bold mt-0.5">{prospect.contact_email || 'Not Specified'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 font-medium">Contact Phone:</span>
                    <p className="text-slate-200 font-bold mt-0.5">{prospect.contact_phone || 'Not Specified'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 font-medium">Plan Administrator:</span>
                    <p className="text-slate-200 font-bold mt-0.5">{audit?.schedule_type || prospect.provider || '5500 Sponsor'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ACTIVITY & INTERACTION LOGS */}
          {activeTab === 'activity' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Quick Inline Log Creation Form */}
              <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-4">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Plus className="h-4 w-4 text-blue-400" />
                  Log Call / Note for {prospect.employer_name}
                </h4>

                <form onSubmit={handleInlineInteractionSubmit} className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="Contact Name"
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                      className="px-3 py-2 bg-slate-900 border border-slate-850 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500/50"
                      required
                    />
                    <select
                      value={interactionType}
                      onChange={(e) => setInteractionType(e.target.value)}
                      className="px-3 py-2 bg-slate-900 border border-slate-850 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500/50 cursor-pointer"
                    >
                      <option value="Call">📞 Call</option>
                      <option value="Email">✉️ Email</option>
                      <option value="Meeting">🤝 Meeting</option>
                      <option value="Note">📝 Note</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Notes</span>
                      <button
                        type="button"
                        onClick={async () => {
                          if (!notes.trim()) return;
                          setIsPolishing(true);
                          try {
                            const res = await agentService.summarizeNotes(notes, contactName, prospect.employer_name);
                            setNotes(res.polished_notes);
                            if (res.suggested_followup_days) {
                              setEnableFollowup(true);
                              const target = new Date();
                              target.setDate(target.getDate() + res.suggested_followup_days);
                              setFollowupDate(target.toISOString().slice(0, 16));
                              if (res.suggested_followup_note) setFollowupNotes(res.suggested_followup_note);
                            }
                          } catch (err) {
                            console.error(err);
                          } finally {
                            setIsPolishing(false);
                          }
                        }}
                        disabled={isPolishing || !notes.trim()}
                        className="text-[10px] font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30 cursor-pointer disabled:opacity-40"
                      >
                        {isPolishing ? <Loader2 className="h-3 w-3 animate-spin text-purple-400" /> : <Sparkles className="h-3 w-3 text-purple-400" />}
                        AI Polish Notes
                      </button>
                    </div>
                    <textarea
                      placeholder="Log discussion details or meeting notes..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-850 rounded-lg text-slate-200 text-xs focus:outline-none focus:border-blue-500/50 resize-none"
                      required
                    />
                  </div>

                  {/* Optional follow-up checkbox inside drawer */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                        <Bell className="h-3 w-3" />
                        Set Follow-up Task?
                      </span>
                      <input
                        type="checkbox"
                        checked={enableFollowup}
                        onChange={(e) => setEnableFollowup(e.target.checked)}
                        className="h-3.5 w-3.5 rounded bg-slate-900 border-slate-850 text-amber-500 focus:ring-amber-500/40 cursor-pointer"
                      />
                    </div>

                    {enableFollowup && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 p-2.5 bg-slate-900/60 border border-amber-500/20 rounded-lg">
                        <input
                          type="datetime-local"
                          value={followupDate}
                          onChange={(e) => setFollowupDate(e.target.value)}
                          className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 text-xs"
                          required={enableFollowup}
                        />
                        <input
                          type="text"
                          placeholder="Follow-up note"
                          value={followupNotes}
                          onChange={(e) => setFollowupNotes(e.target.value)}
                          className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 text-xs"
                        />
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={createInteractionMutation.isPending}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-all shadow-md active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    {createInteractionMutation.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      'Save Interaction'
                    )}
                  </button>
                </form>
              </div>

              {/* Timeline Feed */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Past Interactions ({interactions.length})
                </h4>

                {isInteractionsLoading ? (
                  <div className="flex justify-center py-10">
                    <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
                  </div>
                ) : interactions.length === 0 ? (
                  <div className="text-center py-10 bg-slate-950/30 border border-slate-850 rounded-xl">
                    <p className="text-slate-500 text-xs font-medium">No interactions recorded for this prospect yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {interactions.map((item) => (
                      <div key={item.id} className="p-4 bg-slate-950/60 border border-slate-850 rounded-xl space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{item.contact_name}</span>
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-300">
                              {item.interaction_type}
                            </span>
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {new Date(item.interaction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </span>
                        </div>

                        <p className="text-xs text-slate-300 whitespace-pre-wrap">{item.notes}</p>

                        {item.followup_date && (
                          <div className="pt-2 border-t border-slate-850/60 flex items-center justify-between text-[11px]">
                            <span className="text-amber-400 flex items-center gap-1 font-medium">
                              <Bell className="h-3 w-3" />
                              Follow-up: {new Date(item.followup_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              {item.followup_notes && ` — "${item.followup_notes}"`}
                            </span>
                            <button
                              onClick={() => toggleFollowupMutation.mutate({ id: item.id })}
                              className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1 cursor-pointer"
                            >
                              {item.followup_completed ? (
                                <span className="text-emerald-400 font-bold flex items-center gap-1">
                                  <CheckCircle2 className="h-3.5 w-3.5" /> Done
                                </span>
                              ) : (
                                <span className="text-slate-400 hover:text-emerald-400 flex items-center gap-1">
                                  <CheckCircle2 className="h-3.5 w-3.5" /> Mark Done
                                </span>
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: AI OUTREACH PITCH */}
          {activeTab === 'pitch' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4 text-purple-400" />
                  Customized Outreach Pitch
                </span>
                <button
                  onClick={handleCopyPitch}
                  disabled={!pitch || isPitchLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-300 font-bold text-xs rounded-xl transition-all cursor-pointer disabled:opacity-50"
                >
                  {copiedPitch ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Copy Outreach Pitch
                    </>
                  )}
                </button>
              </div>

              {isPitchLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3 bg-slate-950/40 border border-slate-800 rounded-xl">
                  <Loader2 className="h-8 w-8 text-purple-400 animate-spin" />
                  <p className="text-slate-400 text-xs font-semibold">Generating customized fiduciary pitch...</p>
                </div>
              ) : pitch ? (
                <div className="bg-slate-950/80 border border-slate-800 p-5 rounded-xl space-y-4">
                  <div className="border-b border-slate-850 pb-3">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Subject Line</span>
                    <h4 className="text-sm font-bold text-white mt-0.5">{pitch.subject}</h4>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Email Copy</span>
                    <div className="mt-2 text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                      {pitch.body}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-10 bg-slate-950/40 border border-slate-800 rounded-xl">
                  <p className="text-slate-400 text-xs font-medium">Could not generate outreach pitch at this time.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
