'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams, useRouter } from 'next/navigation';
import { auditsService, prospectsService, FiduciaryAudit } from '@/services/api';
import { 
  ShieldAlert, 
  DollarSign, 
  Users, 
  Activity, 
  Calendar,
  AlertTriangle,
  Award,
  Copy,
  Check,
  Download,
  FileText,
  Loader2,
  ChevronDown,
  Building,
  UserCheck
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ReferenceLine, 
  Cell 
} from 'recharts';

function AuditDashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryEin = searchParams.get('ein') || '';
  const queryName = searchParams.get('name') || '';

  const [selectedEin, setSelectedEin] = useState(queryEin);
  const [copied, setCopied] = useState(false);
  const [pitchText, setPitchText] = useState('');

  // Sync state with query parameters
  useEffect(() => {
    if (queryEin) {
      setSelectedEin(queryEin);
    }
  }, [queryEin]);

  // Fetch list of all prospects for the select dropdown
  const { data: prospects = [] } = useQuery({
    queryKey: ['all-prospects-list'],
    queryFn: () => prospectsService.getProspects(),
  });

  // Fetch audit data for the selected plan
  const { data: audit, isLoading, isError, refetch } = useQuery({
    queryKey: ['fiduciary-audit', selectedEin],
    queryFn: () => auditsService.getAudit(selectedEin),
    enabled: !!selectedEin,
  });

  // Generate outreach pitch mutation
  const { mutate: generatePitch, isPending: isPitchPending } = useMutation({
    mutationFn: (companyName: string) => auditsService.generatePitch(selectedEin, companyName),
    onSuccess: (data) => {
      setPitchText(`Subject: ${data.subject}\n\n${data.body}`);
    }
  });

  // Automatically trigger pitch generation when audit is loaded
  useEffect(() => {
    if (audit?.found) {
      const companyName = queryName || prospects.find(p => p.ein === selectedEin)?.employer_name || 'your prospect';
      generatePitch(companyName);
    }
  }, [audit, selectedEin, queryName, prospects, generatePitch]);

  const activeCompanyName = queryName || prospects.find(p => p.ein === selectedEin)?.employer_name || 'your prospect';

  const formatCurrency = (val: number | undefined) => {
    if (val === undefined || val === null) return 'N/A';
    return `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  };

  const formatPercent = (val: number | undefined, decimals = 2) => {
    if (val === undefined || val === null) return 'N/A';
    return `${(val * 100).toFixed(decimals)}%`;
  };

  const getParticipationColor = (rate: number | undefined) => {
    if (rate === undefined) return 'text-slate-400';
    return rate < 0.70 ? 'text-amber-400' : 'text-emerald-400';
  };

  const getFeeColor = (ratio: number | undefined) => {
    if (ratio === undefined) return 'text-slate-400';
    return ratio > 0.0060 ? 'text-rose-400' : 'text-emerald-400';
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(pitchText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSelectEmployer = (ein: string) => {
    const matched = prospects.find(p => p.ein === ein);
    const companyName = matched ? matched.employer_name : 'your prospect';
    setSelectedEin(ein);
    router.push(`/audits?ein=${ein}&name=${encodeURIComponent(companyName)}`);
  };

  return (
    <div className="space-y-8">
      {/* Header & Plan Selection */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
            Fiduciary Diagnostic Audit
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Institutional compliance report & personalized Outreach Script drafting.
          </p>
        </div>

        {/* Plan Selector */}
        <div className="w-full md:w-80 space-y-1.5">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Plan to Audit</label>
          <select
            value={selectedEin}
            onChange={(e) => handleSelectEmployer(e.target.value)}
            className="w-full px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-slate-300 focus:outline-none focus:border-blue-500/50 text-sm cursor-pointer shadow-lg"
          >
            <option value="">-- Choose Employer --</option>
            {prospects.map((p) => (
              <option key={p.ein} value={p.ein}>
                {p.employer_name} (Assets: {formatCurrency(p.total_assets)})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content Pane */}
      {!selectedEin ? (
        <div className="text-center py-32 border-2 border-dashed border-slate-800/80 bg-slate-900/10 rounded-2xl space-y-4">
          <div className="h-16 w-16 rounded-full bg-slate-900/60 text-slate-500 flex items-center justify-center mx-auto shadow-md">
            <ShieldAlert className="h-8 w-8 animate-pulse text-slate-600" />
          </div>
          <h3 className="text-slate-300 font-bold text-lg">No Fiduciary Audit Active</h3>
          <p className="text-slate-500 text-xs max-w-sm mx-auto">
            Select a prospect plan from the dropdown control to load compliance filings and generate pitches.
          </p>
        </div>
      ) : isLoading ? (
        <div className="flex flex-col items-center justify-center py-36 gap-4">
          <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
          <p className="text-slate-400 text-sm font-semibold animate-pulse">Running Fiduciary Audit metrics engine...</p>
        </div>
      ) : !audit || !audit.found ? (
        <div className="text-center py-24 border border-slate-800/80 bg-slate-900/10 rounded-2xl space-y-3">
          <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto" />
          <h4 className="text-slate-300 font-bold">Filing records not found</h4>
          <p className="text-slate-500 text-xs max-w-md mx-auto">
            Filing details for EIN {selectedEin} could not be lazy-audited. Ensure Form 5500 datasets are unzipped.
          </p>
        </div>
      ) : (
        <div className="space-y-8 animate-fadeIn">
          {/* Filing details header */}
          <div className="p-6 bg-slate-900/30 border border-slate-800/50 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="space-y-1">
              <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700/80 px-2 py-0.5 rounded font-bold uppercase">
                {audit.schedule_type === 'H' ? 'Schedule H (Large Plan)' : audit.schedule_type === 'I' ? 'Schedule I (Small Plan)' : 'Form 5500-SF'}
              </span>
              <h3 className="text-xl font-bold text-white tracking-wide">{activeCompanyName}</h3>
              <p className="text-[11px] text-slate-500 font-mono">Employer Identification Number (EIN): {audit.ein}</p>
            </div>

            {/* Branded PDF Download Button */}
            <a
              href={auditsService.getReportPdfUrl(audit.ein)}
              download
              className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-sm rounded-xl transition-all duration-300 shadow-lg shadow-red-600/10 hover:shadow-red-600/20 group cursor-pointer"
            >
              <Download className="h-4 w-4 group-hover:-translate-y-0.5 transition-transform" />
              Download Branded PDF Audit
            </a>
          </div>

          {/* Fiduciary metrics grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Asset card */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-2xl space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Plan Assets (EOY)</span>
              <div className="text-2xl font-bold text-white">{formatCurrency(audit.total_assets)}</div>
              <div className="text-[10px] text-slate-500">Total plan asset valuation</div>
            </div>

            {/* Active participants */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-2xl space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Active Headcount</span>
              <div className="text-2xl font-bold text-white">
                {audit.active_participants ? audit.active_participants.toLocaleString() : '0'}
              </div>
              <div className="text-[10px] text-slate-500">Active participating members</div>
            </div>

            {/* Total eligible */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-2xl space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Eligible / Total universe</span>
              <div className="text-2xl font-bold text-white">
                {audit.total_eligible_employees ? audit.total_eligible_employees.toLocaleString() : '0'}
              </div>
              <div className="text-[10px] text-slate-500">Total workforce eligibility</div>
            </div>

            {/* Admin Expenses */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-2xl space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Admin Expenses</span>
              <div className="text-2xl font-bold text-white">{formatCurrency(audit.admin_expenses)}</div>
              <div className="text-[10px] text-slate-500">Recordkeeping, advice, TPAs</div>
            </div>
          </div>

          {/* Core compliance percentages */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Participation Rate */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl flex flex-col justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Participation Rate</span>
                <div className={`text-4xl font-extrabold ${getParticipationColor(audit.participation_rate)}`}>
                  {formatPercent(audit.participation_rate, 1)}
                </div>
              </div>
              <div className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-4">
                Sponsors generally target a <strong>70% participation threshold</strong> to avoid operational discrimination testing risks.
              </div>
            </div>

            {/* Fee Ratio */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl flex flex-col justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Expense Fee Ratio</span>
                <div className={`text-4xl font-extrabold ${getFeeColor(audit.fee_ratio)}`}>
                  {formatPercent(audit.fee_ratio, 3)}
                </div>
              </div>
              <div className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-4">
                Institutional fee benchmarks are pegged at <strong>60 basis points (0.60%)</strong>. Higher ratios signal high vendor drag.
              </div>
            </div>

            {/* Corrective distributions */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl flex flex-col justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Corrective Distributions</span>
                <div className={`text-4xl font-extrabold ${audit.compliance_failed ? 'text-rose-400' : 'text-slate-300'}`}>
                  {formatCurrency(audit.corrective_distributions)}
                </div>
              </div>
              <div className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-4">
                Non-zero values signal <strong>discrimination testing failures</strong> (ADP/ACP testing issues) in historical operational periods.
              </div>
            </div>
          </div>

          {/* Fiduciary Benchmarks Visualizations (Recharts) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fee Benchmark Chart */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl space-y-4">
              <div>
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Expense Fee Benchmark Comparison</h4>
                <p className="text-xs text-slate-500 mt-1">Comparing plan fee ratio against the 60 bps (0.60%) industry standard.</p>
              </div>
              <div className="relative h-64 w-full bg-slate-950/20 rounded-xl p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: 'This Plan', value: Number((audit.fee_ratio ? audit.fee_ratio * 100 : 0).toFixed(3)), fill: (audit.fee_ratio ? audit.fee_ratio * 100 : 0) > 0.60 ? '#f43f5e' : '#10b981' },
                      { name: 'Benchmark', value: 0.60, fill: '#3b82f6' }
                    ]}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    layout="vertical"
                  >
                    <XAxis type="number" unit="%" domain={[0, Math.max(1.0, Number(((audit.fee_ratio ? audit.fee_ratio * 100 : 0) * 1.5).toFixed(2)))]} stroke="#64748b" fontSize={11} />
                    <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={80} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                      labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                      itemStyle={{ color: '#fff' }}
                      formatter={(value: any) => [`${value}%`, 'Fee Ratio']}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={24}>
                      <Cell fill={(audit.fee_ratio ? audit.fee_ratio * 100 : 0) > 0.60 ? '#f43f5e' : '#10b981'} />
                      <Cell fill="#3b82f6" />
                    </Bar>
                    <ReferenceLine x={0.60} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: '60 bps Limit', fill: '#f43f5e', position: 'top', fontSize: 10 }} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Participation Benchmark Chart */}
            <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl space-y-4">
              <div>
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Active Employee Participation Benchmark</h4>
                <p className="text-xs text-slate-500 mt-1">Comparing plan participation against the 70.0% advisor target.</p>
              </div>
              <div className="relative h-64 w-full bg-slate-950/20 rounded-xl p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: 'This Plan', value: Number((audit.participation_rate ? audit.participation_rate * 100 : 0).toFixed(1)), fill: (audit.participation_rate ? audit.participation_rate * 100 : 0) < 70 ? '#fbbf24' : '#10b981' },
                      { name: 'Target', value: 70.0, fill: '#3b82f6' }
                    ]}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    layout="vertical"
                  >
                    <XAxis type="number" unit="%" domain={[0, 100]} stroke="#64748b" fontSize={11} />
                    <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={80} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                      labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                      itemStyle={{ color: '#fff' }}
                      formatter={(value: any) => [`${value}%`, 'Participation Rate']}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={24}>
                      <Cell fill={(audit.participation_rate ? audit.participation_rate * 100 : 0) < 70 ? '#fbbf24' : '#10b981'} />
                      <Cell fill="#3b82f6" />
                    </Bar>
                    <ReferenceLine x={70} stroke="#10b981" strokeDasharray="3 3" label={{ value: '70% Target', fill: '#10b981', position: 'top', fontSize: 10 }} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Compliance Alerts / Threat cards */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Fiduciary Threat Alerts</h4>
            
            <div className="grid grid-cols-1 gap-4">
              {audit.fee_red_flag && (
                <div className="p-5 bg-rose-500/5 border border-rose-500/30 rounded-2xl flex gap-4 items-center animate-glowRed">
                  <div className="h-10 w-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-lg">🚨</div>
                  <div>
                    <h5 className="font-bold text-rose-300">Excessive Administrative Fees Flagged</h5>
                    <p className="text-xs text-slate-400 mt-0.5">
                      The plan administrative expense ratio of {formatPercent(audit.fee_ratio, 2)} exceeds the 0.60% industry benchmark, compressing participant long-term capital compounding.
                    </p>
                  </div>
                </div>
              )}

              {audit.participation_red_flag && (
                <div className="p-5 bg-amber-500/5 border border-amber-500/30 rounded-2xl flex gap-4 items-center animate-glowAmber">
                  <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-lg">⚠️</div>
                  <div>
                    <h5 className="font-bold text-amber-300">Active Participation Deficit</h5>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Plan participation is below 70% ({formatPercent(audit.participation_rate, 1)}). Operational review of automatic enrollment design features is highly recommended.
                    </p>
                  </div>
                </div>
              )}

              {audit.compliance_failed && (
                <div className="p-5 bg-rose-500/5 border border-rose-500/30 rounded-2xl flex gap-4 items-center animate-glowRed">
                  <div className="h-10 w-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-lg">🚨</div>
                  <div>
                    <h5 className="font-bold text-rose-300">Operational Compliance testing alerts</h5>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Filing reports historical corrective distributions. Tested failures signal missed deferral allocations or operational errors.
                    </p>
                  </div>
                </div>
              )}

              {!audit.fee_red_flag && !audit.participation_red_flag && !audit.compliance_failed && (
                <div className="p-5 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl flex gap-4 items-center">
                  <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-lg">✨</div>
                  <div>
                    <h5 className="font-bold text-emerald-300">Fiduciary Standards Satisfied</h5>
                    <p className="text-xs text-slate-400 mt-0.5">
                      No critical compliance failures, excessive fee ratios, or active employee participation red flags are flagged on the latest DOL Form 5500 filing.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Outreach Script drafting Desk (Phase 3, Step 4) */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Outreach script drafting desk</h4>
              <button
                onClick={handleCopy}
                disabled={isPitchPending}
                className="flex items-center gap-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors cursor-pointer disabled:opacity-50"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied Pitch!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 text-sky-400" />
                    <span>Copy to Clipboard</span>
                  </>
                )}
              </button>
            </div>

            <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-[#FAF8F5] text-slate-800 shadow-2xl p-6 md:p-8 space-y-4 border-t-[8px] border-t-blue-500">
              {isPitchPending ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                  <p className="text-slate-500 text-xs font-semibold">Generating audit-customized advisory pitch script...</p>
                </div>
              ) : (
                <textarea
                  value={pitchText}
                  onChange={(e) => setPitchText(e.target.value)}
                  className="w-full h-80 bg-transparent text-slate-800 focus:outline-none text-sm font-medium leading-relaxed font-sans resize-none"
                  placeholder="Advisor Outreach Pitch Script will generate here..."
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AuditsPage() {
  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      <Suspense fallback={
        <div className="flex flex-col items-center justify-center py-36 gap-4">
          <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
          <p className="text-slate-400 text-sm font-semibold">Loading Fiduciary Audit workspace...</p>
        </div>
      }>
        <AuditDashboard />
      </Suspense>
    </div>
  );
}
