# AI Image Analysis Pipeline

## Workflow

1. **Guidance** — before capture/upload, show capture guidance (sharp, good lighting, affected + healthy tissue, multiple images, full-plant context).
2. **Ingest** — upload (multipart), store to object storage; record image_uploads row.
3. **Validation** — check file type, size, EXIF orientation, minimum resolution, not corrupted. Reject with clear messages.
4. **Preprocessing** — resize/normalize, correct exposure/white balance, crop if needed, encode safely.
5. **Crop & Organ Identification** — optional species + leaf/fruit classification.
6. **Feature/Symptom Extraction** — detectable patterns: chlorosis (general/interveinal/marginal), necrosis, spots, wilting, deformation, burn, sunburn, abrasion, gall/sticky, etc., plus affected part.
7. **Classification** — produce a probability distribution over diagnostic categories:
   - fungal/bacterial/viral disease, pest damage, nutrient deficiency, heat damage, sunburn, salinity damage, water stress, sand abrasion, physical injury, healthy.
8. **Differential Ranking** — combine CV output with contextual signals (soil moisture/EC, water EC, temp, fertilizer/irrigation history, species, stage, disease/pest history) via the differential engine to rank causes.
9. **Confidence Scoring** — based on agreement across signals, image quality, and completeness of input data. Confidence down-weighted when context missing.
10. **Output** — primary possible diagnosis + confidence %, alternatives with %, severity, affected part, visible symptoms, recommended next step, and `requires_expert` flag.
11. **Human Review** — agronomist confirms/rejects/modifies; stored for future learning. Low-confidence / severe / high-cost → mandatory expert review.

## Safety
- Always labeled **"Possible ..."** unless confirmed by lab/analytical data.
- Never recommend pesticide/fertilizer from image alone if salinity/disease/root/water could explain symptoms.
- Differential engine runs before any action recommendation.

## MVP Implementation
Deterministic symptom-detection + probabilistic scoring engine (rule-based gradient boosting over image-derived features + context). Pluggable interface (`ImageAnalyzer`) so a real CNN (e.g., on-device TensorFlow / external vision API) can replace the MVP classifier without changing the pipeline.

## Model Versioning
`ai_diagnoses.model_version` stored; a model registry records deployed versions for auditability.

## Feedback Loop
Review decisions update a curated dataset that retrains/refines the classifier (Phase 3).
