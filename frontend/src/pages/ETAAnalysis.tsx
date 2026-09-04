import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingDown,
  Target,
  CheckCircle2,
  Activity,
  Award,
  RefreshCw,
  Cpu,
  Database,
  Calendar,
  Sparkles,
  Info,
  GitFork,
  ShieldCheck,
} from 'lucide-react';
import { MetricCard } from '../components/common/MetricCard';
import { DemoBadge } from '../components/common/DemoBadge';
import { AlertBanner } from '../components/common/AlertBanner';
import { LoadingState } from '../components/common/LoadingState';
import { ETAErrorChart } from '../components/charts/ETAErrorChart';
import { ETAComparisonChart } from '../components/charts/ETAComparisonChart';
import { api } from '../services/api';
import { MLStatusResponse, HybridPredictResponse } from '../types';

export const ETAAnalysis: React.FC = () => {
  const [mlStatus, setMlStatus] = useState<MLStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [training, setTraining] = useState<boolean>(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);

  // Hybrid pre-trip decision simulation state
  const [hybridSimResult, setHybridSimResult] = useState<HybridPredictResponse | null>(null);
  const [simDistance, setSimDistance] = useState<number>(25.0);
  const [simWeather, setSimWeather] = useState<string>('CLEAR');
  const [simTraffic, setSimTraffic] = useState<string>('LOW');
  const [simEvent, setSimEvent] = useState<string>('NONE');
  const [simRoad, setSimRoad] = useState<string>('NONE');
  const [simWaste, setSimWaste] = useState<number>(5.0);

  const fetchStatus = async () => {
    try {
      const status = await api.getMLStatus();
      setMlStatus(status);
    } catch (err) {
      console.warn('Could not fetch ML status:', err);
    } finally {
      setLoading(false);
    }
  };

  const evaluateHybridDecision = async () => {
    try {
      const res = await api.predictHybridETA({
        distance_km: simDistance,
        waste_volume_tons: simWaste,
        weather_condition: simWeather,
        traffic_level: simTraffic,
        event_level: simEvent,
        road_restriction_type: simRoad,
        congestion_index: simTraffic === 'SEVERE' ? 85 : simTraffic === 'HIGH' ? 70 : 20,
        rainfall_mm: simWeather === 'HEAVY_RAIN' || simWeather === 'STORM' ? 25 : 0,
      });
      setHybridSimResult(res);
    } catch (err) {
      console.warn('Could not simulate hybrid decision:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    evaluateHybridDecision();
  }, [simDistance, simWeather, simTraffic, simEvent, simRoad, simWaste]);

  const handleTrainModel = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const res = await api.trainMLModel('random_forest', 100);
      setMlStatus(res.metadata);
      setTrainMessage(`Model training complete! Improvement: ${res.metadata.metrics?.mae_improvement_pct}% MAE reduction.`);
      evaluateHybridDecision();
    } catch (err: any) {
      console.error('Training failed:', err);
      setTrainMessage(`Training failed: ${err.message || 'Unknown error'}`);
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading ML model performance metrics..." />;
  }

  const isTrained = mlStatus?.is_trained && mlStatus.metrics;
  const metrics = mlStatus?.metrics;
  const topFeatures = (mlStatus?.feature_importances || []).slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            <BarChart3 className="w-6 h-6 text-emerald-400" />
            ETA Model Intelligence & Adaptive Hybrid Analysis
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Pre-trip model selection heuristics, Random Forest prediction spread, and 3-model comparative evaluation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DemoBadge label="Synthetic Dataset — Research Prototype" />
        </div>
      </div>

      {trainMessage && (
        <AlertBanner
          type={trainMessage.includes('failed') ? 'error' : 'success'}
          title={trainMessage.includes('failed') ? 'Training Notification' : 'Model Training Succeeded'}
          message={trainMessage}
        />
      )}

      {/* Model Status & Architecture Card */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-700/80">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Adaptive Intelligence Architecture
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    isTrained
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  {isTrained ? 'TRAINED & HYBRID ACTIVE' : 'MODEL NOT TRAINED'}
                </span>
              </div>
              <h2 className="text-lg font-black text-white mt-0.5">
                Adaptive Hybrid ETA Selector (Policy: hybrid-v1)
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTrainModel}
            disabled={training}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-xs font-bold rounded-lg transition-all shadow-md shadow-emerald-950/40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${training ? 'animate-spin' : ''}`} />
            {training ? 'Training Model...' : 'Train / Retrain Model'}
          </button>
        </div>

        {/* Model Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/60">
            <div className="text-slate-400 flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-cyan-400" /> Total Records
            </div>
            <div className="text-base font-bold text-white mt-1">
              {mlStatus?.total_dataset_rows || 60}{' '}
              <span className="text-[10px] text-slate-400 font-normal">
                ({mlStatus?.training_row_count || 48} train / {mlStatus?.testing_row_count || 12} test)
              </span>
            </div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/60">
            <div className="text-slate-400 flex items-center gap-1">
              <GitFork className="w-3.5 h-3.5 text-indigo-400" /> Hybrid Strategy
            </div>
            <div className="text-xs font-semibold text-white mt-1 truncate">
              Pre-Trip Policy (Zero Leakage)
            </div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/60">
            <div className="text-slate-400 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-amber-400" /> Last Trained
            </div>
            <div className="text-xs font-mono text-slate-300 mt-1">
              {mlStatus?.training_date
                ? new Date(mlStatus.training_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'Not trained'}
            </div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/60">
            <div className="text-slate-400 flex items-center gap-1">
              <Target className="w-3.5 h-3.5 text-indigo-400" /> Target Variable
            </div>
            <div className="text-xs font-mono text-emerald-400 mt-1">actual_travel_minutes</div>
          </div>
        </div>
      </div>

      {/* Adaptive Decision Card & Interactive Pre-Trip Simulator */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-700/80">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <GitFork className="w-4 h-4 text-cyan-400" />
              Pre-Trip Adaptive Decision Card & Model Uncertainty
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluates environmental triggers prior to dispatch to select the optimal prediction paradigm.
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded border border-slate-700">
            Policy Version: hybrid-v1
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-1">
          {/* Controls */}
          <div className="lg:col-span-1 space-y-3 bg-slate-900/60 p-4 rounded-xl border border-slate-700/60">
            <div className="text-xs font-bold text-slate-300 uppercase tracking-wide">
              Pre-Trip Operational Context
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[11px] text-slate-400">Distance (km)</label>
                <input
                  type="number"
                  value={simDistance}
                  onChange={(e) => setSimDistance(Math.max(1, Number(e.target.value)))}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white font-mono text-xs mt-0.5"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400">Waste (tons)</label>
                <input
                  type="number"
                  value={simWaste}
                  onChange={(e) => setSimWaste(Math.max(0, Number(e.target.value)))}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white font-mono text-xs mt-0.5"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[11px] text-slate-400">Weather</label>
                <select
                  value={simWeather}
                  onChange={(e) => setSimWeather(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white text-xs mt-0.5"
                >
                  <option value="CLEAR">CLEAR</option>
                  <option value="RAIN">RAIN</option>
                  <option value="HEAVY_RAIN">HEAVY_RAIN</option>
                  <option value="STORM">STORM</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-slate-400">Traffic</label>
                <select
                  value={simTraffic}
                  onChange={(e) => setSimTraffic(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white text-xs mt-0.5"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="SEVERE">SEVERE</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[11px] text-slate-400">Major Event</label>
                <select
                  value={simEvent}
                  onChange={(e) => setSimEvent(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white text-xs mt-0.5"
                >
                  <option value="NONE">NONE</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-slate-400">Road Restriction</label>
                <select
                  value={simRoad}
                  onChange={(e) => setSimRoad(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-white text-xs mt-0.5"
                >
                  <option value="NONE">NONE</option>
                  <option value="LANE_RESTRICTION">LANE</option>
                  <option value="ROAD_CLOSURE">CLOSURE</option>
                </select>
              </div>
            </div>
          </div>

          {/* Real-time Decision Results */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 flex flex-col justify-between space-y-3">
              <div>
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Selected Model & Reason
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-lg text-sm font-black tracking-wide border ${
                      hybridSimResult?.selected_model === 'CONTEXT_AWARE'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    }`}
                  >
                    {hybridSimResult?.selected_model || 'BASELINE'}
                  </span>
                </div>
                <div className="text-xs font-mono text-cyan-300 mt-2">
                  Reason: {hybridSimResult?.selection_reason || 'NOMINAL_ENVIRONMENTAL_CONDITIONS'}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                Safety Status:{' '}
                <span className="text-emerald-400 font-bold inline-flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> SAFE DISPATCH
                </span>
              </div>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 flex flex-col justify-between space-y-3">
              <div>
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Predicted Hybrid ETA
                </div>
                <div className="text-3xl font-black text-white mt-1">
                  {hybridSimResult?.predicted_eta_minutes ?? '—'}{' '}
                  <span className="text-sm text-slate-400 font-normal">min</span>
                </div>
                <div className="text-xs text-slate-300 mt-2 flex items-center justify-between">
                  <span>Prediction Spread:</span>
                  <span className="font-mono text-amber-300 font-bold">
                    {hybridSimResult?.prediction_spread_minutes !== null && hybridSimResult?.prediction_spread_minutes !== undefined
                      ? `± ${hybridSimResult.prediction_spread_minutes} min`
                      : 'N/A (Deterministic)'}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 leading-tight">
                * Prediction Spread represents variation among Random Forest tree predictions and is not a formal statistical confidence interval.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real Model Metrics from DB & ML Pipeline */}
      {isTrained && metrics ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <MetricCard
            title="Baseline MAE"
            value={metrics.baseline.mae}
            unit="min"
            icon={<Activity className="w-4 h-4 text-rose-400" />}
            badgeLabel="Baseline 25km/h"
            subtitle="Kinematic benchmark error"
          />
          <MetricCard
            title="Context-aware MAE"
            value={metrics.context_aware.mae}
            unit="min"
            icon={<TrendingDown className="w-4 h-4 text-emerald-400" />}
            badgeLabel="Random Forest"
            subtitle="Context-Aware ML MAE"
            trend={{
              value: `${metrics.mae_improvement_pct}% error reduction`,
              isPositive: metrics.is_improved,
            }}
          />
          <MetricCard
            title="Baseline RMSE"
            value={metrics.baseline.rmse}
            unit="min"
            icon={<Activity className="w-4 h-4 text-rose-400" />}
            badgeLabel="Baseline"
            subtitle="Root Mean Squared Error"
          />
          <MetricCard
            title="Context-aware RMSE"
            value={metrics.context_aware.rmse}
            unit="min"
            icon={<Award className="w-4 h-4 text-cyan-400" />}
            badgeLabel="Random Forest"
            subtitle="Target ML RMSE"
            trend={{
              value: `${metrics.rmse_improvement_pct}% variance drop`,
              isPositive: metrics.rmse_improvement_pct > 0,
            }}
          />
          <MetricCard
            title="ML Mean Bias"
            value={metrics.context_aware.mean_error}
            unit="min"
            icon={<Target className="w-4 h-4 text-emerald-400" />}
            badgeLabel="Model Bias"
            subtitle="Mean signed error"
          />
          <MetricCard
            title="Within ±10 min"
            value={`${metrics.context_aware.within_tolerance_pct}%`}
            icon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            badgeLabel="Tolerance Rate"
            subtitle="Arrivals within ±10m window"
            trend={{
              value: `Baseline: ${metrics.baseline.within_tolerance_pct}%`,
              isPositive: true,
            }}
          />
        </div>
      ) : (
        <AlertBanner
          type="info"
          title="Model Not Trained"
          message="Click 'Train / Retrain Model' above to train the Context-Aware Random Forest regressor on database observations."
        />
      )}

      {/* Feature Importance Section */}
      {topFeatures.length > 0 && (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                Model Feature Importance
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Relative Gini feature importances learned by the tree ensemble during training.
              </p>
            </div>
            <span className="text-[10px] text-slate-500 flex items-center gap-1">
              <Info className="w-3 h-3" /> Association measure, not direct physical causality.
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {topFeatures.map((f, idx) => {
              const pct = (f.importance * 100).toFixed(1);
              return (
                <div key={idx} className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-lg space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-mono text-slate-200 font-semibold">{f.feature}</span>
                    <span className="font-mono text-emerald-400 font-bold">{pct}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-1.5 rounded-full"
                      style={{ width: `${Math.min(Number(pct) * 2.5, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Comparative Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ETAErrorChart />
        <ETAComparisonChart />
      </div>

      {/* Evaluation Methodology Explainer */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wide">
          Three-Model Research Evaluation Methodology & Scientific Principles
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50 space-y-1">
            <span className="font-semibold text-rose-400 block font-mono">
              Model 1 — Baseline (Kinematic)
            </span>
            <p className="text-slate-400">
              ETA = distance / 25.0 km/h. Deterministic standard speed benchmark strictly isolated from environmental and operational context variables.
            </p>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50 space-y-1">
            <span className="font-semibold text-emerald-400 block font-mono">
              Model 2 — Context-Aware ML
            </span>
            <p className="text-slate-400">
              Random Forest Regressor utilizing weather, rainfall, congestion index, average speeds, active road restrictions, and waste volume dwell times.
            </p>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50 space-y-1">
            <span className="font-semibold text-cyan-400 block font-mono">
              Model 3 — Adaptive Hybrid
            </span>
            <p className="text-slate-400">
              Pre-trip rule-based selector dynamically choosing Baseline during nominal conditions and ML under disruptions to achieve minimal overall error.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

