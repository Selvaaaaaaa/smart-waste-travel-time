from fastapi import APIRouter
from app.api.routes import (
    health,
    dashboard,
    routes,
    vehicles,
    drivers,
    weather,
    traffic,
    events,
    road_restrictions,
    scenarios,
    experiments,
    observations,
    safety,
    ml,
    eta,
    routing,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(routes.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
api_router.include_router(weather.router)
api_router.include_router(traffic.router)
api_router.include_router(events.router)
api_router.include_router(road_restrictions.router)
api_router.include_router(scenarios.router)
api_router.include_router(experiments.router)
api_router.include_router(observations.router)
api_router.include_router(safety.router)
api_router.include_router(ml.router)
api_router.include_router(eta.router)
api_router.include_router(routing.router)

