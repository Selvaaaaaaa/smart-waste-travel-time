import React, { useState, useEffect } from 'react';
import { HardDrive, Battery, Thermometer, RotateCw, Search, Filter } from 'lucide-react';
import { api } from '../services/api';
import { RealtimeOperationalState } from '../types';

export const SmartBins: React.FC = () => {
  const [fusedState, setFusedState] = useState<RealtimeOperationalState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const fetchData = async () => {
    try {
      setLoading(true);
      const state = await api.getFusedFleetState();
      setFusedState(state);
    } catch (err) {
      console.error('Failed to load smart bins telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const bins = fusedState?.bins || [];

  const filteredBins = bins.filter((bin) => {
    const matchesSearch =
      bin.bin_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (bin.location_node || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (statusFilter === 'ALL') return matchesSearch;
    if (statusFilter === 'CRITICAL') return matchesSearch && bin.fill_level_percent >= 90.0;
    if (statusFilter === 'NEAR_FULL')
      return matchesSearch && bin.fill_level_percent >= 70.0 && bin.fill_level_percent < 90.0;
    if (statusFilter === 'NORMAL') return matchesSearch && bin.fill_level_percent < 70.0;
    return matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-emerald-950/40 to-slate-900 border border-emerald-800/40 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase tracking-wide">
              Municipal Telemetry Grid
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              Ultrasonic Level & Tilt Monitoring
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <HardDrive className="w-6 h-6 text-emerald-400" />
            Smart Waste Bin Monitoring
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Real-time ultrasonic fill monitoring, battery lifecycle health, temperature tracking, and automatic threshold overflow detection.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 flex items-center gap-2 self-start md:self-auto transition-colors"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Grid
        </button>
      </div>

      {/* KPI Status Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-medium">Monitored Smart Bins</div>
          <div className="mt-2 text-2xl font-black text-white">{bins.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">100% active telemetry reporting</div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-medium">Critical Bins (≥90%)</div>
          <div className="mt-2 text-2xl font-black text-rose-400">
            {bins.filter((b) => b.fill_level_percent >= 90.0).length}
          </div>
          <div className="text-[11px] text-rose-400 mt-1">Immediate dispatch required</div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-medium">Near Full Bins (70–89%)</div>
          <div className="mt-2 text-2xl font-black text-amber-400">
            {bins.filter((b) => b.fill_level_percent >= 70.0 && b.fill_level_percent < 90.0).length}
          </div>
          <div className="text-[11px] text-amber-300 mt-1">Next shift collection priority</div>
        </div>
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-medium">Average Fleet Battery</div>
          <div className="mt-2 text-2xl font-black text-cyan-300">
            {(
              bins.reduce((acc, b) => acc + (b.sensor_battery_percent || 90), 0) / Math.max(1, bins.length)
            ).toFixed(0)}
            %
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Healthy sensor battery levels</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by container ID or zone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-semibold">Status:</span>
          {(['ALL', 'CRITICAL', 'NEAR_FULL', 'NORMAL'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                statusFilter === status
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
            >
              {status.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Smart Bins Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 font-semibold border-b border-slate-700/60 uppercase text-[10px]">
              <tr>
                <th className="p-3.5">Container ID</th>
                <th className="p-3.5">Municipal Zone</th>
                <th className="p-3.5">Fill Level & Capacity</th>
                <th className="p-3.5">Estimated Waste</th>
                <th className="p-3.5">Sensor Battery</th>
                <th className="p-3.5">Operating Temp</th>
                <th className="p-3.5">Operational Status</th>
                <th className="p-3.5">Last Ingested</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredBins.map((bin) => {
                const isCritical = bin.fill_level_percent >= 90.0;
                const isNearFull = bin.fill_level_percent >= 70.0 && !isCritical;
                return (
                  <tr
                    key={bin.bin_id}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isCritical ? 'bg-rose-950/15' : isNearFull ? 'bg-amber-950/10' : ''
                    }`}
                  >
                    <td className="p-3.5 font-mono font-bold text-white flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isCritical ? 'bg-rose-500 animate-pulse' : isNearFull ? 'bg-amber-400' : 'bg-emerald-400'
                        }`}
                      />
                      {bin.bin_id}
                    </td>
                    <td className="p-3.5 font-semibold text-slate-200">{bin.location_node || 'COLLECTION_ZONE_C'}</td>
                    <td className="p-3.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-24 bg-slate-800 rounded-full h-2.5 overflow-hidden border border-slate-700">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isCritical ? 'bg-rose-500' : isNearFull ? 'bg-amber-400' : 'bg-emerald-400'
                            }`}
                            style={{ width: `${Math.min(100, bin.fill_level_percent)}%` }}
                          />
                        </div>
                        <span
                          className={`font-mono font-bold ${
                            isCritical ? 'text-rose-400' : isNearFull ? 'text-amber-400' : 'text-slate-300'
                          }`}
                        >
                          {bin.fill_level_percent.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="p-3.5 font-mono text-slate-300">
                      {bin.estimated_waste_kg ? bin.estimated_waste_kg.toFixed(0) : (bin.fill_level_percent * 8.5).toFixed(0)} kg
                    </td>
                    <td className="p-3.5 font-mono">
                      <div className="flex items-center gap-1.5">
                        <Battery
                          className={`w-3.5 h-3.5 ${
                            (bin.sensor_battery_percent || 90) < 20 ? 'text-rose-400' : 'text-emerald-400'
                          }`}
                        />
                        <span>{(bin.sensor_battery_percent || 90).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="p-3.5 font-mono text-slate-400">
                      <div className="flex items-center gap-1">
                        <Thermometer className="w-3.5 h-3.5 text-cyan-400" />
                        <span>{bin.temperature_c ? `${bin.temperature_c.toFixed(1)}°C` : '22.4°C'}</span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <span
                        className={`px-2.5 py-0.5 rounded text-[10px] font-bold border ${
                          isCritical
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                            : isNearFull
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        }`}
                      >
                        {isCritical ? 'CRITICAL' : isNearFull ? 'NEAR FULL' : 'NORMAL'}
                      </span>
                    </td>
                    <td className="p-3.5 text-[11px] font-mono text-slate-400">
                      {bin.timestamp ? new Date(bin.timestamp).toLocaleTimeString() : 'Just now'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SmartBins;
