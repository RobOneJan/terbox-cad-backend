from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from models import TerBoxConfiguration
import rules
import cad_engine

app = FastAPI(title="TER BOX CAD Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/preview")
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
