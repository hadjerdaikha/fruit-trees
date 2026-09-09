"""
Irrigation calculation engine.

Model: ETc = ETo x Kc
Water balance: Prev_water + Rain + Irrigation - ETc - Deep_percolation - Runoff

Sandy-soil aware, configurable per crop/variety/age/stage thresholds.
Every result is explainable (data used, assumptions, confidence).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SoilParams:
    texture: Optional[str]
    field_capacity_pct: Optional[float]  # volumetric %
    wilting_point_pct: Optional[float]
    sand_pct: Optional[float]
    clay_pct: Optional[float]
    organic_matter_pct: Optional[float]
    bulk_density: Optional[float]
    root_zone_depth_m: Optional[float]
    measured_moisture_pct: Optional[float]  # current volumetric moisture
    is_assumed: bool = False

    # texture-based default if FC/PWP missing
    def effective_fc(self) -> float:
        if self.field_capacity_pct is not None:
            return self.field_capacity_pct
        if self.texture == "sandy" or (self.sand_pct and self.sand_pct > 70):
            return 16.0
        if self.texture == "loamy":
            return 28.0
        if self.texture == "clay":
            return 40.0
        # sandy loam default (desert default)
        return 20.0

    def effective_wp(self) -> float:
        if self.wilting_point_pct is not None:
            return self.wilting_point_pct
        if self.texture == "sandy" or (self.sand_pct and self.sand_pct > 70):
            return 6.0
        if self.texture == "loamy":
            return 12.0
        if self.texture == "clay":
            return 22.0
        return 8.0

    def mad(self) -> float:
        # management allowed depletion low for sandy soils -> frequent irrigation
        if self.texture == "sandy" or (self.sand_pct and self.sand_pct > 70):
            return 0.30
        if self.texture == "loamy":
            return 0.45
        if self.texture == "clay":
            return 0.50
        return 0.40


@dataclass
class SystemParams:
    emitter_flow_lph: Optional[float]
    emitters_per_tree: Optional[int]
    irrigation_efficiency_pct: float = 85.0
    max_run_time_min: Optional[float] = None
    tree_count: int = 1
    spacing_m: float = 4.0
    row_spacing_m: float = 6.0
    wetted_width_m: Optional[float] = None
    emitter_flow_assumed: bool = False


@dataclass
class CropParams:
    species_id: int
    species_name: str
    kc: float
    root_depth_m: Optional[float]
    tree_age_years: Optional[float]
    heat_threshold_c: Optional[float]
    growth_stage: Optional[str] = None


@dataclass
class ClimateParams:
    eto_mm: float
    max_forecast_temp_c: Optional[float] = None
    rainfall_mm: float = 0.0
    effective_rainfall_mm: float = 0.0
    relative_humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None


@dataclass
class IrrigationResult:
    etc_mm: float
    eto_mm: float
    kc: float
    readily_available_water_mm: float
    available_water_mm: float
    current_moisture_pct: Optional[float]
    deficit_mm: float
    net_irrigation_mm: float
    gross_irrigation_mm: float
    irrigation_volume_m3: Optional[float]
    duration_min: Optional[float]
    frequency_days: Optional[float]
    split_cycles: int
    recommendation_text: str
    rationale: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: str = "medium"
    heat_alert: bool = False
    suggested_start: Optional[str] = None


class IrrigationEngine:
    """Computes irrigation recommendations."""

    def compute(
        self,
        soil: SoilParams,
        system: SystemParams,
        crop: CropParams,
        climate: ClimateParams,
    ) -> IrrigationResult:
        rationale: list[str] = []
        assumptions: list[str] = []

        # ---- ETc = ETo x Kc ----
        etc_mm = round(climate.eto_mm * crop.kc, 2)
        rationale.append(f"Crop evapotranspiration ETc = ETo x Kc = {climate.eto_mm:.1f} x {crop.kc:.2f} = {etc_mm:.2f} mm/day")

        # ---- Available water ----
        fc = soil.effective_fc()
        wp = soil.effective_wp()
        root_depth = crop.root_depth_m or soil.root_zone_depth_m or 1.0
        if crop.root_depth_m is None and soil.root_zone_depth_m is None:
            assumptions.append("Root zone depth not provided; using 1.0 m assumption.")
        effective_fc_flag = soil.field_capacity_pct is None
        effective_wp_flag = soil.wilting_point_pct is None
        if effective_fc_flag or effective_wp_flag:
            assumptions.append(
                "Field capacity / wilting point not measured; using texture-based estimates (assumption)."
            )

        aw_mm = (fc - wp) / 100.0 * root_depth * 1000.0
        mad = soil.mad()
        raw_mm = aw_mm * mad
        rationale.append(
            f"Available water = (FC {fc:.0f}% - PWP {wp:.0f}%) x depth {root_depth:.2f}m = {aw_mm:.0f} mm; "
            f"Readily available = AW x MAD {mad * 100:.0f}% = {raw_mm:.1f} mm (MAD lowered for soil water retention)."
        )
        if soil.texture == "sandy" or (soil.sand_pct and soil.sand_pct > 70):
            rationale.append("Sandy soil: low water-holding capacity -> shorter, more frequent irrigation preferred.")

        # ---- Current deficit ----
        current_moisture_pct = soil.measured_moisture_pct
        net_irrigation_mm: float
        if current_moisture_pct is not None:
            deficit_mm = max(0.0, (fc - current_moisture_pct) / 100.0 * root_depth * 1000.0)
            net_irrigation_mm = deficit_mm
            rationale.append(
                f"Current soil moisture {current_moisture_pct:.1f}% is "
                + ("above" if current_moisture_pct >= fc - (mad * (fc - wp)) else "below")
                + " target; deficit = {:.1f} mm.".format(deficit_mm)
            )
        else:
            # no moisture sensor -> estimate deficit from water balance
            deficit_mm = max(0.0, etc_mm - climate.effective_rainfall_mm)
            net_irrigation_mm = min(raw_mm, deficit_mm) if raw_mm > 0 else deficit_mm
            assumptions.append("No soil moisture measurement; deficit estimated from water balance (assumption).")
            rationale.append(f"No soil moisture sensor data; estimated deficit from water balance (~{deficit_mm:.1f} mm/day).")

        # weather / heat adjustment
        if climate.max_forecast_temp_c is not None and crop.heat_threshold_c is not None:
            if climate.max_forecast_temp_c > crop.heat_threshold_c:
                net_irrigation_mm = net_irrigation_mm * 1.15
                rationale.append(
                    f"Forecast max temp {climate.max_forecast_temp_c:.0f}C exceeds crop heat threshold "
                    f"{crop.heat_threshold_c:.0f}C; irrigation increased ~15% and monitoring advised."
                )
            else:
                rationale.append(
                    f"Forecast max temp {climate.max_forecast_temp_c:.0f}C within crop heat threshold {crop.heat_threshold_c:.0f}C."
                )

        # rainfall consideration
        if climate.effective_rainfall_mm > 0.5:
            net_irrigation_mm = max(0.0, net_irrigation_mm - climate.effective_rainfall_mm)
            rationale.append(f"Effective rainfall {climate.effective_rainfall_mm:.1f} mm subtracted from requirement.")

        gross_mm = net_irrigation_mm / (system.irrigation_efficiency_pct / 100.0)
        rationale.append(f"Gross irrigation = net {net_irrigation_mm:.1f} mm / efficiency {system.irrigation_efficiency_pct:.0f}% = {gross_mm:.1f} mm.")

        irrigation_volume_m3: Optional[float] = None
        duration_min: Optional[float] = None
        split_cycles = 1

        if system.emitter_flow_lph and system.emitters_per_tree:
            # application rate over the effective wetted area per tree
            wetted_width_m = system.wetted_width_m or (system.spacing_m * 0.5)
            wetted_area_m2 = wetted_width_m * system.row_spacing_m
            flow_per_tree_lph = system.emitter_flow_lph * system.emitters_per_tree
            application_rate_mm_h = flow_per_tree_lph / wetted_area_m2
            duration_h = gross_mm / application_rate_mm_h if application_rate_mm_h else 0.0
            duration_min = round(duration_h * 60.0, 1)
            volume_zone_m3 = (gross_mm / 1000.0) * wetted_area_m2 * system.tree_count
            irrigation_volume_m3 = round(volume_zone_m3, 2)
            rationale.append(
                f"Application rate ~{application_rate_mm_h:.1f} mm/h over the wetted area "
                f"({system.emitters_per_tree} emitters x {system.emitter_flow_lph:.1f} L/h per tree); "
                f"duration ~{duration_min:.0f} min; volume ~{irrigation_volume_m3:.1f} m3."
            )
            if system.emitter_flow_assumed:
                assumptions.append("Emitter flow rate not verified recently (assumption).")
        else:
            assumptions.append(
                "Emitter flow / count not provided; duration and volume not computed. Provide drip system parameters."
            )

        # sanitize duration fractions: report minutes but keep hours for rationale
        if duration_min is not None and duration_min > 24 * 60:
            rationale.append(
                f"Requested run of ~{duration_min / 60:.1f} h exceeds practical single-event limits; "
                "the refill should be distributed across multiple 24-48h scheduling windows."
            )

        # split cycles for sandy soil and long runs
        if soil.texture == "sandy" or (soil.sand_pct and soil.sand_pct > 70):
            if duration_min and duration_min > 60:
                max_run = system.max_run_time_min or 45
                natural = max(2, int(duration_min // max_run) + (1 if duration_min % max_run else 0))
                split_cycles = min(natural, 4)  # cap; exceedance spreads over days
                if natural > 4:
                    rationale.append(
                        f"Long refill run split across {split_cycles}+ scheduling windows over the next few days "
                        "to limit deep percolation and nutrient leaching in sandy soil."
                    )
                else:
                    rationale.append(
                        f"Sandy soil: run split into {split_cycles} cycles to limit deep percolation and nutrient leaching."
                    )
            elif duration_min:
                split_cycles = 1

        # frequency
        daily_etc = etc_mm
        frequency_days: Optional[float] = None
        if raw_mm > 0 and etc_mm > 0:
            freq = raw_mm / etc_mm
            if soil.texture == "sandy" or (soil.sand_pct and soil.sand_pct > 70):
                freq = min(freq, 2.0)  # cap for sandy soils -> frequent
            frequency_days = round(freq, 1)
            rationale.append(f"Suggested frequency = readily available water / daily ETc ~ every {frequency_days} days (capped for sandy soil).")

        # confidence
        missing_drivers = 0
        if current_moisture_pct is None:
            missing_drivers += 1
        if system.emitter_flow_assumed or system.emitter_flow_lph is None:
            missing_drivers += 1
        if effective_fc_flag or effective_wp_flag:
            missing_drivers += 1
        if missing_drivers >= 2:
            confidence = "low"
        elif missing_drivers == 1:
            confidence = "medium"
        else:
            confidence = "high"

        heat_alert = (
            climate.max_forecast_temp_c is not None
            and crop.heat_threshold_c is not None
            and climate.max_forecast_temp_c > crop.heat_threshold_c
        )

        suggested_start = None
        if heat_alert:
            suggested_start = "06:00-10:00 (cooler period)"
            rationale.append("Heat event: schedule irrigation in cooler morning window to reduce evaporative losses.")

        # recommendation text
        parts = [f"Apply {gross_mm:.1f} mm"]
        if irrigation_volume_m3 is not None:
            parts.append(f"(~{irrigation_volume_m3} m3{' for the zone' if system.tree_count > 1 else ''})")
        if duration_min is not None:
            if duration_min >= 24 * 60:
                parts.append(f"over ~{duration_min / 60:.0f} h of drip runtime")
            else:
                parts.append(f"over ~{duration_min:.0f} min")
        if split_cycles > 1:
            parts.append(f"split into {split_cycles} cycles")
        if frequency_days is not None:
            parts.append(f"repeat about every {frequency_days} days")
        if suggested_start:
            parts.append(f"timed {suggested_start}")
        recommendation_text = ", ".join(parts) + "."

        return IrrigationResult(
            etc_mm=etc_mm,
            eto_mm=climate.eto_mm,
            kc=crop.kc,
            readily_available_water_mm=round(raw_mm, 1),
            available_water_mm=round(aw_mm, 1),
            current_moisture_pct=current_moisture_pct,
            deficit_mm=round(deficit_mm, 1),
            net_irrigation_mm=round(net_irrigation_mm, 1),
            gross_irrigation_mm=round(gross_mm, 1),
            irrigation_volume_m3=irrigation_volume_m3,
            duration_min=duration_min,
            frequency_days=frequency_days,
            split_cycles=split_cycles,
            recommendation_text=recommendation_text,
            rationale=rationale,
            assumptions=assumptions,
            confidence=confidence,
            heat_alert=heat_alert,
            suggested_start=suggested_start,
        )
