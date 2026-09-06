"""Telemetry and IoT ingestion and benchmark API routes."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from app.schemas.telemetry import (
    VehicleGPSTelemetry,
    BinSensorTelemetry,
    TelemetryHealthSummary,
    TelemetryAlert,
    Phase9BenchmarkSummary,
    ScalabilityBenchmarkResult,
    RealtimeOperationalState,
    AuthUser,
)
from app.telemetry.service import telemetry_service
from app.telemetry.phase9_experiments import Phase9ExperimentRunner
from app.telemetry.auth import get_current_user, require_role

router = APIRouter(prefix="/telemetry", tags=["Real-Time Telemetry & IoT"])

# Cached experiment runners
_runner = Phase9ExperimentRunner()
_last_benchmark_cache: Optional[Phase9BenchmarkSummary] = None
_last_scalability_cache: Optional[ScalabilityBenchmarkResult] = None


@router.get("/vehicles", response_model=List[VehicleGPSTelemetry])
def get_vehicle_telemetry():
    """Return latest real-time GPS telemetry for all fleet vehicles."""
    return telemetry_service.ingestion.get_all_latest_vehicles()


@router.post("/vehicle", response_model=Dict[str, Any])
def ingest_vehicle_telemetry(telemetry: Dict[str, Any]):
    """Ingest a single simulated vehicle GPS telemetry message."""
    accepted, health, validated = telemetry_service.ingestion.ingest_vehicle_gps(telemetry)
    if not accepted:
        raise HTTPException(status_code=400, detail="Invalid GPS telemetry rejected.")
    return {
        "status": "ACCEPTED",
        "health": health,
        "data": validated.model_dump() if validated else None,
    }


@router.get("/bins", response_model=List[BinSensorTelemetry])
def get_bin_telemetry():
    """Return latest sensor telemetry and fill levels for all smart waste bins."""
    return telemetry_service.ingestion.get_all_latest_bins()


@router.post("/bin", response_model=Dict[str, Any])
def ingest_bin_telemetry(telemetry: Dict[str, Any]):
    """Ingest a single smart waste bin sensor telemetry message."""
    accepted, health, validated = telemetry_service.ingestion.ingest_bin_sensor(telemetry)
    if not accepted:
        raise HTTPException(status_code=400, detail="Invalid bin sensor telemetry rejected.")
    return {
        "status": "ACCEPTED",
        "health": health,
        "data": validated.model_dump() if validated else None,
    }


@router.get("/health", response_model=TelemetryHealthSummary)
def get_telemetry_health():
    """Return aggregated telemetry quality, staleness, and message throughput metrics."""
    return telemetry_service.get_health_summary()


@router.get("/alerts", response_model=List[TelemetryAlert])
def get_telemetry_alerts(limit: int = Query(50, ge=1, le=100)):
    """Return active and recent operational alerts (critical bins, route deviations, stale units)."""
    return telemetry_service.get_alerts(limit=limit)


@router.post("/simulate/step", response_model=RealtimeOperationalState)
def step_telemetry_simulation(elapsed_seconds: float = Query(5.0, ge=1.0, le=60.0)):
    """Advance the simulated IoT clock: progress vehicles along routes and advance bin fill levels."""
    return telemetry_service.step_simulation(elapsed_seconds=elapsed_seconds)


@router.post("/experiments/run", response_model=Phase9BenchmarkSummary)
def run_phase9_benchmarks(user: AuthUser = Depends(require_role(["DISPATCHER", "MUNICIPAL_SUPERVISOR"]))):
    """Execute the full 40-run controlled Phase 9 benchmark suite (8 scenarios x 5 seeds)."""
    global _last_benchmark_cache
    summary = _runner.run_benchmark_suite()
    _last_benchmark_cache = summary
    return summary


@router.get("/experiments", response_model=Phase9BenchmarkSummary)
def get_phase9_experiments():
    """Fetch the latest Phase 9 benchmark results (or auto-executes if not yet run)."""
    global _last_benchmark_cache
    if not _last_benchmark_cache:
        _last_benchmark_cache = _runner.run_benchmark_suite()
    return _last_benchmark_cache


@router.post("/scalability/run", response_model=ScalabilityBenchmarkResult)
def run_scalability_benchmark(user: AuthUser = Depends(require_role(["DISPATCHER", "MUNICIPAL_SUPERVISOR"]))):
    """Execute empirical multi-vehicle scalability benchmark (6, 20, 50 vehicles)."""
    global _last_scalability_cache
    result = _runner.run_scalability_benchmark()
    _last_scalability_cache = result
    return result


@router.get("/scalability", response_model=ScalabilityBenchmarkResult)
def get_scalability_benchmark():
    """Fetch latest multi-vehicle scalability benchmark results."""
    global _last_scalability_cache
    if not _last_scalability_cache:
        _last_scalability_cache = _runner.run_scalability_benchmark()
    return _last_scalability_cache
