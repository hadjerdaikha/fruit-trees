"""
Salinity monitoring & early-warning engine.

- Detects gradual EC increase, sudden increase, high-risk zones, salt accumulation.
- Configurable per-crop/variety tolerances (never a universal threshold).
- Distinguishes salinity vs water stress vs nutrient deficiency vs disease where possible.
- Leaching recommendation only when sufficient data exists.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SalinityData:
    zone_name: str
    soil_ec_now: Optional[float]
    soil_ec_previous: Optional[float]  # previous monitoring period
    soil_ec_series: list[float] = field(default_factory=list)
    water_ec: Optional[float] = None
    crop_threshold_ds_m: Optional[float] = None
    crop_critical_ds_m: Optional[float] = None
    soil_texture: Optional[str] = None
    symptoms_detected: bool = False
    has_drainage: Optional[bool] = None
    water_scarcity: bool = False


@dataclass
class SalinityAssessment:
    level: str  # normal | warning | high_risk | critical
    message: str
    rationale: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: str = "medium"
    leaching_advisable: bool = False


class SalinityEngine:
    """Assesses salinity status and risk."""

    def assess(self, data: SalinityData) -> SalinityAssessment:
        rationale: list[str] = []
        recommendations: list[str] = []
        ec_now = data.soil_ec_now
        ec_prev = data.soil_ec_previous

        if ec_now is None:
            return SalinityAssessment(
                level="insufficient_data",
                message="No recent soil EC measurement available for this zone.",
                rationale=["Soil EC not measured."],
                recommendations=["Enter a manual soil test or connect an EC sensor."],
                confidence="low",
            )

        threshold = data.crop_threshold_ds_m
        critical = data.crop_critical_ds_m

        if threshold is None or critical is None:
            rationale.append("No crop/variety-specific salinity thresholds configured; using generic guidance (assumption).")
            threshold = 4.0 if data.soil_texture != "sandy" else 3.0
            critical = threshold * 1.5

        # trend detection
        change_pct = None
        if ec_prev and ec_prev > 0:
            change_pct = (ec_now - ec_prev) / ec_prev * 100.0
            if change_pct > 15:
                rationale.append(
                    f"Soil EC increased by {change_pct:.0f}% from {ec_prev:.2f} to {ec_now:.2f} dS/m over the last monitoring period."
                )
            else:
                rationale.append(f"Soil EC {ec_now:.2f} dS/m, change {change_pct:+.0f}% vs previous ({ec_prev:.2f} dS/m).")

        level = "normal"
        message = "Salinity within normal range."
        if ec_now >= critical:
            level = "critical"
            message = f"Critical salinity: soil EC {ec_now:.2f} dS/m exceeds critical threshold {critical:.2f} dS/m."
            rationale.append(f"EC {ec_now:.2f} exceeds critical {critical:.2f} dS/m.")
        elif ec_now >= threshold:
            level = "high_risk"
            message = f"High salinity risk: soil EC {ec_now:.2f} dS/m exceeds crop threshold {threshold:.2f} dS/m."
            rationale.append(f"EC {ec_now:.2f} exceeds crop threshold {threshold:.2f} dS/m.")
        elif change_pct and change_pct > 15:
            level = "warning"
            message = f"Salinity warning: EC increasing ({change_pct:+.0f}%)."
        else:
            rationale.append(f"Soil EC {ec_now:.2f} dS/m within crop threshold {threshold:.2f} dS/m.")

        # water EC contribution
        if data.water_ec is not None and data.water_ec > 1.0 and ec_now and ec_now >= threshold:
            rationale.append(
                f"Irrigation water EC {data.water_ec:.2f} dS/m is elevated and may contribute to salt accumulation."
            )
            recommendations.append("Analyze irrigation water quality; review the source and treatment of irrigation water.")

        # recommendations by level
        if level == "normal":
            recommendations.append("Continue routine salinity monitoring per schedule.")
        elif level == "warning":
            recommendations.append("Increase salinity monitoring frequency.")
            recommendations.append("Verify sensor accuracy; take a manual soil sample to cross-check.")
        elif level == "high_risk":
            recommendations.append("Test soil at multiple depths to locate salt accumulation.")
            recommendations.append("Review irrigation scheduling and adequacy of leaching (if drainage allows).")
            recommendations.append("Consult an agronomist before major interventions.")
        elif level == "critical":
            recommendations.append("Immediate review required.")
            recommendations.append("Test soil at multiple depths and analyze irrigation water.")
            recommendations.append("Evaluate drainage conditions.")
            recommendations.append("Consult an agronomist for severe salinity management.")

        # symptoms -> possible salt stress vs other causes (differential note)
        if data.symptoms_detected and level in ("high_risk", "critical"):
            message += " Visual symptoms consistent with salt stress are noted."
            rationale.append(
                "Combined elevated EC with visual symptoms increases the likelihood of salt stress. "
                "Note: nutrient deficiency, water stress, and disease can produce similar symptoms; differential verification recommended."
            )
            recommendations.append(
                "Before applying amendments, differentiate salt stress from nutrient deficiency/water stress/disease via soil, leaf, and moisture data."
            )

        # leaching validation
        leaching_advisable = False
        if level in ("high_risk", "critical"):
            if data.has_drainage is False:
                recommendations.append("Poor drainage detected: do NOT leach without improving drainage first.")
            elif data.has_drainage is True:
                if data.water_scarcity:
                    recommendations.append(
                        "Water is scarce: minimize leaching volume and only leach the required amount, accounting for drainage and water availability."
                    )
                elif data.water_ec and data.water_ec > 1.5:
                    recommendations.append(
                        "Irrigation water itself is saline; leaching with this water may worsen the problem. Evaluate water quality first."
                    )
                else:
                    leaching_advisable = True
                    recommendations.append(
                        "A modest, calculated leaching fraction may be considered. Confirm soil texture and drainage, then check with an agronomist."
                    )
            else:
                recommendations.append(
                    "Drainage status unknown: verify drainage before considering any leaching."
                )

        # confidence
        missing = 0
        if ec_prev is None and not data.soil_ec_series:
            missing += 1
        if data.water_ec is None:
            missing += 1
        if threshold is None:
            missing += 1
        confidence = "high" if missing == 0 else ("medium" if missing == 1 else "low")

        return SalinityAssessment(
            level=level,
            message=message,
            rationale=rationale,
            recommendations=recommendations,
            confidence=confidence,
            leaching_advisable=leaching_advisable,
        )
