"""Farm, field, block, zone, row, tree management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Block, CropCoefficient, CropSpecies, Farm, Field, Row, Tree, Variety, Zone,
)
from ..schemas import (
    BlockCreate, FarmCreate, FarmOut, FieldCreate, TreeCreate, ZoneCreate, ZoneOut,
)
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("", response_model=list[FarmOut])
def list_farms(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role in ("admin", "owner"):
        return db.query(Farm).all()
    return db.query(Farm).all()  # MVP: all visible; refine ownership later


@router.post("", response_model=FarmOut)
def create_farm(payload: FarmCreate, db: Session = Depends(get_db), user=Depends(require_min_role("owner"))):
    farm = Farm(**payload.model_dump(), owner_id=user.id)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    farm = db.query(Farm).filter_by(id=farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/{farm_id}/map")
def farm_map(farm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Export farm hierarchy with geo for map rendering."""
    farm = db.query(Farm).filter_by(id=farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    data = {
        "farm": {"id": farm.id, "name": farm.name, "boundary_wkt": farm.boundary_wkt},
        "fields": [],
    }
    for f in farm.fields:
        fdata = {"id": f.id, "name": f.name, "boundary_wkt": f.boundary_wkt, "blocks": []}
        for b in f.blocks:
            bdata = {
                "id": b.id, "name": b.name, "boundary_wkt": b.boundary_wkt,
                "crop_species_id": b.crop_species_id, "variety_id": b.variety_id,
                "tree_count": b.tree_count, "zones": [],
            }
            for z in b.zones:
                zdata = {
                    "id": z.id, "name": z.name, "boundary_wkt": z.boundary_wkt,
                    "soil_texture": z.soil_texture, "soil_ec_ds_m": z.soil_ec_ds_m,
                    "water_ec_ds_m": z.water_ec_ds_m, "trees": [
                        {"id": t.id, "code": t.tree_code, "geo_wkt": t.geo_wkt,
                         "health_status": t.health_status} for t in z.trees
                    ],
                }
                bdata["zones"].append(zdata)
            fdata["blocks"].append(bdata)
        data["fields"].append(fdata)
    return data


@router.post("/{farm_id}/fields")
def create_field(payload: FieldCreate, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    field = Field(**payload.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.post("/{farm_id}/blocks")
def create_block(payload: BlockCreate, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    block = Block(**payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.post("/blocks/{block_id}/zones", response_model=ZoneOut)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/zones/{zone_id}", response_model=ZoneOut)
def get_zone(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.post("/zones/{zone_id}/trees")
def create_tree(payload: TreeCreate, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    tree = Tree(**payload.model_dump())
    db.add(tree)
    db.commit()
    db.refresh(tree)
    return tree


@router.get("/trees/{tree_id}")
def get_tree(tree_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    tree = db.query(Tree).filter_by(id=tree_id).first()
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    return {
        "id": tree.id, "tree_code": tree.tree_code, "zone_id": tree.zone_id,
        "species_id": tree.species_id, "variety_id": tree.variety_id,
        "age_years": tree.age_years, "planting_date": tree.planting_date,
        "health_status": tree.health_status, "geo_wkt": tree.geo_wkt, "notes": tree.notes,
    }


# ---------- Crops & varieties ----------
@router.get("/crops/species")
def list_species(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(CropSpecies).all()


@router.get("/crops/species/{sid}/varieties")
def list_varieties(sid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Variety).filter_by(species_id=sid).all()


@router.get("/crops/species/{sid}/coefficients")
def list_coefficients(sid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(CropCoefficient).filter_by(species_id=sid).all()
