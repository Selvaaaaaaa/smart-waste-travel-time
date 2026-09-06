import React from 'react';
import { Users, Shield, CheckCircle2 } from 'lucide-react';

export const UsersRoles: React.FC = () => {
  const roles = [
    {
      role: 'Municipal Supervisor',
      code: 'MUNICIPAL_SUPERVISOR',
      badge: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      description: 'Senior municipal authority with full access to strategic policies, fleet audits, and system configuration.',
      usersCount: 3,
      permissions: [
        'Full administrative oversight',
        'Modify safety guardrail tolerances',
        'Approve high-level fleet rebalancing',
        'View complete immutable audit logs',
        'Access full analytics and reporting',
      ],
    },
    {
      role: 'Fleet Dispatcher',
      code: 'DISPATCHER',
      badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
      description: 'Control-room operator managing real-time vehicle routes, collection task assignments, and emergency pickups.',
      usersCount: 8,
      permissions: [
        'Assign and modify collection tasks',
        'Trigger dynamic vehicle rerouting',
        'Approve emergency collection requests',
        'Initiate breakdown vehicle rebalancing',
        'Monitor live telemetry and alerts',
      ],
    },
    {
      role: 'Field Driver',
      code: 'DRIVER',
      badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      description: 'Field vehicle operator receiving in-cab navigation instructions, stop checklists, and route updates.',
      usersCount: 24,
      permissions: [
        'View assigned route and navigation sequence',
        'Acknowledge route detour updates',
        'Report vehicle status and stop completion',
        'Submit breakdown/maintenance alerts',
      ],
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-800/40 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 uppercase tracking-wide">
              Access Control & Security
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              Role-Based Access Control (RBAC)
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-400" />
            Users & Operational Roles
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Cryptographic role-based access management ensuring secure operational separation between dispatchers, drivers, and supervisors.
          </p>
        </div>
      </div>

      {/* Roles Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {roles.map((r) => (
          <div
            key={r.code}
            className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${r.badge}`}>
                  {r.code}
                </span>
                <span className="text-xs text-slate-400 font-mono">{r.usersCount} Active Users</span>
              </div>

              <h3 className="text-base font-bold text-white mt-3">{r.role}</h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{r.description}</p>

              <div className="mt-4 pt-4 border-t border-slate-800">
                <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-indigo-400" />
                  Assigned Privileges
                </div>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {r.permissions.map((perm) => (
                    <li key={perm} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span>{perm}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800 text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Token: Cryptographic Bearer</span>
              <span className="text-emerald-400 font-bold">Active</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UsersRoles;
