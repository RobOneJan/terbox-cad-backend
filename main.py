import os
from fastapi import FastAPI, HTTPException, Security, Depends, Body
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from models import BoxConfig, BoxAngebotRequest
import assembly_rules
import cad_engine
import angebot_engine
import quote_logic
import bom_excel

_BOX_EXAMPLES = {
    "full_walls_wpc": {
        "summary": "Standard 3 m box – full WPC walls, WPC floor",
        "value": {
            "width_mm": 3000, "depth_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "wpc", "wall_wpc_color": "cedar",
            "floor_material": "wpcFloor", "floor_wpc_color": "cedar",
            "roller_door": False, "with_solar": False,
            "with_bike_stand": True, "frame_color": "anthrazitgrau",
        },
    },
    "roller_door": {
        "summary": "Roller door (RAL9005 black), corrugated walls, wood floor",
        "value": {
            "width_mm": 3000, "depth_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "corrugatedSheet",
            "floor_material": "woodFloor",
            "roller_door": True, "roller_door_color": "ral9005",
            "with_solar": False, "with_bike_stand": True, "frame_color": "tiefschwarz",
        },
    },
    "bike_storage": {
        "summary": "WPC walls, WPC floor, bike stands inside",
        "value": {
            "width_mm": 3000, "depth_mm": 1500, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "wpc", "wall_wpc_color": "darkGrey",
            "floor_material": "wpcFloor", "floor_wpc_color": "darkGrey",
            "roller_door": False, "with_solar": False,
            "with_bike_stand": True, "frame_color": "anthrazitgrau",
        },
    },
    "solar": {
        "summary": "Solar panels on roof – anthrazite frame, WPC walls",
        "value": {
            "width_mm": 4000, "depth_mm": 2200, "height_mm": 2200,
            "with_roof": True, "with_floor": True,
            "walls": "full", "wall_material": "wpc", "wall_wpc_color": "cedar",
            "floor_material": "wpcFloor", "floor_wpc_color": "cedar",
            "roller_door": False, "with_solar": True,
            "with_bike_stand": True, "frame_color": "anthrazitgrau",
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


@app.post("/ab1000/preview", dependencies=[Depends(verify_api_key)])
async def ab1000_preview(config: BoxConfig = Body(openapi_examples=_BOX_EXAMPLES)):
    try:
        glb = cad_engine.generate_ab1000_preview_glb(
            width_mm=config.width_mm,
            depth_mm=config.depth_mm,
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
            with_solar=config.with_solar,
            with_bike_stand=config.with_bike_stand,
            frame_color=config.frame_color.value if config.frame_color else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return Response(
        content=glb,
        media_type="model/gltf-binary",
        headers={"Content-Disposition": "attachment; filename=preview.glb"},
    )


@app.post("/ab1000/bom-xlsx", dependencies=[Depends(verify_api_key)])
async def ab1000_bom_xlsx(config: BoxConfig = Body(openapi_examples=_BOX_EXAMPLES)):
    items = assembly_rules.bom_for_box(
        config.width_mm, config.depth_mm, config.height_mm,
        with_roof=config.with_roof,
        with_floor=config.with_floor,
        walls=config.walls.value,
        wall_material=config.wall_material.value if config.wall_material else None,
        wall_wpc_color=config.wall_wpc_color.value if config.wall_wpc_color else None,
        floor_material=config.floor_material.value if config.floor_material else None,
        floor_wpc_color=config.floor_wpc_color.value if config.floor_wpc_color else None,
        roller_door=config.roller_door,
        roller_door_color=config.roller_door_color,
        with_solar=config.with_solar,
        with_bike_stand=config.with_bike_stand,
    )
    try:
        xlsx = bom_excel.generate_bom_xlsx(config, items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    filename = f"Stueckliste_{int(config.width_mm)}x{int(config.depth_mm)}x{int(config.height_mm)}.xlsx"
    return Response(
        content=xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/ab1000/angebot-konfiguration", dependencies=[Depends(verify_api_key)])
async def ab1000_angebot_konfiguration(req: BoxAngebotRequest):
    """Generate a quote PDF from a BoxConfig + price table."""
    try:
        from models import AngebotRequest
        positionen = quote_logic.box_config_to_positionen(req.config, req.preise)
        if not positionen:
            raise HTTPException(
                status_code=422,
                detail="No positions generated — check that at least one price is set in 'preise'.",
            )
        angebot_req = AngebotRequest(
            angebots_nr=req.angebots_nr,
            datum=req.datum,
            anrede=req.anrede,
            name=req.name,
            firma=req.firma,
            strasse=req.strasse,
            plz=req.plz,
            ort=req.ort,
            land=req.land,
            kundennummer=req.kundennummer,
            ansprechpartner=req.ansprechpartner,
            positionen=positionen,
            mwst_prozent=req.mwst_prozent,
        )
        pdf = angebot_engine.generate_angebot_pdf(angebot_req)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    filename = f"Angebot_{req.angebots_nr}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
