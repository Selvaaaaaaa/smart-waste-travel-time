import React, { useState, useEffect } from 'react';
import { AlertTriangle, RotateCw, CheckCircle, Filter, MapPin, Truck, HardDrive } from 'lucide-react';
import { api } from '../services/api';
import { TelemetryAlert } from '../types';

export const AlertsIncidents: React.FC = () => {
  const [alerts, setAlerts] = useState<TelemetryAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await api.getTelemetryAlerts();
      setAlerts(res || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter === 'ALL') return true;
    return a.severity?.toUpperCase() === severityFilter;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950/40 to-slate-900 border border-amber-900/40 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-wide">
              Municipal Incident Management
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              Active Control Room Stream
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-400" />
            Alerts & Incidents Management
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Real-time telemetry alerts, route deviation detection, container spillover warnings, and mechanical breakdown notifications.
          </p>
        </div>

        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 flex items-center gap-2 self-start md:self-auto transition-colors"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Alerts
        </button>
      </div>

      {/* Severity Filter Strip */}
      <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300">Filter by Severity:</span>
          {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                severityFilter === sev
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Showing {filteredAlerts.length} active alerts
        </span>
      </div>

      {/* Alert Cards List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center text-slate-400 text-xs">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            <p className="font-semibold text-slate-300">No active incidents detected</p>
            <p className="mt-1">All monitored municipal vehicles, containers, and corridors are operating within safe tolerances.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            let badgeBg = 'bg-blue-500/20 text-blue-300 border-blue-500/40';
            if (alert.severity === 'CRITICAL') {
              badgeBg = 'bg-rose-500/20 text-rose-300 border-rose-500/40';
            } else if (alert.severity === 'WARNING') {
              badgeBg = 'bg-amber-500/20 text-amber-300 border-amber-500/40';
            }

            return (
              <div
                key={alert.alert_id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-4 transition-all shadow-md"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 mt-0.5">
                      {alert.entity_id?.startsWith('V-') ? (
                        <Truck className="w-4 h-4 text-cyan-400" />
                      ) : (
                        <HardDrive className="w-4 h-4 text-amber-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badgeBg}`}>
                          {alert.severity}
                        </span>
                        <span className="font-mono text-xs font-bold text-white">{alert.alert_type}</span>
                        <span className="text-[11px] text-slate-400 font-mono">#{alert.alert_id}</span>
                      </div>
                      <p className="text-xs text-slate-200 mt-1 font-medium">{alert.message}</p>
                      <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1 font-mono">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          Entity: {alert.entity_id}
                        </span>
                        <span>
                          Reported: {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-3 text-right self-stretch md:self-auto flex flex-col justify-center">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                      Recommended Operational Action
                    </span>
                    <span className="text-xs font-bold text-emerald-400 mt-0.5">
                      {alert.recovery_action || 'CONTINUE_MONITORING'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AlertsIncidents;
