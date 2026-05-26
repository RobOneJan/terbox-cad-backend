import os
from fastapi import FastAPI, HTTPException, Security, Depends, Body
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from models import TerBoxConfiguration, BoxConfig, BOMItem, BOMResponse
import rules
import assembly_rules
import cad_engine

_BOX_EXAMPLES = {
    "full_walls_wpc": {
        "summary": "Standard 3 m box – full WPC walls, WPC floor",
        "value": {
            "length_mm": 3000, "width_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "wpc", "wall_wpc_color": "cedar",
            "floor_material": "wpcFloor", "floor_wpc_color": "cedar",
            "roller_door": False,
        },
    },
    "roller_door": {
        "summary": "Roller door (RAL9005 black), corrugated walls, wood floor",
        "value": {
            "length_mm": 3000, "width_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "corrugatedSheet",
            "floor_material": "woodFloor",
            "roller_door": True, "roller_door_color": "ral9005",
        },
    },
    "bike_storage": {
        "summary": "WPC walls, WPC floor, bike stands inside",
        "value": {
            "length_mm": 3000, "width_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "wpc", "wall_wpc_color": "darkGrey",
            "floor_material": "wpcFloor", "floor_wpc_color": "darkGrey",
            "roller_door": False,
        },
    },
    "half_walls_glass": {
        "summary": "Wide box – half glass walls, wood floor, no door",
        "value": {
            "length_mm": 3000, "width_mm": 2800, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "half", "wall_material": "glass",
            "floor_material": "woodFloor",
            "roller_door": False,
        },
    },
}

app = FastAPI(title="TER BOX CAD Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ter-box.com",
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

_API_KEY = os.environ.get("API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(key: str = Security(_api_key_header)):
    if not _API_KEY or key != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.post("/preview", dependencies=[Depends(verify_api_key)])
async def preview(config: TerBoxConfiguration):
    computed = rules.compute_config(config)
    try:
        obj_content = cad_engine.generate_preview_obj(config, computed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Response(
        content=obj_content,
        media_type="model/obj",
        headers={"Content-Disposition": "attachment; filename=preview.obj"},
    )


@app.post("/ab1000/preview", dependencies=[Depends(verify_api_key)])
async def ab1000_preview(config: BoxConfig = Body(examples=_BOX_EXAMPLES)):
    try:
        obj_content = cad_engine.generate_ab1000_preview_obj(
            length_mm=config.length_mm,
            width_mm=config.width_mm,
            height_mm=config.height_mm,
            with_roof=config.with_roof,
            with_floor=config.with_floor,
            walls=config.walls.value,
            wall_material=config.wall_material.value if config.wall_material else None,
            wall_wpc_color=config.wall_wpc_color.value if config.wall_wpc_color else None,
            floor_material=config.floor_material.value if config.floor_material else None,
            floor_wpc_color=config.floor_wpc_color.value if config.floor_wpc_color else None,
            roller_door=config.roller_door,
            roller_door_color=config.roller_door_color,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Response(
        content=obj_content,
        media_type="model/obj",
        headers={"Content-Disposition": "attachment; filename=ab1000_preview.obj"},
    )



@app.post("/ab1000/bom", dependencies=[Depends(verify_api_key)])
async def ab1000_bom(config: BoxConfig = Body(examples=_BOX_EXAMPLES)):
    items = assembly_rules.bom_for_box(
        config.length_mm,
        config.width_mm,
        config.height_mm,
        with_roof=config.with_roof,
        with_floor=config.with_floor,
        walls=config.walls.value,
        wall_material=config.wall_material.value if config.wall_material else None,
        floor_material=config.floor_material.value if config.floor_material else None,
        roller_door=config.roller_door,
    )
    return BOMResponse(
        items=[BOMItem(**item) for item in items],
        total_parts=sum(i["qty"] for i in items),
    )
