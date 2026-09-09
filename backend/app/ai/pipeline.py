"""
AI image analysis pipeline.

Image validation -> preprocessing -> symptom extraction -> probabilistic
differential classification -> confidence -> human review workflow.

MVP uses a deterministic symptom/signal heuristic classifier complemented by
context from the differential engine. The ImageAnalyzer interface is pluggable
so real CV models can be swapped in.
"""

from dataclasses import dataclass, field
from typing import Optional

from PIL import Image, ImageOps

from ..engines.differential import ContextData, DifferentialEngine, SymptomEvidence


@dataclass
class ImageAnalysisResult:
    primary_diagnosis: str
    confidence_pct: float
    alternatives: list[dict]
    severity: str
    affected_part: str
    visible_symptoms: list[str]
    recommended_action: str
    requires_expert: bool
    model_version: str = "heuristic-v1"


class ImageValidationError(Exception):
    pass


def validate_image(pil_image: Image.Image) -> None:
    """Validate image quality / sanity."""
    if pil_image.size[0] < 64 or pil_image.size[1] < 64:
        raise ImageValidationError("Image resolution too low for analysis. Use a sharp, well-lit photo.")
    if pil_image.size[0] > 4096 or pil_image.size[1] > 4096:
        # allowed but downscaled during preprocessing
        pass


def preprocess(pil_image: Image.Image) -> Image.Image:
    """Normalize orientation and resize for analysis."""
    image = ImageOps.exif_transpose(pil_image)
    image = ImageOps.autocontrast(image)
    image.thumbnail((1024, 1024))
    return image


def capture_guidance() -> list[str]:
    return [
        "Use a sharp, well-lit image (not blurry or in direct harsh shadow).",
        "Capture both the affected and healthy tissue when possible.",
        "Take more than one image for difficult cases.",
        "Include full-plant/tree context when useful.",
        "Ensure the affected part (leaf/fruit) fills a good portion of the frame.",
    ]


class ImageAnalyzer:
    """Analyzes image for possible conditions using signal heuristics.

    This is intentionally a soft, uncertain classifier: outputs are 'possible'
    diagnoses with confidence and differentials, never guarantees.
    """

    def analyze(self, pil_image: Image.Image, context: Optional[ContextData] = None) -> ImageAnalysisResult:
        validate_image(pil_image)
        image = preprocess(pil_image)
        stats = _extract_visual_signals(image)

        # Build symptom evidence from extracted signals
        ev = SymptomEvidence(
            symptom=stats["symptom_summary"],
            chlorosis=stats["chlorosis"],
            interveinal=stats["interveinal"],
            marginal_burn=stats["marginal_burn"],
            necrosis=stats["necrosis"],
            wilting=stats["wilting"],
            spots=stats["spots"],
            lesion=stats["lesion"],
            powdery=stats["powdery"],
        )
        ctx = context or ContextData()
        engine = DifferentialEngine()
        ranked = engine.rank(ev, ctx)

        if not ranked:
            raise ImageValidationError("No analyzable features detected; retake with better lighting/focus.")

        primary = ranked[0]
        alternatives = [{"cause": h.cause, "probability": h.probability} for h in ranked[1:4]]

        severity = _severity(primary.probability, ev, ctx)
        requires_expert = (severity in ("severe", "moderate") and primary.probability < 55) or (
            severity == "severe"
        )

        action = primary.action_guidance or "Confirm with field/lab verification."
        if requires_expert:
            action += " Expert (agronomist) review is recommended before taking action."

        visible = _visible_symptoms(stats)

        return ImageAnalysisResult(
            primary_diagnosis=primary.cause,
            confidence_pct=round(min(primary.probability, 90.0), 1),
            alternatives=alternatives,
            severity=severity,
            affected_part="leaf",
            visible_symptoms=visible,
            recommended_action=action,
            requires_expert=requires_expert,
        )


def _extract_visual_signals(image: Image.Image) -> dict:
    """Heuristic color/texture analysis to detect symptom signals.

    This is a lightweight MVP proxy for visual signals; production would use
    a trained vision model. It detects broad patterns (chlorosis, necrosis)
    from color distribution and returns a cautious feature set.
    """
    import numpy as np

    rgb = np.array(image.convert("RGB"), dtype=np.float32)
    h, w, _ = rgb.shape
    signals = {
        "chlorosis": False,
        "interveinal": False,
        "marginal_burn": False,
        "necrosis": False,
        "wilting": False,
        "spots": False,
        "lesion": False,
        "powdery": False,
        "symptom_summary": "",
    }
    if h == 0 or w == 0:
        return signals

    # green channel ratios
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    greenness = g / (r + g + b + 1e-6)
    yellowness = (r + g) / (r + g + b + 1e-6) * (g / (r + 1e-6))
    mean_green = float(np.mean(greenness))
    yellow_fraction = float(np.mean((greenness < 0.40) & (g > r) & (g > b)))
    brown_fraction = float(np.mean((r > g) & (r > b) & (r > 90)))
    dark_fraction = float(np.mean(rgb.max(axis=2) < 60))

    if yellow_fraction > 0.25:
        signals["chlorosis"] = True
    if brown_fraction > 0.20:
        signals["necrosis"] = True
        signals["marginal_burn"] = True  # heuristic
    if dark_fraction > 0.2:
        signals["wilting"] = True

    summary = []
    if signals["chlorosis"]:
        summary.append("yellowing (chlorosis)")
    if signals["necrosis"]:
        summary.append("browning/necrosis")
    if signals["wilting"]:
        summary.append("dark/wilted appearance")
    signals["symptom_summary"] = ", ".join(summary) or "no strong color anomalies detected"

    return signals


def _visible_symptoms(stats: dict) -> list[str]:
    out = []
    if stats["chlorosis"]:
        out.append("Chlorosis (yellowing)")
    if stats["necrosis"]:
        out.append("Necrosis / browning")
    if stats["wilting"]:
        out.append("Wilt / stressed appearance")
    return out or ["Image quality limited; no clear visible symptom pattern detected"]


def _severity(prob: float, ev: SymptomEvidence, ctx: ContextData) -> str:
    score = 0
    if prob > 60:
        score += 1
    if ev.necrosis:
        score += 1
    if ev.wilting:
        score += 1
    if ctx.soil_ec_ds_m is not None and ctx.soil_ec_ds_m > 4.0:
        score += 1
    if score >= 3:
        return "severe"
    if score == 2:
        return "moderate"
    return "mild"
