'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { 
  CreditCard, 
  Check, 
  Sparkles, 
  Zap, 
  ShieldCheck, 
  Activity,
  Layers,
  HelpCircle,
  TrendingUp,
  Cpu
} from 'lucide-react';

export default function BillingPage() {
  const queryClient = useQueryClient();
  const [demoTier, setDemoTier] = useState('pro');

  const plans = [
    {
      id: 'free',
      name: 'Free Basic',
      price: '$0',
      period: 'forever',
      description: 'Essential plan metrics for local prospecting and small advisors.',
      icon: Zap,
      iconColor: 'text-slate-400',
      badgeColor: 'bg-slate-500/10 text-slate-400 border border-slate-500/20',
      features: [
        'Relational SQLite database indexing',
        'Basic assets & headcount filters',
        'Offline fallback contact matching',
        'Standard fiduciary metrics view',
      ],
      limitText: 'Up to 5 manual audits per day',
    },
    {
      id: 'pro',
      name: 'Advisor Pro',
      price: '$129',
      period: 'per month',
      description: 'Power prospecting geofencing and advanced competitor analytics.',
      icon: Sparkles,
      iconColor: 'text-sky-400',
      badgeColor: 'bg-sky-500/10 text-sky-400 border border-sky-500/20',
      features: [
        'Everything in Free Basic',
        'Deep fiduciary audit metrics',
        'Outreach pitch generator desktop',
        'PDF diagnostic report downloads',
        'Apollo/Hunter email contact enrichment',
        'Advanced sorting & sorting algorithms',
      ],
      limitText: 'Unlimited plan audits & exports',
      popular: true,
    },
    {
      id: 'enterprise',
      name: 'Enterprise SaaS',
      price: '$499',
      period: 'per month',
      description: 'The ultimate CRM workspace with background automated registries sweeps.',
      icon: ShieldCheck,
      iconColor: 'text-indigo-400',
      badgeColor: 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20',
      features: [
        'Everything in Advisor Pro',
        '☁️ DOL registries cloud background sync',
        'Full multi-tenant RLS postgres isolation',
        'Priority API contact enrichment quota',
        'Team pipeline workspace collaboration',
        'Custom corporate geofencing boundaries',
      ],
      limitText: 'Full registry databases replication',
    },
  ];

  const handleUpgradeDemo = (tierId: string) => {
    setDemoTier(tierId);
    // Instant mock stripe success callback
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent tracking-tight">
          Subscription Suite
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Manage your Stripe advisor account, select pricing tiers, and explore plan structures.
        </p>
      </div>

      {/* Account Info card */}
      <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="flex gap-4 items-center">
          <div className="p-3 bg-gradient-to-tr from-sky-400 to-indigo-500 text-white rounded-xl shadow-lg">
            <CreditCard className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-white text-lg">Active Account Tier</h4>
              <span className="text-[10px] bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded-full font-semibold capitalize tracking-wide animate-pulse">
                {demoTier} tier active
              </span>
            </div>
            <p className="text-slate-500 text-xs mt-0.5">
              Stripe Customer ID: <span className="font-mono">cus_mock_99d3e8e2b</span> · Renewal Date: June 28, 2026
            </p>
          </div>
        </div>

        <div className="text-slate-400 text-xs border border-slate-800 bg-slate-950/40 px-4 py-3 rounded-xl max-w-xs leading-relaxed">
          ⚡ <strong>Enterprise Node Connected</strong>: PostgreSQL schemas and row level security isolation active.
        </div>
      </div>

      {/* Subscription Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pt-4">
        {plans.map((plan) => {
          const isCurrent = demoTier === plan.id;
          const Icon = plan.icon;

          return (
            <div
              key={plan.id}
              className={`relative flex flex-col justify-between bg-slate-900/30 border p-6 rounded-3xl shadow-xl transition-all duration-300 ${
                plan.popular 
                  ? 'border-sky-500/40 ring-1 ring-sky-500/20 bg-slate-900/50 shadow-sky-500/5 hover:-translate-y-1' 
                  : 'border-slate-800/80 hover:border-slate-700/80'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3.5 left-6 bg-gradient-to-r from-sky-400 to-blue-500 text-white text-[10px] uppercase font-black px-3 py-1 rounded-full shadow-md tracking-wider">
                  Popular Plan
                </span>
              )}

              {/* Title & Price */}
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                  <div className="p-3 bg-slate-950/60 rounded-xl">
                    <Icon className={`h-6 w-6 ${plan.iconColor}`} />
                  </div>
                  {isCurrent && (
                    <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full font-bold uppercase tracking-wide">
                      Active Plan
                    </span>
                  )}
                </div>

                <div className="space-y-1">
                  <h4 className="font-extrabold text-lg text-white tracking-wide">{plan.name}</h4>
                  <p className="text-slate-500 text-xs leading-relaxed">{plan.description}</p>
                </div>

                <div className="flex items-baseline gap-1 pt-2">
                  <span className="text-4xl font-extrabold text-white tracking-tight">{plan.price}</span>
                  <span className="text-slate-500 text-xs font-semibold">{plan.period}</span>
                </div>
              </div>

              {/* Features List */}
              <div className="border-t border-slate-800/60 my-6 pt-6 flex-1">
                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex gap-2.5 items-start text-xs text-slate-400">
                      <Check className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Bottom Action */}
              <div className="space-y-4">
                <button
                  onClick={() => handleUpgradeDemo(plan.id)}
                  disabled={isCurrent}
                  className={`w-full py-3 rounded-xl font-bold text-xs transition-all duration-300 shadow-lg cursor-pointer ${
                    isCurrent
                      ? 'bg-slate-900 border border-slate-800 text-slate-500 cursor-default shadow-none'
                      : plan.popular
                      ? 'bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white shadow-sky-500/10 hover:shadow-sky-500/20'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                  }`}
                >
                  {isCurrent ? 'Current Selection' : `Activate ${plan.name}`}
                </button>
                <div className="text-center text-[10px] text-slate-500 font-medium">
                  {plan.limitText}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Enterprise Security Box */}
      <div className="p-6 bg-indigo-950/10 border border-indigo-500/20 rounded-3xl grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-indigo-400">
            <Cpu className="h-5 w-5 animate-pulse" />
            <h5 className="font-extrabold text-white text-sm uppercase tracking-wider">Multi-Tenant Vault security</h5>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every query executed on our PostgreSQL nodes utilizes Row Level Security (RLS). Fiduciary pipeline updates are isolated using individual tenant UUIDs, protecting corporate directories, contacts, and audits seamlessly under standard OIDC Clerk authorization headers.
          </p>
        </div>

        <div className="flex flex-wrap gap-3 justify-start md:justify-end">
          <span className="text-[10px] bg-slate-950/60 border border-slate-800 text-slate-400 px-3 py-1.5 rounded-xl font-semibold">
            PostgreSQL isolation
          </span>
          <span className="text-[10px] bg-slate-950/60 border border-slate-800 text-slate-400 px-3 py-1.5 rounded-xl font-semibold">
            RLS Policy enforced
          </span>
          <span className="text-[10px] bg-slate-950/60 border border-slate-800 text-slate-400 px-3 py-1.5 rounded-xl font-semibold">
            Stripe SDK configured
          </span>
        </div>
      </div>
    </div>
  );
}
