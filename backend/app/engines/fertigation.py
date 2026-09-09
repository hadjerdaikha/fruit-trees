"""
Fertigation planning & nutrient budget engine.

Inputs: crop, variety, age, density, yield, stage, soil test, leaf analysis,
water quality, irrigation system, history, symptoms.

Outputs: nutrient requirements, products, timing, splits, quantities
(per tree / ha / zone), safety warnings, nutrient budget.

Safety: never recommend fertilizer from image alone if salinity/disease/root/
water stress could explain symptoms.
"""

from dataclasses import dataclass, field
from typing import Optional

# Typical nutrient uptake ranges for desert fruit trees (kg nutrient / tonne yield)
# These are agronomic estimates (clearly labeled).
UPTAKE = {
    "date": {"n": 1.0, "p": 0.2, "k": 1.6},
    "olive": {"n": 1.2, "p": 0.25, "k": 1.8},
    "pomegranate": {"n": 1.5, "p": 0.3, "k": 2.2},
    "citrus": {"n": 2.8, "p": 0.4, "k": 3.2},
    "grape": {"n": 1.8, "p": 0.3, "k": 2.4},
    "fig": {"n": 1.3, "p": 0.25, "k": 1.7},
}

# Suggested per-tree annual maintenance rates for mature trees (grams/tree)
MAINTENANCE = {
    "date": {"n": 250, "p": 50, "k": 300},
    "olive": {"n": 400, "p": 90, "k": 350},
    "pomegranate": {"n": 300, "p": 60, "k": 400},
    "citrus": {"n": 500, "p": 100, "k": 450},
    "grape": {"n": 150, "p": 40, "k": 200},
    "fig": {"n": 300, "p": 70, "k": 350},
}


@dataclass
class FertigationInput:
    species_code: str
    tree_age_years: Optional[float]
    tree_count: int
    tree_spacing_m: Optional[float]
    area_m2: Optional[float]
    expected_yield_kg: Optional[float]
    growth_stage: Optional[str]
    soil_test: Optional[dict] = None
    leaf_analysis: Optional[dict] = None
    water_ec_ds_m: Optional[float] = None
    soil_ec_ds_m: Optional[float] = None
    symptoms: Optional[str] = None
    salinity_likely: bool = False
    water_stress_likely: bool = False
    disease_likely: bool = False
    confirmed_deficiency: Optional[str] = None  # only from lab analysis


@dataclass
class FertigationResult:
    nutrient_requirements: dict
    product_recommendations: list[str] = field(default_factory=list)
    application_timing: str = ""
    split_applications: str = ""
    quantity_per_tree: dict = field(default_factory=dict)
    quantity_per_ha: dict = field(default_factory=dict)
    safety_warnings: list[str] = field(default_factory=list)
    nutrient_budget: dict = field(default_factory=dict)
    confidence: str = "medium"
    blocked: bool = False
    block_reason: str = ""


class FertigationEngine:
    def plan(self, inp: FertigationInput) -> FertigationResult:
        warnings: list[str] = []
        blocked = False
        block_reason = ""

        # SAFETY: cannot recommend fertilizer from image alone if other causes possible
        if inp.symptoms and not inp.confirmed_deficiency:
            alt = []
            if inp.soil_ec_ds_m is not None and inp.soil_ec_ds_m > 2.5:
                alt.append("salinity")
            if inp.water_stress_likely:
                alt.append("water stress")
            if inp.disease_likely:
                alt.append("disease")
            if inp.salinity_likely:
                alt.append("salinity & root damage")
            if alt:
                blocked = True
                block_reason = (
                    "Symptoms alone cannot justify fertilizer application. Potential alternative causes "
                    "detected: " + ", ".join(alt) + ". Verify soil, leaf, moisture, and EC before fertilizing."
                )
                return FertigationResult(
                    nutrient_requirements={},
                    safety_warnings=[block_reason],
                    blocked=True,
                    block_reason=block_reason,
                    confidence="low",
                )
            warnings.append(
                "Symptom-based fertilizer guidance is only 'possible'; confirm via soil/leaf analysis."
            )

        up = UPTAKE.get(inp.species_code, UPTAKE["olive"])
        maint = MAINTENANCE.get(inp.species_code, MAINTENANCE["olive"])

        # nutrient requirement: max(maintenance, uptake-based) adjusted
        req = {}
        for nut in ("n", "p", "k"):
            maintenance_g = maint[nut] * inp.tree_count
            if inp.expected_yield_kg and up.get(nut):
                uptake_g = up[nut] * (inp.expected_yield_kg / 1000.0) * 1000.0
                # uptake kg nutrient / tonne, yield in kg -> nutrient kg -> g
                uptake_g = up[nut] * (inp.expected_yield_kg)  # g (kg/t * kg / 1000 *1000)
            else:
                uptake_g = 0
            req[nut] = round(max(maintenance_g, uptake_g), 1)

        # soil test adjustment: reduce P/K if soil levels adequate
        if inp.soil_test:
            if inp.soil_test.get("p_ppm") is not None and inp.soil_test["p_ppm"] > 15:
                req["p"] = round(req["p"] * 0.6, 1)
            if inp.soil_test.get("k_ppm") is not None and inp.soil_test["k_ppm"] > 150:
                req["k"] = round(req["k"] * 0.7, 1)

        # growth-stage timing
        timing = "Apply in split applications across the growing season (fertigation)."
        if inp.growth_stage:
            timing = f"Programmed for {inp.growth_stage} stage; adjust N:P:K ratio accordingly."

        tree_count = inp.tree_count or 1
        per_tree = {
            "n": round(req["n"] / tree_count, 1),
            "p": round(req["p"] / tree_count, 1),
            "k": round(req["k"] / tree_count, 1),
        }
        area_ha = (inp.area_m2 or (tree_count * (inp.tree_spacing_m or 4.0) ** 2)) / 10000.0
        per_ha = {k: round(req[k] / area_ha, 1) for k in ("n", "p", "k")} if area_ha else {}

        products = [
            "Prefer split fertigation with water-soluble fertilizers (e.g., NPK 20-20-20 or tailored 12-5-40 for fruit).",
            f"Approx. elemental need: N {req['n']:.0f} g, P {req['p']:.0f} g, K {req['k']:.0f} g for the zone.",
        ]

        # salinity warning
        if inp.soil_ec_ds_m is not None and inp.soil_ec_ds_m > 2.5:
            warnings.append(
                "Soil salinity is elevated: avoid ammonium-based fertilizers that raise EC; prioritize water quality and leaching before high-rate fertigation."
            )
        if inp.water_ec_ds_m is not None and inp.water_ec_ds_m > 1.5:
            warnings.append("Irrigation water is saline; this constrains fertigation rates and may require treatment.")

        budget = {
            "added_estimate": req,
            "requirement_estimate": req,
            "removed_by_harvest_kg": (up[nut] * (inp.expected_yield_kg or 0) / 1000.0 for nut in ("n", "p", "k")),
            "note": "Nutrient budget is an estimate; confirm with soil and leaf analysis.",
        }

        confidence = "high" if inp.soil_test and (inp.expected_yield_kg or inp.leaf_analysis) else "medium"
        if not inp.soil_test:
            confidence = "medium"

        return FertigationResult(
            nutrient_requirements=req,
            product_recommendations=products,
            application_timing=timing,
            split_applications="Split into 3-5 fertigation events matching irrigation frequency, especially in sandy soil to reduce leaching.",
            quantity_per_tree=per_tree,
            quantity_per_ha=per_ha,
            safety_warnings=warnings,
            nutrient_budget={"added": req},
            confidence=confidence,
            blocked=False,
        )
