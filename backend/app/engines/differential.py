"""
Differential diagnosis engine.

Ranks possible causes for observed symptoms using image + context data
(soil moisture, EC, water EC, temperature, fertilizer/irrigation history,
crop species, growth stage, disease/pest history).

Never assumes a single cause; always ranks possibilities and recommends
verification before major action (fertilizer/pesticide).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SymptomEvidence:
    symptom: str  # e.g. "yellow leaf margins", "interveinal chlorosis young leaves"
    affected_part: str = "leaf"  # leaf | fruit | trunk | whole
    location_old_leaves: Optional[bool] = None
    location_young_leaves: Optional[bool] = None
    interveinal: Optional[bool] = None
    marginal_burn: Optional[bool] = None
    chlorosis: Optional[bool] = None
    necrosis: Optional[bool] = None
    wilting: Optional[bool] = None
    deformation: Optional[bool] = None
    spots: Optional[bool] = None
    lesion: Optional[bool] = None
    sticky: Optional[bool] = None
    powdery: Optional[bool] = None


@dataclass
class ContextData:
    soil_moisture_status: Optional[str] = None  # low | adequate | high
    soil_ec_ds_m: Optional[float] = None
    water_ec_ds_m: Optional[float] = None
    soil_ph: Optional[float] = None
    air_temp_c: Optional[float] = None
    species: Optional[str] = None
    growth_stage: Optional[str] = None
    recent_irrigation_adequate: Optional[bool] = None
    fertilizer_recent: Optional[bool] = None
    disease_history: Optional[bool] = None
    pest_history: Optional[bool] = None
    deficit_confirmed: Optional[bool] = None  # leaf analysis confirmed


@dataclass
class DiagnosisHypothesis:
    cause: str
    probability: float
    kind: str  # nutrient | salinity | water | disease | pest | heat | sunburn | root | physical
    verification: list[str] = field(default_factory=list)
    action_guidance: str = ""


class DifferentialEngine:
    """Ranks possible causes of observed symptoms."""

    def rank(self, evidence: SymptomEvidence, context: ContextData) -> list[DiagnosisHypothesis]:
        scores: dict[str, dict] = {}
        for h in self._hypotheses(evidence, context):
            scores.setdefault(h.cause, h)

        ranked = sorted(
            self._hypotheses(evidence, context),
            key=lambda h: h.probability,
            reverse=True,
        )
        # normalize probabilities
        total = sum(h.probability for h in ranked) or 1.0
        for h in ranked:
            h.probability = round(h.probability / total * 100.0, 1)
        return ranked

    def _base_hypotheses(self):
        return {
            "nutrient": 0.2,
            "salinity": 0.2,
            "water": 0.15,
            "heat": 0.1,
            "disease": 0.1,
            "pest": 0.1,
            "root": 0.1,
            "sunburn": 0.05,
            "physical": 0.0,
        }

    def _hypotheses(self, ev: SymptomEvidence, ctx: ContextData) -> list[DiagnosisHypothesis]:
        base = self._base_hypotheses()
        p = dict(base)

        # --- Marginal burn / old leaf marginal chlorosis -> K deficiency or salinity ---
        if ev.marginal_burn or (ev.chlorosis and ev.location_old_leaves):
            p["nutrient"] += 0.18
            p["salinity"] += 0.15
            p["water"] += 0.05

        # --- Interveinal chlorosis on young leaves -> Fe/Zn or high pH or root/water ---
        if ev.interveinal and ev.location_young_leaves:
            p["nutrient"] += 0.22
            if ctx.soil_ph is not None and ctx.soil_ph > 7.5:
                p["nutrient"] += 0.1  # Fe unavailability at high pH
            p["root"] += 0.06
            p["water"] += 0.06

        # --- Wilting -> water stress or root or salinity ---
        if ev.wilting:
            p["water"] += 0.2
            p["root"] += 0.1
            p["salinity"] += 0.05

        # --- Lesions/spots/powdery/sticky -> disease or pest ---
        if ev.lesion or ev.spots:
            p["disease"] += 0.18
        if ev.powdery:
            p["disease"] += 0.25
        if ev.sticky:
            p["pest"] += 0.2

        # --- Heat / sunburn ---
        if ctx.air_temp_c is not None and ctx.air_temp_c > 40:
            p["heat"] += 0.12
        if ev.affected_part == "fruit" and (ev.necrosis is not None or ev.lesion):
            p["sunburn"] += 0.12

        # --- Context weighting: salinity ---
        if ctx.soil_ec_ds_m is not None and ctx.soil_ec_ds_m > 4.0:
            p["salinity"] += 0.3
        elif ctx.soil_ec_ds_m is not None and ctx.soil_ec_ds_m > 2.5:
            p["salinity"] += 0.12
        if ctx.water_ec_ds_m is not None and ctx.water_ec_ds_m > 1.5:
            p["salinity"] += 0.1

        # --- moisture ---
        if ctx.soil_moisture_status == "low":
            p["water"] += 0.18
            p["heat"] += 0.05
        elif ctx.soil_moisture_status == "high":
            p["root"] += 0.12
            p["disease"] += 0.08

        # --- fertiliser history suppresses nutrient if recently applied ---
        if ctx.fertilizer_recent:
            p["nutrient"] -= 0.08
            p["salinity"] += 0.05  # over-fertigation can raise salt

        # --- history ---
        if ctx.disease_history:
            p["disease"] += 0.1
        if ctx.pest_history:
            p["pest"] += 0.1

        # build hypotheses with verification
        hs = []

        nutrient_ver = ["Confirm with soil test or leaf analysis before applying fertilizer."]
        if ctx.soil_ph is not None and ctx.soil_ph > 7.5:
            nutrient_ver.append("High soil pH may limit micronutrient availability.")
        salinity_ver = ["Measure soil EC / test irrigation water.", "Differentiate from K deficiency: symptoms overlap."]

        if ev.marginal_burn or (ev.chlorosis and ev.location_old_leaves):
            hs.append(DiagnosisHypothesis(
                cause="Potassium deficiency (possible)",
                probability=p["nutrient"], kind="nutrient",
                verification=[*nutrient_ver,
                              "Verify salinity FIRST: elevated EC + marginal burn suggests salt stress."],
                action_guidance="Before applying potassium, verify soil EC and leaf nutrients because salinity and K deficiency overlap.",
            ))
        elif ev.interveinal and ev.location_young_leaves:
            hs.append(DiagnosisHypothesis(
                cause="Iron deficiency (possible)", probability=p["nutrient"], kind="nutrient",
                verification=[
                    "Check soil pH.",
                    "Review irrigation/moisture conditions (excess moisture can damage roots).",
                    "Leaf analysis if severe or persistent.",
                ],
                action_guidance="Do not apply fertilizer based only on the image; verify soil pH and root/moisture status first.",
            ))
        else:
            hs.append(DiagnosisHypothesis(
                cause="Nutrient deficiency (possible)", probability=p["nutrient"], kind="nutrient",
                verification=nutrient_ver,
                action_guidance="Confirm via soil/leaf analysis before fertilizing.",
            ))

        hs.append(DiagnosisHypothesis(
            cause="Salinity stress", probability=p["salinity"], kind="salinity",
            verification=salinity_ver,
            action_guidance="If soil EC is elevated, treat salinity rather than a nutrient problem.",
        ))
        hs.append(DiagnosisHypothesis(
            cause="Water stress (drought)", probability=p["water"], kind="water",
            verification=["Check soil moisture at multiple depths.", "Check irrigation events & emitter flow."],
        ))
        hs.append(DiagnosisHypothesis(
            cause="Root problem (disease/excess moisture)", probability=p["root"], kind="root",
            verification=["Check soil moisture & drainage.", "Inspect root system if possible."],
        ))
        hs.append(DiagnosisHypothesis(
            cause="Heat stress", probability=p["heat"], kind="heat",
            verification=["Check weather records for heat events."],
        ))
        hs.append(DiagnosisHypothesis(
            cause="Fungal/bacterial disease", probability=p["disease"], kind="disease",
            verification=["Inspect symptom distribution; laboratory/pathology confirmation for severe cases."],
        ))
        hs.append(DiagnosisHypothesis(
            cause="Pest damage", probability=p["pest"], kind="pest",
            verification=["Inspect for pest presence; trap checks."],
        ))
        hs.append(DiagnosisHypothesis(
            cause="Sunburn / physical damage", probability=p["sunburn"], kind="sunburn",
            verification=["Check sun exposure and recent wind/sand events."],
        ))
        return hs
