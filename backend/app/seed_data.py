"""Seed data: crop species, varieties, coefficients, nutrient deficiency references."""

from .models import (
    CropCoefficient,
    CropSpecies,
    FertilizerProduct,
    NutrientDeficiency,
    PhenologyStage,
    Variety,
)


def seed_species(db):
    species = [
        {
            "code": "date", "name_en": "Date palm", "name_ar": "نخيل التمر", "name_fr": "Palmier dattier",
            "family": "Arecaceae", "default_kc": 0.9, "salinity_threshold_ds_m": 4.0,
            "critical_ec_ds_m": 8.0, "heat_threshold_c": 42.0, "frost_threshold_c": -5.0,
        },
        {
            "code": "olive", "name_en": "Olive", "name_ar": "زيتون", "name_fr": "Olivier",
            "family": "Oleaceae", "default_kc": 0.5, "salinity_threshold_ds_m": 4.0,
            "critical_ec_ds_m": 6.0, "heat_threshold_c": 40.0, "frost_threshold_c": -7.0,
        },
        {
            "code": "pomegranate", "name_en": "Pomegranate", "name_ar": "رمان", "name_fr": "Grenadier",
            "family": "Lythraceae", "default_kc": 0.8, "salinity_threshold_ds_m": 3.0,
            "critical_ec_ds_m": 5.0, "heat_threshold_c": 40.0, "frost_threshold_c": -6.0,
        },
        {
            "code": "citrus", "name_en": "Citrus", "name_ar": "حمضيات", "name_fr": "Agrumes",
            "family": "Rutaceae", "default_kc": 0.85, "salinity_threshold_ds_m": 1.7,
            "critical_ec_ds_m": 3.0, "heat_threshold_c": 38.0, "frost_threshold_c": -2.0,
        },
        {
            "code": "grape", "name_en": "Grapevine", "name_ar": "عنب", "name_fr": "Vigne",
            "family": "Vitaceae", "default_kc": 0.7, "salinity_threshold_ds_m": 1.5,
            "critical_ec_ds_m": 2.5, "heat_threshold_c": 40.0, "frost_threshold_c": -3.0,
        },
        {
            "code": "fig", "name_en": "Fig", "name_ar": "تين", "name_fr": "Figuier",
            "family": "Moraceae", "default_kc": 0.7, "salinity_threshold_ds_m": 3.0,
            "critical_ec_ds_m": 5.0, "heat_threshold_c": 42.0, "frost_threshold_c": -5.0,
        },
    ]
    created = []
    for s in species:
        exists = db.query(CropSpecies).filter_by(code=s["code"]).first()
        if exists:
            created.append(exists)
            continue
        obj = CropSpecies(**s)
        db.add(obj)
        db.flush()
        created.append(obj)

    # varieties
    varieties = [
        # species_id set after flush
        ("date", "Medjool", 0.8, 0.9, 0.6, 0.3, 0.5, 900, 0.5, 0.9, 0.7),
        ("date", "Deglet Nour", 0.9, 0.9, 0.7, 0.4, 0.5, 800, 0.4, 0.9, 0.7),
        ("date", "Barhi", 0.9, 0.9, 0.8, 0.4, 0.6, 700, 0.3, 0.8, 0.7),
        ("olive", "Arbequina", 0.8, 0.8, 0.7, 0.6, 0.7, 500, 0.4, 0.8, 0.5),
        ("olive", "Koroneiki", 0.9, 0.9, 0.7, 0.7, 0.8, 400, 0.4, 0.9, 0.6),
        ("olive", "Picual", 0.9, 0.8, 0.8, 0.8, 0.7, 450, 0.3, 0.9, 0.6),
        ("pomegranate", "Wonderful", 0.7, 0.8, 0.6, 0.5, 0.6, 700, 0.4, 0.8, 0.6),
        ("pomegranate", "Hicaznar", 0.8, 0.8, 0.7, 0.5, 0.6, 650, 0.3, 0.8, 0.6),
        ("citrus", "Navel Orange", 0.6, 0.6, 0.4, 0.4, 0.6, 700, 0.4, 0.8, 0.7),
        ("citrus", "Valencia Orange", 0.7, 0.6, 0.5, 0.4, 0.6, 700, 0.3, 0.8, 0.7),
        ("citrus", "Lemon", 0.7, 0.7, 0.5, 0.3, 0.6, 650, 0.3, 0.7, 0.6),
        ("grape", "Flame Seedless", 0.7, 0.7, 0.5, 0.4, 0.6, 550, 0.4, 0.8, 0.7),
        ("grape", "Thompson Seedless", 0.8, 0.7, 0.5, 0.4, 0.6, 500, 0.4, 0.8, 0.7),
        ("fig", "Bursa Siyah", 0.8, 0.8, 0.6, 0.5, 0.6, 600, 0.3, 0.7, 0.5),
        ("fig", "Brown Turkey", 0.7, 0.8, 0.6, 0.5, 0.7, 600, 0.4, 0.7, 0.5),
    ]
    species_map = {s.code: s for s in created}
    for code, name, heat, drought, sal, frost, soil, waterreq, dis, market, mgmt in varieties:
        sp = species_map[code]
        exists = db.query(Variety).filter_by(species_id=sp.id, name=name).first()
        if exists:
            continue
        db.add(Variety(
            species_id=sp.id, name=name, heat_tolerance=heat, drought_tolerance=drought,
            salinity_tolerance=sal, frost_tolerance=frost, soil_compatibility=soil,
            water_requirement=waterreq, disease_susceptibility=dis, market_suitability=market,
            management_intensity=mgmt,
        ))

    # crop coefficients by stage
    stages_species = {
        "date": [("dormancy", 0.5), ("vegetative", 0.7), ("flowering", 0.85), ("fruit_development", 0.9), ("fruit_maturation", 0.85), ("post_harvest", 0.7)],
        "olive": [("dormancy", 0.3), ("vegetative", 0.5), ("flowering", 0.6), ("fruit_development", 0.7), ("fruit_maturation", 0.6), ("post_harvest", 0.5)],
        "pomegranate": [("dormancy", 0.3), ("vegetative", 0.6), ("flowering", 0.8), ("fruit_development", 0.85), ("fruit_maturation", 0.8), ("post_harvest", 0.6)],
        "citrus": [("dormancy", 0.5), ("vegetative", 0.65), ("flowering", 0.75), ("fruit_development", 0.8), ("fruit_maturation", 0.8), ("post_harvest", 0.65)],
        "grape": [("dormancy", 0.3), ("bud_break", 0.4), ("vegetative", 0.6), ("flowering", 0.7), ("fruit_set", 0.8), ("fruit_development", 0.85), ("fruit_maturation", 0.75), ("post_harvest", 0.5)],
        "fig": [("dormancy", 0.3), ("vegetative", 0.6), ("flowering", 0.7), ("fruit_development", 0.8), ("fruit_maturation", 0.75), ("post_harvest", 0.6)],
    }
    default_root_depth = {
        "date": 1.5, "olive": 1.2, "pomegranate": 1.0, "citrus": 1.0, "grape": 1.0, "fig": 1.0,
    }
    for code, stages in stages_species.items():
        sp = species_map[code]
        for stage_key, kc in stages:
            exists = db.query(CropCoefficient).filter_by(species_id=sp.id, stage_key=stage_key).first()
            if exists:
                continue
            db.add(CropCoefficient(
                species_id=sp.id, stage_key=stage_key, kc=kc,
                root_depth_m=default_root_depth[code],
            ))
            db.add(PhenologyStage(
                species_id=sp.id, stage_key=stage_key, name=stage_key.replace("_", " ").title(),
                day_range="",
            ))

    # nutrient deficiency references
    deficiencies = [
        ("N", "General chlorosis starting on older leaves", "old"),
        ("P", "Dark green/purple older leaves, reduced growth", "old"),
        ("K", "Marginal chlorosis and necrosis on older leaves", "old"),
        ("Ca", "Young leaves distorted, tip burn", "young"),
        ("Mg", "Interveinal chlorosis on older leaves", "old"),
        ("S", "Uniform chlorosis on young leaves", "young"),
        ("Fe", "Interveinal chlorosis on young leaves, often at high pH", "young"),
        ("Zn", "Small leaves, rosetting, interveinal chlorosis on young leaves", "young"),
        ("Mn", "Interveinal chlorosis on young leaves", "young"),
        ("B", "Shoot dieback, deformed growth, fruit issues", "young"),
        ("Cu", "Wilt, dieback, distorted new growth", "young"),
    ]
    for nutrient, symptoms, location in deficiencies:
        exists = db.query(NutrientDeficiency).filter_by(nutrient_code=nutrient).first()
        if exists:
            continue
        db.add(NutrientDeficiency(
            species_id=None, nutrient_code=nutrient, symptoms=symptoms,
            symptom_location=location,
            notes="Possible nutrient deficiency; confirm with soil/leaf analysis before applying fertilizer.",
        ))

    # fertilizer products
    products = [
        {"name": "NPK 20-20-20", "n_pct": 20, "p2o5_pct": 20, "k2o_pct": 20, "description": "Balanced water-soluble for fertigation"},
        {"name": "NPK 12-5-40", "n_pct": 12, "p2o5_pct": 5, "k2o_pct": 40, "description": "High potassium, for fruit development/maturation"},
        {"name": "Ammonium sulfate", "n_pct": 21, "p2o5_pct": 0, "k2o_pct": 0, "description": "Nitrogen source (acidifying; caution in salinity)"},
        {"name": "Potassium nitrate", "n_pct": 13, "p2o5_pct": 0, "k2o_pct": 44, "description": "N+K fertigation, low EC impact"},
        {"name": "Calcium nitrate", "n_pct": 15, "p2o5_pct": 0, "k2o_pct": 0, "ca_pct": 19, "description": "Calcium + nitrogen"},
    ]
    for p in products:
        exists = db.query(FertilizerProduct).filter_by(name=p["name"]).first()
        if exists:
            continue
        db.add(FertilizerProduct(**p))

    db.commit()
