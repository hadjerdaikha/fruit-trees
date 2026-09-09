"""
Climate risk engine.

Evaluates heat wave, frost, strong wind, sandstorm, and sudden temp drop
risk from weather observations/forecasts and per-crop thresholds.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WeatherSnapshot:
    max_forecast_temp_c: Optional[float]
    min_forecast_temp_c: Optional[float]
    wind_speed_ms: Optional[float]
    heat_wave_risk: Optional[float] = None
    frost_risk: Optional[float] = None
    sandstorm_risk: Optional[float] = None
    forecast_for: Optional[str] = None


@dataclass
class RiskAssessment:
    risks: list[dict] = field(default_factory=list)


class ClimateEngine:
    def evaluate(
        self,
        weather: WeatherSnapshot,
        crop_thresholds: Optional[dict] = None,
        young_trees: bool = False,
    ) -> RiskAssessment:
        risks: list[dict] = []
        thresholds = crop_thresholds or {}

        if weather.max_forecast_temp_c is not None:
            heat_threshold = thresholds.get("heat_threshold_c", 40.0)
            if weather.max_forecast_temp_c > heat_threshold:
                level = "high" if weather.max_forecast_temp_c >= heat_threshold + 4 else "medium"
                risks.append({
                    "type": "heat_wave",
                    "level": level,
                    "timing": weather.forecast_for or "next 48h",
                    "detail": f"Maximum temperature forecast {weather.max_forecast_temp_c:.0f}C exceeds crop heat threshold {heat_threshold:.0f}C.",
                    "why": "Extreme heat raises evaporative demand and can cause heat stress, sunburn, leaf scorch, especially in young trees.",
                    "actions": [
                        "Irrigate in cooler morning window; ensure soil moisture is adequate before/during heat.",
                        "Increase soil-moisture monitoring frequency.",
                        "Avoid water stress and unnecessary pruning during heat.",
                        "Flag young trees for priority inspection.",
                        "Check irrigation system performance (clogs reduce effective application).",
                    ],
                    "young_trees_priority": young_trees,
                })

        if weather.min_forecast_temp_c is not None:
            frost_threshold = thresholds.get("frost_threshold_c", 0.0)
            if weather.min_forecast_temp_c < frost_threshold:
                risks.append({
                    "type": "frost",
                    "level": "high" if weather.min_forecast_temp_c < frost_threshold - 2 else "medium",
                    "timing": weather.forecast_for or "next 48h",
                    "detail": f"Minimum temperature forecast {weather.min_forecast_temp_c:.0f}C below frost threshold {frost_threshold:.0f}C.",
                    "why": "Frost can damage sensitive growth stages (buds, flowers, young fruit).",
                    "actions": ["Implement frost protection if crop is at a sensitive stage.", "Monitor overnight temperatures."],
                })

        if weather.wind_speed_ms is not None:
            if weather.wind_speed_ms > 15:
                risks.append({
                    "type": "strong_wind",
                    "level": "high" if weather.wind_speed_ms > 22 else "medium",
                    "timing": weather.forecast_for or "next 48h",
                    "detail": f"Wind speed forecast {weather.wind_speed_ms:.0f} m/s exceeds safe threshold.",
                    "why": "Strong wind can break branches, damage young trees, and cause sand abrasion.",
                    "actions": [
                        "Inspect branches and young trees for damage after event.",
                        "Check drip emitters, filters, and lines for clogging/sand.",
                        "Inspect windbreaks.",
                    ],
                })

        if weather.sandstorm_risk and weather.sandstorm_risk > 0.6:
            risks.append({
                "type": "sandstorm",
                "level": "high" if weather.sandstorm_risk > 0.8 else "medium",
                "timing": weather.forecast_for or "next 48h",
                "detail": f"Sandstorm risk elevated ({weather.sandstorm_risk:.0%}).",
                "why": "Sandstorms cause abrasion, bury young trees, and clog irrigation infrastructure.",
                "actions": ["After storm: auto-generate inspection checklist (branches, fruit, emitters, filters, lines, sand burial, windbreaks)."],
            })

        return RiskAssessment(risks=risks)
