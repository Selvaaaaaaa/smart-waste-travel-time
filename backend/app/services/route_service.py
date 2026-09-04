from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.route import Route
from app.models.route_stop import RouteStop
from app.schemas.routes import RouteItem, RouteListResponse, RouteStop as SchemaRouteStop


class RouteService:
    """Service providing collection route queries from PostgreSQL with synthetic fallback."""

    @staticmethod
    def get_routes(
        db: Optional[Session] = None,
        status: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> RouteListResponse:
        if db is None:
            return RouteService._get_fallback_routes(status, vehicle_id, query)

        try:
            q = db.query(Route)

            if status and status.lower() != "all":
                q = q.filter(Route.status.ilike(f"%{status}%"))

            if vehicle_id and vehicle_id.lower() != "all":
                q = q.join(Route.vehicle).filter(Route.vehicle.has(vehicle_code=vehicle_id))

            routes_db = q.all()

            if not routes_db:
                return RouteService._get_fallback_routes(status, vehicle_id, query)

            items = []
            for r in routes_db:
                # Map vehicle and driver codes
                v_code = r.vehicle.vehicle_code if r.vehicle else "V-01"
                d_name = r.driver.name if r.driver else "Unassigned Driver"

                # If query search string provided
                if query:
                    search_str = query.lower()
                    if (
                        search_str not in r.route_code.lower()
                        and search_str not in d_name.lower()
                        and search_str not in v_code.lower()
                    ):
                        continue

                stops_schema = [
                    SchemaRouteStop(
                        stop_id=f"S-{s.id:02d}",
                        name=f"Collection Point #{s.stop_sequence}",
                        lat=float(s.latitude),
                        lng=float(s.longitude),
                        waste_volume_kg=float(s.waste_tons * 1000.0),
                        sequence=s.stop_sequence,
                    )
                    for s in r.stops
                ]

                # Map to standard interface
                items.append(
                    RouteItem(
                        route_id=r.route_code,
                        vehicle_id=v_code,
                        driver_name=d_name,
                        waste_volume_tons=float(r.total_waste_tons),
                        distance_km=float(r.total_distance_km),
                        baseline_eta_min=float(r.baseline_eta_minutes),
                        context_eta_min=round(float(r.baseline_eta_minutes * 1.15), 1),
                        status=r.status,
                        collection_stops_count=len(r.stops) or 6,
                        stops=stops_schema,
                    )
                )

            return RouteListResponse(routes=items, total=len(items), is_demo=True)
        except Exception:
            return RouteService._get_fallback_routes(status, vehicle_id, query)

    @staticmethod
    def _get_fallback_routes(
        status: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> RouteListResponse:
        demo_routes = [
            RouteItem(
                route_id="R-101",
                vehicle_id="V-01",
                driver_name="Alex Mercer",
                waste_volume_tons=4.2,
                distance_km=18.5,
                baseline_eta_min=42.0,
                context_eta_min=49.0,
                status="On Schedule",
                collection_stops_count=8,
                stops=[
                    SchemaRouteStop(stop_id="S-01", name="Depot / Central Yard", lat=40.7128, lng=-74.0060, waste_volume_kg=0.0, sequence=1),
                    SchemaRouteStop(stop_id="S-02", name="Sector A - Commercial Point", lat=40.7180, lng=-73.9980, waste_volume_kg=850.0, sequence=2),
                    SchemaRouteStop(stop_id="S-03", name="Sector B - Residential Block 4", lat=40.7250, lng=-73.9920, waste_volume_kg=1200.0, sequence=3),
                    SchemaRouteStop(stop_id="S-04", name="Sector C - Civic Center", lat=40.7310, lng=-73.9850, waste_volume_kg=950.0, sequence=4),
                    SchemaRouteStop(stop_id="S-05", name="Sector D - Market District", lat=40.7380, lng=-73.9800, waste_volume_kg=1200.0, sequence=5),
                    SchemaRouteStop(stop_id="S-06", name="Landfill / Transfer Hub", lat=40.7450, lng=-73.9720, waste_volume_kg=0.0, sequence=6),
                ],
            ),
            RouteItem(
                route_id="R-102",
                vehicle_id="V-02",
                driver_name="Elena Vance",
                waste_volume_tons=3.8,
                distance_km=14.2,
                baseline_eta_min=35.0,
                context_eta_min=39.0,
                status="On Schedule",
                collection_stops_count=6,
            ),
            RouteItem(
                route_id="R-103",
                vehicle_id="V-03",
                driver_name="Marcus Reed",
                waste_volume_tons=5.9,
                distance_km=22.8,
                baseline_eta_min=52.0,
                context_eta_min=68.0,
                status="Delayed",
                collection_stops_count=11,
            ),
            RouteItem(
                route_id="R-104",
                vehicle_id="V-04",
                driver_name="Sarah Chen",
                waste_volume_tons=2.1,
                distance_km=11.0,
                baseline_eta_min=28.0,
                context_eta_min=30.0,
                status="On Schedule",
                collection_stops_count=5,
            ),
            RouteItem(
                route_id="R-105",
                vehicle_id="V-05",
                driver_name="David Kim",
                waste_volume_tons=5.1,
                distance_km=19.4,
                baseline_eta_min=48.0,
                context_eta_min=59.0,
                status="At Risk",
                collection_stops_count=9,
            ),
            RouteItem(
                route_id="R-106",
                vehicle_id="V-06",
                driver_name="Carlos Gomez",
                waste_volume_tons=4.6,
                distance_km=16.8,
                baseline_eta_min=40.0,
                context_eta_min=44.0,
                status="On Schedule",
                collection_stops_count=7,
            ),
            RouteItem(
                route_id="R-107",
                vehicle_id="V-07",
                driver_name="Priya Patel",
                waste_volume_tons=3.4,
                distance_km=13.5,
                baseline_eta_min=32.0,
                context_eta_min=35.0,
                status="On Schedule",
                collection_stops_count=6,
            ),
            RouteItem(
                route_id="R-108",
                vehicle_id="V-08",
                driver_name="Liam Johnson",
                waste_volume_tons=4.9,
                distance_km=21.0,
                baseline_eta_min=50.0,
                context_eta_min=64.0,
                status="Delayed",
                collection_stops_count=10,
            ),
        ]

        filtered = demo_routes
        if status and status.lower() != "all":
            filtered = [r for r in filtered if r.status.lower() == status.lower()]
        if vehicle_id and vehicle_id.lower() != "all":
            filtered = [r for r in filtered if r.vehicle_id.lower() == vehicle_id.lower()]
        if query:
            q = query.lower()
            filtered = [
                r for r in filtered
                if q in r.route_id.lower() or q in r.driver_name.lower() or q in r.vehicle_id.lower()
            ]

        return RouteListResponse(routes=filtered, total=len(filtered), is_demo=True)
