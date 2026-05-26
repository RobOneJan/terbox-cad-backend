from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator


class UseCaseType(str, Enum):
    urban = "urban"
    gastronomy = "gastronomy"
    combined = "combined"

class SizeOption(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"

class FloorOption(str, Enum):
    withFloor = "withFloor"
    withoutFloor = "withoutFloor"

class MountingOption(str, Enum):
    noMounting = "noMounting"
    bolted = "bolted"
    underPaving = "underPaving"
    concrete = "concrete"

class WallMaterial(str, Enum):
    wpc = "wpc"
    realWood = "realWood"
    glass = "glass"
    meshFence = "meshFence"
    meshFenceWithPrivacy = "meshFenceWithPrivacy"
    corrugatedSheet = "corrugatedSheet"

class WallHeight(str, Enum):
    full = "full"
    half = "half"
    none = "none"

class FloorMaterial(str, Enum):
    wpcFloor = "wpcFloor"
    woodFloor = "woodFloor"

class FloorWoodType(str, Enum):
    bankirai = "bankirai"
    douglas = "douglas"

class WpcColor(str, Enum):
    cedar = "cedar"
    darkGrey = "darkGrey"
    teak = "teak"
    ipe = "ipe"
    lightGrey = "lightGrey"

class GlassType(str, Enum):
    frosted = "frosted"
    clear = "clear"

class WoodType(str, Enum):
    spruce = "spruce"
    pine = "pine"
    larch = "larch"
    douglas = "douglas"
    oak = "oak"
    bankirai = "bankirai"

class ClosureType(str, Enum):
    rollerDoor = "rollerDoor"
    doubleDoor = "doubleDoor"
    singleDoor = "singleDoor"
    slidingDoor = "slidingDoor"
    open = "open"

class FeatureKey(str, Enum):
    led = "led"
    solar = "solar"
    camera = "camera"
    carCharging = "carCharging"
    bikeCharging = "bikeCharging"
    app = "app"
    greening = "greening"
    power = "power"
    highPower = "highPower"
    battery = "battery"
    heater = "heater"

_VALID_RAL_COLORS = {
    "ral9005", "ral9016", "ral7016", "ral7035", "ral3000",
    "ral5010", "ral6005", "ral8017", "ral1021", "ral2004", "other",
}
_VALID_SHUTTER_COLORS = {
    "ral9005", "ral9016", "ral7016", "ral7035", "ral3000",
    "ral5010", "ral6005", "ral8017", "other",
}

class CustomSize(BaseModel):
    width: str
    height: str
    length: str

class TerBoxConfiguration(BaseModel):
    useCase: UseCaseType
    size: SizeOption
    customSize: Optional[CustomSize] = None
    mounting: MountingOption
    color: str
    customColor: Optional[str] = None
    floor: FloorOption
    floorMaterial: Optional[FloorMaterial] = None
    floorWpcColor: Optional[WpcColor] = None
    floorWoodType: Optional[FloorWoodType] = None
    wallHeight: WallHeight
    wallMaterial: Optional[WallMaterial] = None
    wpcColor: Optional[WpcColor] = None
    glassType: Optional[GlassType] = None
    woodType: Optional[WoodType] = None
    closureType: Optional[ClosureType] = None
    shutterColor: Optional[str] = None
    customShutterColor: Optional[str] = None
    closureMaterial: Optional[WallMaterial] = None
    closureWpcColor: Optional[WpcColor] = None
    closureGlassType: Optional[GlassType] = None
    closureWoodType: Optional[WoodType] = None
    features: List[FeatureKey]

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if v not in _VALID_RAL_COLORS:
            raise ValueError(f"invalid color: {v}")
        return v

    @field_validator("shutterColor")
    @classmethod
    def validate_shutter_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_SHUTTER_COLORS:
            raise ValueError(f"invalid shutterColor: {v}")
        return v

    @model_validator(mode="after")
    def validate_conditional_fields(self) -> "TerBoxConfiguration":
        if self.color == "other" and not self.customColor:
            raise ValueError("customColor required when color is other")
        if self.shutterColor == "other" and not self.customShutterColor:
            raise ValueError("customShutterColor required when shutterColor is other")
        if self.useCase == UseCaseType.gastronomy and self.closureType is not None:
            raise ValueError("closureType must not be set for gastronomy")
        return self

class ComputedConfig(BaseModel):
    module_count: int
    module_length_cm: float

# --- AB1000 box configurator ---

class BoxConfig(BaseModel):
    length_mm: float
    width_mm: float
    height_mm: float
    with_roof: bool = True
    with_floor: bool = True
    walls: WallHeight = WallHeight.full
    wall_material: Optional[WallMaterial] = None
    wall_wpc_color: Optional[WpcColor] = None
    floor_material: Optional[FloorMaterial] = None
    floor_wpc_color: Optional[WpcColor] = None
    roller_door: bool = False
    roller_door_color: Optional[str] = None

    @field_validator("roller_door_color")
    @classmethod
    def validate_roller_door_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_SHUTTER_COLORS:
            raise ValueError(f"invalid roller_door_color: {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "length_mm": 3000,
                "width_mm": 1500,
                "height_mm": 2200,
                "with_roof": True,
                "with_floor": True,
                "walls": "full",
                "wall_material": "wpc",
                "wall_wpc_color": "cedar",
                "floor_material": "wpcFloor",
                "floor_wpc_color": "cedar",
                "roller_door": False,
                "roller_door_color": None,
            }
        }
    }

class BOMItem(BaseModel):
    component_key: str
    article_nr: str
    description: str
    qty: int
    length_mm: Optional[float] = None
    note: Optional[str] = None

class BOMResponse(BaseModel):
    items: List[BOMItem]
    total_parts: int
