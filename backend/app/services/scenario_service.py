from app.schemas.scenarios import ScenarioOptionsResponse


class ScenarioService:
    """Service providing simulation options and parameter configurations."""

    @staticmethod
    def get_scenario_options() -> ScenarioOptionsResponse:
        return ScenarioOptionsResponse(
            weather_options=["Clear", "Light Rain", "Heavy Rain"],
            traffic_options=["Low", "Medium", "High"],
            event_options=["None", "Small Event", "Major Event"],
            road_restriction_options=["None", "Partial Closure", "Full Closure"],
            waste_volume_options=["Low", "Normal", "High", "Extreme"],
            time_of_day_options=["Morning", "Afternoon", "Evening", "Night"],
            is_demo=True,
        )
