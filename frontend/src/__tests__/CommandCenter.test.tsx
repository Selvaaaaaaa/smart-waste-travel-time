import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { CommandCenter } from '../pages/CommandCenter';

// Mock API service
vi.mock('../services/api', () => {
  const mockHealth = {
    status: 'HEALTHY',
    service: 'Smart Waste Travel Time Simulator',
    phase: 2,
    database: { status: 'CONNECTED', latency_ms: 0.45 },
    telemetry: { status: 'ACTIVE', health_rate_pct: 100.0 },
    websocket: { status: 'CONNECTED', connected_clients: 1 },
    simulation: { status: 'READY' },
  };

  const mockDemoState = {
    status: 'COMPLETED',
    current_step: 21,
    total_steps: 21,
    elapsed_seconds: 1.67,
    active_scenario: 'FULL_SYSTEM_DEMO',
    safe_allocation_rate: 100.0,
    safety_violations: 0,
    deviations_detected: 1,
    breakdown_handled: true,
    emergency_inserted: true,
    step_logs: [
      {
        step: 1,
        timestamp: '2026-09-06T12:00:01Z',
        action: 'INITIALIZE_SIMULATION_ENVIRONMENT',
        subsystem: 'SYSTEM',
        status: 'PASS',
        details: { seed: 42, initial_vehicles: 4 },
      },
      {
        step: 21,
        timestamp: '2026-09-06T12:00:21Z',
        action: 'FINAL_SYSTEM_STATUS_ASSESSMENT',
        subsystem: 'SYSTEM',
        status: 'PASS',
        details: { verdict: 'ALL_STEPS_COMPLETED' },
      },
    ],
    steps_log: [
      {
        step: 1,
        timestamp: '2026-09-06T12:00:01Z',
        action: 'INITIALIZE_SIMULATION_ENVIRONMENT',
        subsystem: 'SYSTEM',
        status: 'PASS',
        details: { seed: 42, initial_vehicles: 4 },
      },
      {
        step: 21,
        timestamp: '2026-09-06T12:00:21Z',
        action: 'FINAL_SYSTEM_STATUS_ASSESSMENT',
        subsystem: 'SYSTEM',
        status: 'PASS',
        details: { verdict: 'ALL_STEPS_COMPLETED' },
      },
    ],
  };

  const mockBenchmarks = {
    total_runs: 50,
    scenarios_count: 10,
    seeds_evaluated: [42, 43, 44, 45, 46],
    eta_accuracy: {
      baseline_mae_min: 20.32,
      integrated_mae_min: 14.27,
      mae_improvement_pct: 29.77,
      baseline_rmse_min: 23.41,
      integrated_rmse_min: 17.15,
      rmse_improvement_pct: 26.74,
      accuracy_within_10min_baseline_pct: 44.0,
      accuracy_within_10min_integrated_pct: 72.0,
      accuracy_within_15min_baseline_pct: 66.0,
      accuracy_within_15min_integrated_pct: 88.0,
    },
    fleet_performance: {
      baseline_workload_balance: 0.6044,
      integrated_workload_balance: 0.8875,
      workload_balance_improvement_pct: 46.84,
      safe_assignment_rate_pct: 100.0,
      unsafe_assignments_prevented: 0,
      emergency_fulfillment_rate_baseline_pct: 0.0,
      emergency_fulfillment_rate_integrated_pct: 100.0,
    },
    system_latency: {
      average_integrated_decision_ms: 124.5,
      average_baseline_decision_ms: 0.02,
    },
    scenario_summaries: {
      NORMAL_OPERATION: {
        runs_count: 5,
        baseline_mean_eta_min: 44.88,
        integrated_mean_eta_min: 44.88,
        baseline_mean_dist_km: 18.7,
        integrated_mean_dist_km: 18.7,
        baseline_workload_balance: 0.6736,
        integrated_workload_balance: 0.8875,
        baseline_eta_mae_min: 13.56,
        integrated_eta_mae_min: 13.56,
        emergency_fulfillment_rate_pct: 100.0,
        safe_assignment_rate_pct: 100.0,
      },
    },
  };

  const mockFleetState = {
    timestamp: '2026-09-06T12:00:00Z',
    vehicles: [
      {
        vehicle_id: 'V-01',
        vehicle_code: 'V-01',
        status: 'ASSIGNED',
        latitude: 40.7128,
        longitude: -74.006,
        speed_kmh: 35.0,
        heading: 90.0,
        current_payload_kg: 2500.0,
        capacity_kg: 12000.0,
        utilization_pct: 20.8,
        current_task_id: 'TSK-01',
        current_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_A'],
        route_status: 'ON_TRACK',
        deviation_distance_m: 0.0,
        estimated_eta_min: 24.5,
        telemetry_health: 'TELEMETRY_HEALTHY',
        last_telemetry_timestamp: '2026-09-06T12:00:00Z',
        depot_id: 'DEPOT_CENTRAL',
        safety_status: 'SAFE',
      },
    ],
    bins: [
      {
        bin_id: 'BIN-01',
        fill_level_percent: 65.0,
        battery_level_percent: 94.0,
        latitude: 40.7128,
        longitude: -74.006,
        last_reading_time: '2026-09-06T12:00:00Z',
        fill_classification: 'NORMAL',
        tilt_degrees: 1.2,
        sensor_health: 'HEALTHY',
        zone: 'ZONE_A',
      },
    ],
    critical_bins_count: 0,
    active_alerts: [],
    traffic_condition: 'NORMAL',
    weather_condition: 'CLEAR',
    fleet_workload_balance: 0.8875,
    average_eta_minutes: 24.5,
    disclaimer: 'Simulated',
  };

  return {
    api: {
      getExtendedHealth: vi.fn().mockResolvedValue(mockHealth),
      getDemoState: vi.fn().mockResolvedValue(mockDemoState),
      getFinalBenchmarks: vi.fn().mockResolvedValue(mockBenchmarks),
      getFusedFleetState: vi.fn().mockResolvedValue(mockFleetState),
      runFullSystemDemo: vi.fn().mockResolvedValue(mockDemoState),
    },
  };
});

describe('Phase 10 CommandCenter Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders command center banner, status indicators, and KPI hero cards', async () => {
    render(
      <MemoryRouter>
        <CommandCenter />
      </MemoryRouter>
    );

    // Title banner
    expect(screen.getByText('Integrated Municipal Command Center')).toBeInTheDocument();
    expect(screen.getByText('Municipal Control Room')).toBeInTheDocument();
    expect(screen.getByText('System Integration Verified')).toBeInTheDocument();

    // KPI Cards
    await waitFor(() => {
      expect(screen.getAllByText('Fleet Coordination').length).toBeGreaterThan(0);
      expect(screen.getAllByText('IoT Telemetry & Bins').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Hybrid ETA Accuracy').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Safety Guardrails').length).toBeGreaterThan(0);
    });
  });

  it('renders the 21-step simulation timeline and step log inspection', async () => {
    render(
      <MemoryRouter>
        <CommandCenter />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Deterministic 21-Step End-to-End Simulation Timeline (Seed 42)')).toBeInTheDocument();
      expect(screen.getAllByText('INITIALIZE_SIMULATION_ENVIRONMENT').length).toBeGreaterThan(0);
      expect(screen.getAllByText('FINAL_SYSTEM_STATUS_ASSESSMENT').length).toBeGreaterThan(0);
    });
  });

  it('renders benchmark comparison metrics and scenario table', async () => {
    render(
      <MemoryRouter>
        <CommandCenter />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Municipal Operations Performance Evaluation')).toBeInTheDocument();
      expect(screen.getByText('50 Controlled Trials Complete')).toBeInTheDocument();
      expect(screen.getByText('NORMAL OPERATION')).toBeInTheDocument();
      expect(screen.getByText('20.32 min')).toBeInTheDocument();
      expect(screen.getByText('14.27 min')).toBeInTheDocument();
    });
  });

  it('triggers run full system demo on button click', async () => {
    render(
      <MemoryRouter>
        <CommandCenter />
      </MemoryRouter>
    );

    const runBtn = screen.getByRole('button', { name: /Run Full System Demo/i });
    expect(runBtn).toBeInTheDocument();

    fireEvent.click(runBtn);
    await waitFor(() => {
      expect(screen.getAllByText('INITIALIZE_SIMULATION_ENVIRONMENT').length).toBeGreaterThan(0);
    });
  });
});
