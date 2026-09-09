"""Creates a fully-populated demo farm for exploration/testing."""

from datetime import datetime, timedelta

from .database import SessionLocal
from .models import (
    Block, CropCoefficient, CropSpecies, Farm, Field, IrrigationEvent, IrrigationSystem,
    Sensor, SensorMeasurement, SoilProfile, SoilTest, Task, Tree, WaterSource, WaterTest,
    WeatherForecast, WeatherObservation, Zone,
)
from .security import hash_password
from .models import User


def create_demo_data():
    db = SessionLocal()

    # ensure demo user exists
    demo = db.query(User).filter_by(email="demo@oasis.farm").first()
    if not demo:
        demo = User(
            email="demo@oasis.farm", password_hash=hash_password("demo1234"),
            full_name="Demo Farm Manager", role="manager", preferred_language="en",
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)

    # demo species
    date = db.query(CropSpecies).filter_by(code="date").first()
    pomegranate = db.query(CropSpecies).filter_by(code="pomegranate").first()
    olive = db.query(CropSpecies).filter_by(code="olive").first()

    farm = db.query(Farm).filter_by(name="Al Waha Demo Farm").first()
    if not farm:
        farm = Farm(
            owner_id=demo.id, name="Al Waha Demo Farm", climate_zone="arid",
            soil_type="sandy", water_source="groundwater - well", irrigation_system_type="drip",
            area_m2=250000, country="AE",
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

    field = db.query(Field).filter_by(farm_id=farm.id, name="Main Field").first()
    if not field:
        field = Field(farm_id=farm.id, name="Main Field", area_m2=250000)
        db.add(field)
        db.commit()
        db.refresh(field)

    def make_block(name, species, variety=None, count=200, age=6):
        block = db.query(Block).filter_by(field_id=field.id, name=name).first()
        if not block:
            from .models import Variety
            variety_id = None
            if variety:
                v = db.query(Variety).filter_by(species_id=species.id, name=variety).first()
                variety_id = v.id if v else None
            block = Block(
                field_id=field.id, name=name, crop_species_id=species.id, variety_id=variety_id,
                tree_count=count, tree_spacing_m=4, tree_age_years=age,
                irrigation_system_type="drip",
            )
            db.add(block)
            db.commit()
            db.refresh(block)
        return block

    date_block = make_block("North Date Palm", date, "Medjool", count=300, age=6)
    pom_block = make_block("Young Pomegranate", pomegranate, "Wonderful", count=150, age=2)
    olive_block = make_block("Olive Grove", olive, "Arbequina", count=200, age=4)

    # zones
    def make_zone(block, name, soil_texture="sandy", ec=2.0, water_ec=1.2):
        zone = db.query(Zone).filter_by(block_id=block.id, name=name).first()
        if not zone:
            zone = Zone(
                block_id=block.id, name=name, soil_texture=soil_texture,
                organic_matter_pct=0.8, soil_ph=7.8, soil_ec_ds_m=ec,
                water_ec_ds_m=water_ec, water_ph=7.6, root_zone_depth_m=1.0,
            )
            db.add(zone)
            db.commit()
            db.refresh(zone)
        return zone

    z1 = make_zone(date_block, "Date Zone A", ec=2.2)
    z2 = make_zone(date_block, "Date Zone B", ec=4.8)  # high salinity
    z3 = make_zone(pom_block, "Pomegranate Young Zone", ec=1.8)
    z4 = make_zone(olive_block, "Olive Zone", ec=2.5)

    # soil profiles
    for z in (z1, z2, z3, z4):
        if not db.query(SoilProfile).filter_by(zone_id=z.id).first():
            db.add(SoilProfile(
                zone_id=z.id, sand_pct=88, silt_pct=7, clay_pct=5,
                organic_matter_pct=0.8, bulk_density=1.55,
                field_capacity_pct=16, permanent_wilting_point_pct=6,
                root_zone_depth_m=1.0, is_assumed=False,
            ))

    # soil tests
    now = datetime.utcnow()
    if not db.query(SoilTest).filter_by(zone_id=z1.id).first():
        db.add(SoilTest(zone_id=z1.id, sampled_at=now - timedelta(days=30), ec_ds_m=1.9, ph=7.8, k_ppm=180))
        db.add(SoilTest(zone_id=z1.id, sampled_at=now - timedelta(days=10), ec_ds_m=2.2, ph=7.8, k_ppm=175))
        db.add(SoilTest(zone_id=z2.id, sampled_at=now - timedelta(days=30), ec_ds_m=3.5, ph=7.9))
        db.add(SoilTest(zone_id=z2.id, sampled_at=now - timedelta(days=10), ec_ds_m=4.8, ph=7.9))
        db.add(SoilTest(zone_id=z3.id, sampled_at=now - timedelta(days=10), ec_ds_m=1.8))
        db.add(SoilTest(zone_id=z4.id, sampled_at=now - timedelta(days=10), ec_ds_m=2.5))

    # water source + tests
    ws = db.query(WaterSource).filter_by(farm_id=farm.id).first()
    if not ws:
        ws = WaterSource(farm_id=farm.id, name="Well #1", source_type="groundwater", ec_ds_m=1.2, ph=7.6)
        db.add(ws)
        db.commit()
        db.refresh(ws)
    if not db.query(WaterTest).filter_by(water_source_id=ws.id).first():
        db.add(WaterTest(water_source_id=ws.id, sampled_at=now - timedelta(days=20), ec_ds_m=1.2, ph=7.6))

    # irrigation systems
    for z in (z1, z2, z3, z4):
        if not db.query(IrrigationSystem).filter_by(zone_id=z.id).first():
            db.add(IrrigationSystem(
                zone_id=z.id, system_type="drip", emitter_flow_lph=2.0,
                emitters_per_tree=8, irrigation_efficiency_pct=85.0, max_run_time_min=45,
            ))

    # sensors
    def sensor(zone, code, stype, unit):
        s = db.query(Sensor).filter_by(sensor_code=code).first()
        if not s:
            s = Sensor(farm_id=farm.id, zone_id=zone.id, sensor_code=code, sensor_type=stype, unit=unit, status="active")
            db.add(s)
            db.commit()
            db.refresh(s)
        return s

    s_m1 = sensor(z1, "S-MOIST-Z1", "soil_moisture", "%")
    s_e1 = sensor(z1, "S-EC-Z1", "soil_ec", "dS/m")
    s_m2 = sensor(z2, "S-MOIST-Z2", "soil_moisture", "%")
    s_e2 = sensor(z2, "S-EC-Z2", "soil_ec", "dS/m")

    # measurements over last days
    for s, vals in [(s_m1, [14, 13, 12, 11, 10, 9, 9, 8, 9]), (s_e1, [2.0, 2.1, 2.2, 2.2, 2.3]),
                    (s_m2, [15, 14, 13, 13, 12, 11, 11, 10, 10]), (s_e2, [3.5, 3.8, 4.1, 4.4, 4.8])]:
        if db.query(SensorMeasurement).filter_by(sensor_id=s.id).first():
            continue
        for i, v in enumerate(vals):
            db.add(SensorMeasurement(
                sensor_id=s.id, measured_at=now - timedelta(hours=(len(vals) - i) * 6),
                value=v, quality="good",
            ))

    # weather
    if not db.query(WeatherForecast).filter_by(farm_id=farm.id).first():
        db.add(WeatherObservation(farm_id=farm.id, observed_at=now - timedelta(hours=1), air_temp_c=34, rel_humidity_pct=25, wind_speed_ms=8))
        db.add(WeatherForecast(
            farm_id=farm.id, forecast_for=now + timedelta(days=1),
            min_temp_c=28, max_temp_c=46, humidity_pct=18, wind_speed_ms=12,
            heat_wave_risk=0.8, frost_risk=0.0, sandstorm_risk=0.3,
        ))

    # trees
    if not db.query(Tree).filter_by(zone_id=z3.id).first():
        for i in range(20):
            db.add(Tree(zone_id=z3.id, row_id=None, tree_code=f"POM-{i:03d}", species_id=pomegranate.id,
                        age_years=2, health_status="good"))

    if not db.query(Task).filter_by(farm_id=farm.id).first():
        db.add(Task(
            farm_id=farm.id, zone_id=z2.id, title="Inspect salinity in Date Zone B",
            description="Soil EC is 4.8 dS/m and rising. Take multi-depth samples and verify irrigation water quality.",
            assignee_role="manager", assigned_at=now, due_date=now + timedelta(days=1), status="open",
        ))
        db.add(Task(
            farm_id=farm.id, zone_id=z3.id, title="Irrigate young pomegranate trees",
            description="Young trees require priority moisture; prepare for tomorrow's heat wave (46C forecast).",
            assignee_role="technician", assigned_at=now, due_date=now, status="open",
        ))

    db.commit()
    db.close()
    return True


if __name__ == "__main__":
    create_demo_data()
    print("Demo data created.")
