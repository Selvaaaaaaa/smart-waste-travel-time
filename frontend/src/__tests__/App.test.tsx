import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from '../pages/Dashboard';
import { ScenarioSimulator } from '../pages/ScenarioSimulator';
import { Routes as RoutesPage } from '../pages/Routes';
import { ETAAnalysis } from '../pages/ETAAnalysis';
import { Experiments } from '../pages/Experiments';
import { DynamicRouting } from '../pages/DynamicRouting';
import { SystemInformation } from '../pages/SystemInformation';
import { Sidebar } from '../components/layout/Sidebar';


// Mock API calls to return predictable demo, ML, and experiment values
vi.mock('../services/api', () => {
  const mockDashboard = {
    waste_volume: 8.4,
    waste_volume_unit: 'tons',
    active_routes: 12,
    average_eta_min: 42.0,
    eta_accuracy_pct: 91.0,
    available_vehicles: '8 / 10',
    workload_status: 'Within Limits',
    operating_conditions: {
      weather: 'Clear',
      traffic: 'Moderate',
      event_impact: 'Low',
      road_restrictions: 'None',
      waste_volume: 'Normal',
    },
    waste_volume_trends: [
      { day: 'Mon', volume_tons: 7.8 },
      { day: 'Tue', volume_tons: 8.2 },
    ],
    eta_comparisons: [
      { route_id: 'Route R001', baseline_eta_min: 45, context_eta_min: 52, actual_eta_min: 54 },
    ],
    eta_errors: [
      { route_id: 'R001', baseline_error_min: 9, context_error_min: 2 },
    ],
    vehicle_utilization: [
      { vehicle_id: 'V001', utilization_pct: 82, capacity_tons: 10, current_load_tons: 8.2 },
    ],
    is_demo: true,
    phase: 1,
  };

  const mockRoutes = {
    routes: [
      {
        route_id: 'R-101',
        vehicle_id: 'V-01',
        driver_name: 'Alex Mercer',
        waste_volume_tons: 4.2,
        distance_km: 18.5,
        baseline_eta_min: 42.0,
        context_eta_min: 49.0,
        status: 'On Schedule',
        collection_stops_count: 8,
      },
    ],
    total: 1,
    is_demo: true,
  };

  const mockPresets = [
    {
      key: 'NORMAL',
      name: 'Normal Conditions',
      description: 'Nominal operational environment',
      weather_condition: 'CLEAR',
      rainfall_mm: 0,
      visibility_km: 10,
      traffic_level: 'LOW',
      congestion_index: 15,
      average_speed_kmh: 42,
      event_level: 'NONE',
      event_radius: 0,
      road_restriction_type: 'NONE',
      road_restriction_severity: 'NONE',
      waste_volume_tons: 5.5,
      hour_of_day: 9,
      day_of_week: 1,
    },
  ];

  const mockMLStatus = {
    is_trained: true,
    model_name: 'Context-Aware ETA (Random Forest)',
    model_type: 'random_forest',
    model_version: '1.0.0',
    training_date: '2026-09-04T11:13:19Z',
    training_row_count: 48,
    testing_row_count: 12,
    total_dataset_rows: 60,
    metrics: {
      baseline: {
        mae: 36.76,
        rmse: 43.75,
        mean_error: -36.76,
        median_absolute_error: 29.1,
        within_tolerance_pct: 0.0,
        tolerance_minutes: 10.0,
        sample_count: 12,
      },
      context_aware: {
        mae: 3.75,
        rmse: 4.74,
        mean_error: -1.29,
        median_absolute_error: 3.32,
        within_tolerance_pct: 91.67,
        tolerance_minutes: 10.0,
        sample_count: 12,
      },
      mae_improvement_pct: 89.8,
      rmse_improvement_pct: 89.17,
      is_improved: true,
    },
    feature_importances: [
      { feature: 'rainfall_mm', importance: 0.31 },
      { feature: 'congestion_index', importance: 0.28 },
    ],
    split_method: 'Chronological (80/20)',
    synthetic_disclaimer: 'Synthetic Dataset — Research Prototype',
  };

  const mockScenarioRun = {
    scenario_name: 'Normal Conditions',
    scenario_key: 'NORMAL',
    status: 'COMPLETED',
    is_safe: true,
    parameters: {},
    baseline_eta_minutes: 54.0,
    context_aware_eta_minutes: 72.7,
    simulated_actual_minutes: 36.75,
    baseline_error_minutes: 17.25,
    context_aware_error_minutes: 35.95,
    improvement_pct: -108.41,
    safety_status: 'SAFE',
    safety_message: 'All operational and labor safety constraints satisfied.',
  };

  const mockBenchmark = {
    total_scenarios: 6,
    total_experiment_runs: 30,
    safe_runs_count: 30,
    unsafe_runs_count: 0,
    global_metrics: {
      baseline: { mae: 51.51, rmse: 71.08, within_tolerance_pct: 16.67 },
      context_aware: { mae: 34.85, rmse: 41.69, within_tolerance_pct: 13.33 },
      mae_improvement_pct: 32.34,
      rmse_improvement_pct: 41.35,
    },
    scenario_breakdown: [
      {
        scenario_key: 'NORMAL',
        scenario_name: 'Normal Conditions',
        repetitions: 5,
        total_runs: 5,
        safe_runs: 5,
        unsafe_runs: 0,
        winner: 'BASELINE',
        metrics: {
          baseline: { mae: 14.91, rmse: 15.08 },
          context_aware: { mae: 30.18, rmse: 30.25 },
          mae_improvement_pct: -102.41,
          rmse_improvement_pct: -100.6,
        },
        safety_summary: { total_assignments: 5, safe_assignments: 5, unsafe_assignments: 0 },
      },
    ],
    failure_analysis: {
      total_runs: 30,
      total_failures: 26,
      failure_rate_pct: 86.67,
      category_breakdown: { CONTEXT_MISMATCH: 10, RARE_CONDITION: 5 },
      failure_cases: [
        {
          scenario_key: 'NORMAL',
          scenario_name: 'Normal Conditions',
          route_id: 'R-101',
          seed: 42,
          baseline_eta_minutes: 54.0,
          context_aware_eta_minutes: 72.7,
          actual_travel_minutes: 36.75,
          baseline_error_minutes: 17.25,
          context_aware_error_minutes: 35.95,
          failure_reason: 'CONTEXT_MISMATCH',
          is_safe: true,
        },
      ],
    },
    top_worst_errors: {
      baseline_worst: [],
      context_aware_worst: [],
    },
    synthetic_disclaimer: 'Synthetic Dataset — Research Prototype',
  };

  return {
    api: {
      getHealth: vi.fn().mockResolvedValue({ status: 'ok', service: 'smart-waste-travel-time-api', phase: 1 }),
      getDashboardSummary: vi.fn().mockResolvedValue(mockDashboard),
      getRoutes: vi.fn().mockResolvedValue(mockRoutes),
      getScenarioPresets: vi.fn().mockResolvedValue(mockPresets),
      getMLStatus: vi.fn().mockResolvedValue(mockMLStatus),
      runScenario: vi.fn().mockResolvedValue(mockScenarioRun),
      trainMLModel: vi.fn().mockResolvedValue({ status: 'SUCCESS', metadata: mockMLStatus }),
      getBenchmarkResults: vi.fn().mockResolvedValue(mockBenchmark),
      runExperiment: vi.fn().mockResolvedValue(mockBenchmark),
      getFailureCases: vi.fn().mockResolvedValue(mockBenchmark.failure_analysis),
      getModelComparison: vi.fn().mockResolvedValue({ comparison_table: [] }),
      predictHybridETA: vi.fn().mockResolvedValue({
        selected_model: 'BASELINE',
        predicted_eta_minutes: 42.5,
        selection_reason: 'NOMINAL_ENVIRONMENTAL_CONDITIONS',
        prediction_spread_minutes: null,
        safety_status: 'SAFE',
        is_safe: true,
        policy_version: 'hybrid-v1',
      }),
      getNetworkGraph: vi.fn().mockResolvedValue({
        nodes: [
          { id: 'DEPOT_CENTRAL', name: 'Central Depot', lat: 40.7128, lng: -74.0060, node_type: 'depot' },
          { id: 'LANDFILL_MAIN', name: 'Main Landfill', lat: 40.7900, lng: -73.9400, node_type: 'landfill' },
        ],
        edges: [],
        disclaimer: 'SIMULATION DISCLAIMER',
      }),
      listActiveTrips: vi.fn().mockResolvedValue([
        {
          id: 'TRIP-12345',
          vehicle_id: 'V-01',
          driver_id: 'EMP-001',
          origin_node: 'DEPOT_CENTRAL',
          destination_node: 'LANDFILL_MAIN',
          current_node: 'DEPOT_CENTRAL',
          visited_nodes: ['DEPOT_CENTRAL'],
          remaining_stops: ['COLLECTION_ZONE_A'],
          current_path: ['DEPOT_CENTRAL', 'LANDFILL_MAIN'],
          current_payload_kg: 1000,
          vehicle_capacity_kg: 8000,
          elapsed_time_minutes: 0,
          max_shift_hours: 4.0,
          distance_traveled_km: 0,
          current_eta_minutes: 35.0,
          baseline_eta_minutes: 35.0,
          hybrid_eta_minutes: 35.0,
          eta_uncertainty_minutes: 2.0,
          status: 'IN_PROGRESS',
          active_disruptions: [],
          reroute_count: 0,
          created_at: '2026-09-04T12:00:00Z',
          updated_at: '2026-09-04T12:00:00Z',
        },
      ]),
      getActiveTrip: vi.fn().mockResolvedValue({
        id: 'TRIP-12345',
        vehicle_id: 'V-01',
        driver_id: 'EMP-001',
        origin_node: 'DEPOT_CENTRAL',
        destination_node: 'LANDFILL_MAIN',
        current_node: 'DEPOT_CENTRAL',
        visited_nodes: ['DEPOT_CENTRAL'],
        remaining_stops: ['COLLECTION_ZONE_A'],
        current_path: ['DEPOT_CENTRAL', 'LANDFILL_MAIN'],
        current_payload_kg: 1000,
        vehicle_capacity_kg: 8000,
        elapsed_time_minutes: 0,
        max_shift_hours: 4.0,
        distance_traveled_km: 0,
        current_eta_minutes: 35.0,
        baseline_eta_minutes: 35.0,
        hybrid_eta_minutes: 35.0,
        eta_uncertainty_minutes: 2.0,
        status: 'IN_PROGRESS',
        active_disruptions: [],
        reroute_count: 0,
        created_at: '2026-09-04T12:00:00Z',
        updated_at: '2026-09-04T12:00:00Z',
      }),
      executeReroute: vi.fn().mockResolvedValue({
        trip_id: 'TRIP-12345',
        reroute_executed: true,
        trigger_type: 'MANUAL',
        decision_rationale: 'Rerouted to AVOID_TRAFFIC',
        all_candidates: [],
        trip: {
          id: 'TRIP-12345',
          vehicle_id: 'V-01',
          driver_id: 'EMP-001',
          origin_node: 'DEPOT_CENTRAL',
          destination_node: 'LANDFILL_MAIN',
          current_node: 'DEPOT_CENTRAL',
          visited_nodes: ['DEPOT_CENTRAL'],
          remaining_stops: [],
          current_path: ['DEPOT_CENTRAL', 'LANDFILL_MAIN'],
          current_payload_kg: 1000,
          vehicle_capacity_kg: 8000,
          elapsed_time_minutes: 0,
          max_shift_hours: 4.0,
          distance_traveled_km: 0,
          current_eta_minutes: 32.0,
          baseline_eta_minutes: 35.0,
          hybrid_eta_minutes: 32.0,
          eta_uncertainty_minutes: 1.5,
          status: 'IN_PROGRESS',
          active_disruptions: [],
          reroute_count: 1,
          created_at: '2026-09-04T12:00:00Z',
          updated_at: '2026-09-04T12:00:00Z',
        },
        disclaimer: 'SIMULATION DISCLAIMER',
      }),
      simulateStep: vi.fn().mockResolvedValue({
        step_taken_from: 'DEPOT_CENTRAL',
        step_taken_to: 'COLLECTION_ZONE_A',
        segment_distance_km: 1.8,
        segment_time_minutes: 4.5,
        waste_collected_kg: 1200,
        trip_completed: false,
        reroute_occurred: false,
        trip: {
          id: 'TRIP-12345',
          vehicle_id: 'V-01',
          driver_id: 'EMP-001',
          origin_node: 'DEPOT_CENTRAL',
          destination_node: 'LANDFILL_MAIN',
          current_node: 'COLLECTION_ZONE_A',
          visited_nodes: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_A'],
          remaining_stops: [],
          current_path: ['DEPOT_CENTRAL', 'LANDFILL_MAIN'],
          current_payload_kg: 2200,
          vehicle_capacity_kg: 8000,
          elapsed_time_minutes: 4.5,
          max_shift_hours: 4.0,
          distance_traveled_km: 1.8,
          current_eta_minutes: 30.5,
          baseline_eta_minutes: 35.0,
          hybrid_eta_minutes: 30.5,
          eta_uncertainty_minutes: 1.5,
          status: 'IN_PROGRESS',
          active_disruptions: [],
          reroute_count: 0,
          created_at: '2026-09-04T12:00:00Z',
          updated_at: '2026-09-04T12:00:00Z',
        },
        disclaimer: 'SIMULATION DISCLAIMER',
      }),
      runRoutingBenchmark: vi.fn().mockResolvedValue({
        total_runs: 35,
        scenarios_evaluated: ['NORMAL', 'HEAVY_RAIN'],
        mean_time_saved_min: 5.93,
        mean_pct_time_saved: 10.41,
        overall_safety_rate_static_pct: 71.4,
        overall_safety_rate_dynamic_pct: 85.7,
        disruption_adaptation_effectiveness_pct: 18.11,
        scenario_breakdown: {},
        disclaimer: 'SIMULATION DISCLAIMER',
      }),
    },
  };
});


// Mock leaflet components to prevent canvas/DOM errors in jsdom
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children }: any) => <div data-testid="marker">{children}</div>,
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  Polyline: () => <div data-testid="polyline" />,
}));

describe('Smart Waste Collection Operations Platform (Phase 5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders Dashboard with KPI cards and operating conditions', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Smart Waste Collection Operations/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Today's Waste Volume/i)).toBeInTheDocument();
    expect(screen.getByText(/8.4/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Routes/i)).toBeInTheDocument();
    expect(screen.getByText(/Within Limits/i)).toBeInTheDocument();
    expect(screen.getByText(/Current Operating Conditions/i)).toBeInTheDocument();
  });

  it('2. Renders Sidebar navigation and system status indicator', () => {
    render(
      <MemoryRouter>
        <Sidebar isOpen={true} />
      </MemoryRouter>
    );

    expect(screen.getByText(/SMART WASTE/i)).toBeInTheDocument();
    expect(screen.getByText(/SYSTEM ONLINE/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Scenario Simulator/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Routes/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /ETA Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Experiments/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /System Information/i })).toBeInTheDocument();
  });

  it('3. Renders Scenario Simulator and executes simulation', async () => {
    render(
      <MemoryRouter>
        <ScenarioSimulator />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Operational Scenario Simulator/i)).toBeInTheDocument();
      expect(screen.getByText(/Normal Conditions/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/ROAD RESTRICTION/i)).toBeInTheDocument();

    const form = screen.getByRole('button', { name: /Run Scenario/i }).closest('form')!;
    fireEvent.submit(form);

    await waitFor(
      () => {
        expect(screen.getByText(/Scenario Simulation Completed/i)).toBeInTheDocument();
        expect(screen.getByText(/Model 1: Baseline/i)).toBeInTheDocument();
        expect(screen.getByText(/Model 2: Context-Aware ML/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('4. Renders Routes page and displays active collection route table', async () => {
    render(
      <MemoryRouter>
        <RoutesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Active Collection Routes/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/Alex Mercer/i)).toBeInTheDocument();
      expect(screen.getByText(/R-101/i)).toBeInTheDocument();
    });
  });

  it('5. Renders ETA Analysis and verifies MAE / RMSE cards and adaptive decision card', async () => {
    render(
      <MemoryRouter>
        <ETAAnalysis />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/ETA Model Intelligence & Adaptive Hybrid Analysis/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText(/Baseline MAE/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Context-aware MAE/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Baseline RMSE/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Context-aware RMSE/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Pre-Trip Adaptive Decision Card & Model Uncertainty/i)).toBeInTheDocument();
    expect(screen.getByText(/Model Feature Importance/i)).toBeInTheDocument();
  });

  it('6. Renders Experiments and System Information pages with 3-model benchmark', async () => {
    const { unmount } = render(
      <MemoryRouter>
        <Experiments />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Empirical Experimentation & Adaptive Hybrid Benchmarks/i)).toBeInTheDocument();
      expect(screen.getByText(/Three-Model Experiment Parameters & Execution Control/i)).toBeInTheDocument();
      expect(screen.getByText(/Three-Model Performance, Selection Rates & Scenario Winners/i)).toBeInTheDocument();
    });

    unmount();

    render(
      <MemoryRouter>
        <SystemInformation />
      </MemoryRouter>
    );
    expect(screen.getByText(/PROJECT PROBLEM/i)).toBeInTheDocument();
    expect(screen.getByText(/PROJECT OBJECTIVE/i)).toBeInTheDocument();
    expect(screen.getByText(/SAFETY CONSTRAINTS & OPERATIONAL BOUNDS/i)).toBeInTheDocument();
    expect(screen.getByText(/Complete Technology Stack/i)).toBeInTheDocument();
  });

  it('7. Renders Dynamic Routing (Phase 6) page with live map, controls, and candidate scoring table', async () => {
    render(
      <MemoryRouter>
        <DynamicRouting />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Dynamic Real-Time Route Rerouting & Optimization/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Step Simulation/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Evaluate Candidates & Reroute/i })).toBeInTheDocument();
    expect(screen.getByText(/Candidate Routes Evaluation & Safety Scoring/i)).toBeInTheDocument();
    expect(screen.getByText(/Inject Real-Time Disruption/i)).toBeInTheDocument();
    expect(screen.getByText(/SIMULATION DISCLAIMER/i)).toBeInTheDocument();

  });
});

