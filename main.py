import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from models import TerBoxConfiguration
import rules
import cad_engine

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
