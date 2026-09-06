import React, { useState, useEffect } from 'react';
import { FileText, RotateCw, Filter, Search } from 'lucide-react';
import { api } from '../services/api';
import { AuditEvent } from '../types';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditLog(100);
      setLogs(res || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.entity_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.reason || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (roleFilter === 'ALL') return matchesSearch;
    return matchesSearch && log.role?.toUpperCase() === roleFilter;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-700 text-slate-300 border border-slate-600 uppercase tracking-wide">
              Municipal Governance
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              Immutable Cryptographic Audit Trail
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-slate-300" />
            Operational & Security Audit Logs
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Append-only verification log tracking fleet task dispatches, emergency collections, vehicle breakdowns, dynamic detours, and security role events.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 flex items-center gap-2 self-start md:self-auto transition-colors"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Log
        </button>
      </div>

      {/* Filter and Search Controls */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search action, actor, reason, entity..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-slate-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-semibold">Role:</span>
          {(['ALL', 'DISPATCHER', 'DRIVER', 'MUNICIPAL_SUPERVISOR', 'SYSTEM'] as const).map((role) => (
            <button
              key={role}
              onClick={() => setRoleFilter(role)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                roleFilter === role
                  ? 'bg-slate-700 text-white border border-slate-600'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
            >
              {role.replace('MUNICIPAL_', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 font-semibold border-b border-slate-700/60 uppercase text-[10px]">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">Action Executed</th>
                <th className="p-3.5">Actor & Role</th>
                <th className="p-3.5">Entity Target</th>
                <th className="p-3.5">Operational Reason</th>
                <th className="p-3.5 text-right">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400 text-xs">
                    No matching audit records found.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.event_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3.5 font-bold text-white tracking-wide">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <div className="text-slate-200 font-semibold">{log.actor}</div>
                      <div className="text-[10px] text-slate-400">{log.role}</div>
                    </td>
                    <td className="p-3.5 text-cyan-300 font-bold">
                      {log.entity_type}: {log.entity_id || 'SYSTEM'}
                    </td>
                    <td className="p-3.5 text-slate-300 max-w-xs truncate font-sans text-xs">
                      {log.reason || 'Automated system dispatch execution.'}
                    </td>
                    <td className="p-3.5 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        {log.result || 'SUCCESS'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AuditLogs;
