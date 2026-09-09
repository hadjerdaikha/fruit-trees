"""
Variety suitability engine for desert conditions.

Ranks varieties by aggregate suitability score from crop beak tolerances and
user-provided conditions. Never claims a variety is "best"; uses "more suitable
under the selected conditions".
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Conditions:
    max_summer_temp_c: float
    min_winter_temp_c: float
    frost_risk: float = 0.5
    water_availability: float = 0.5  # 0=poor,1=good
    water_ec_ds_m: Optional[float] = None
    soil_ec_ds_m: Optional[float] = None
    soil_type: str = "sandy"
    market_objective: Optional[str] = None


@dataclass
class VarietyRating:
    variety_id: int
    variety_name: str
    species: str
    suitability_score: float
    strengths: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    main_risks: list[str] = field(default_factory=list)
    management_intensity: float = 0.5


class VarietyEngine:
    """Computes a suitability score per variety."""

    def evaluate(self, variety: dict, conditions: Conditions) -> VarietyRating:
        score = 0.0
        strengths: list[str] = []
        limitations: list[str] = []
        risks: list[str] = []

        heat = variety.get("heat_tolerance", 0.5)
        drought = variety.get("drought_tolerance", 0.5)
        salinity = variety.get("salinity_tolerance", 0.5)
        frost = variety.get("frost_tolerance", 0.5)
        soil = variety.get("soil_compatibility", 0.5)
        water_req = variety.get("water_requirement")  # higher = more water
        disease = variety.get("disease_susceptibility", 0.5)
        market = variety.get("market_suitability", 0.5)

        score += heat * 20  # up to 20
        score += drought * 15  # 15
        score += salinity * 20  # 20
        score += frost * 10  # 10
        score += soil * 5  # 5

        # water availability
        if conditions.water_availability < 0.4:
            score += (1 - drought) * 5  # drought tolerant better when water scarce
            strengths.append("Tolerant of limited water" if drought > 0.6 else "Moderate water needs")
        else:
            score += 3
        # but if variety needs lots of water and water scarce -> penalize
        if water_req and water_req > 800 and conditions.water_availability < 0.4:
            score -= 10
            risks.append("High water demand conflicts with scarce water availability")

        if conditions.water_ec_ds_m and conditions.water_ec_ds_m > 2.5:
            score += salinity * 8 if salinity > 0.6 else 0
            if salinity < 0.4:
                risks.append("Sensitive to saline irrigation water")
        if conditions.soil_ec_ds_m and conditions.soil_ec_ds_m > 3.0:
            score += salinity * 8 if salinity > 0.6 else -8

        if conditions.min_winter_temp_c < 0 and frost < 0.5:
            score -= 10
            risks.append("Frost-sensitive")
        elif conditions.frost_risk > 0.6 and frost < 0.5:
            score -= 8
            limitations.append("Higher frost risk")

        if conditions.max_summer_temp_c > 43 and heat < 0.6:
            score -= 8
            risks.append("May suffer heat stress in extreme summer heat")

        if conditions.soil_type == "sandy" and soil < 0.5:
            score -= 5
            limitations.append("Less suited to sandy soils (higher management needed)")

        # disease susceptibility (lower is better)
        score -= disease * 5

        if conditions.market_objective:
            score += market * 5

        management = (0.0 if heat >= 0.8 else 0.1) + (0.0 if drought >= 0.7 else 0.1) + (0.0 if salinity >= 0.6 else 0.15) + (0.0 if frost >= 0.6 else 0.1) + (0.1 if conditions.water_availability < 0.4 and (not drought or drought < 0.5) else 0)

        score = max(0.0, min(100.0, score))

        return VarietyRating(
            variety_id=variety["id"],
            variety_name=variety["name"],
            species=variety.get("species_name", ""),
            suitability_score=round(score, 1),
            strengths=strengths,
            limitations=limitations,
            main_risks=risks,
            management_intensity=round(min(1.0, management), 2),
        )
