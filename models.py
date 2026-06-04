from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


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

class FrameColor(str, Enum):
    tiefschwarz      = "tiefschwarz"       # RAL 9005
    verkehrsweiss    = "verkehrsweiss"      # RAL 9016
    anthrazitgrau    = "anthrazitgrau"      # RAL 7016
    lichtgrau        = "lichtgrau"          # RAL 7035
    feuerrot         = "feuerrot"           # RAL 3000
    enzianblau       = "enzianblau"         # RAL 5010
    moosgruen        = "moosgruen"          # RAL 6005
    schokoladenbraun = "schokoladenbraun"   # RAL 8017

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
    width_mm: float
    depth_mm: float
    height_mm: float

    @model_validator(mode="after")
    def clamp_dimensions(self) -> "BoxConfig":
        self.width_mm  = min(self.width_mm,  12000.0)
        self.depth_mm  = min(self.depth_mm,   2500.0)
        self.height_mm = min(self.height_mm,  3000.0)
        return self
    with_roof: bool = True
    with_floor: bool = True
    walls: WallHeight = WallHeight.full
    wall_material: Optional[WallMaterial] = None
    wall_wpc_color: Optional[WpcColor] = None
    floor_material: Optional[FloorMaterial] = None
    floor_wpc_color: Optional[WpcColor] = None
    roller_door: bool = False
    roller_door_color: Optional[str] = None
    with_solar: bool = False
    with_bike_stand: bool = True
    frame_color: Optional[FrameColor] = Field(default=None, title="Frame Color",
        description="Steel frame color. Applies to all tubes, connectors, roof substructure and Schienen.")

    @field_validator("roller_door_color")
    @classmethod
    def validate_roller_door_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_SHUTTER_COLORS:
            raise ValueError(f"invalid roller_door_color: {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "width_mm": 3000,
                "depth_mm": 1500,
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
                "with_solar": False,
                "with_bike_stand": True,
                "frame_color": "anthrazitgrau",
            }
        }
    }

class AngebotPosition(BaseModel):
    beschreibung: str
    menge: float = 1.0
    einheit: str = "Stk"
    einzelpreis: float

class AngebotRequest(BaseModel):
    angebots_nr: str
    datum: Optional[str] = None          # "DD.MM.YYYY"; defaults to today
    anrede: Optional[str] = None         # "Herrn", "Frau", …
    name: str
    firma: Optional[str] = None
    strasse: str
    plz: str
    ort: str
    land: str = "Deutschland"
    kundennummer: Optional[str] = None
    ansprechpartner: str = "Sven Terhardt"
    positionen: List[AngebotPosition]
    mwst_prozent: float = 19.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "angebots_nr": "AN-1001",
                "datum": "04.06.2026",
                "anrede": "Herrn",
                "name": "Max Mustermann",
                "firma": "Musterfirma GmbH",
                "strasse": "Musterstraße 1",
                "plz": "12345",
                "ort": "Musterstadt",
                "land": "Deutschland",
                "kundennummer": "1002",
                "ansprechpartner": "Sven Terhardt",
                "positionen": [
                    {
                        "beschreibung": "Grundkorpus\n4,00 m lang, 2,20 m tief, 2,20 m hoch\nverzinkter Stahl, RAL 7016 anthrazit grau beschichtet\ninklusive Dach und Dachrinne",
                        "menge": 1.0,
                        "einheit": "Stk",
                        "einzelpreis": 3600.0
                    },
                    {
                        "beschreibung": "WPC Holzoptik\nFarbe Teak\n2 Wände 2,00 x 2,20 m\n2 Wände 1,80 x 2,20 m",
                        "menge": 1.0,
                        "einheit": "Stk",
                        "einzelpreis": 1450.0
                    },
                    {
                        "beschreibung": "Lieferkosten",
                        "menge": 1.0,
                        "einheit": "Stk",
                        "einzelpreis": 100.0
                    }
                ],
                "mwst_prozent": 19.0
            }
        }
    }


class BoxAngebotPreise(BaseModel):
    """Prices per component group. Set a field to None to exclude that group from the quote."""
    grundkorpus:      Optional[float] = None   # steel frame + connectors + roof
    wand:             Optional[float] = None   # complete wall system (all 3 walls)
    boden:            Optional[float] = None   # floor panel
    rolltor:          Optional[float] = None   # roller door
    fahrradstaender:  Optional[float] = None   # bike stand system (rail + racks)
    solar:            Optional[float] = None   # solar panels
    solar_pro_panel:  bool = False             # True → solar price is per panel (qty=n), False → lump sum
    lieferkosten:     Optional[float] = None   # delivery
    extras:           List[AngebotPosition] = []  # additional free-form positions appended at the end

class BoxAngebotRequest(BaseModel):
    config:           BoxConfig
    preise:           BoxAngebotPreise
    # Angebot header
    angebots_nr:      str
    datum:            Optional[str] = None     # "DD.MM.YYYY"; defaults to today
    # Customer
    anrede:           Optional[str] = None
    name:             str
    firma:            Optional[str] = None
    strasse:          str
    plz:              str
    ort:              str
    land:             str = "Deutschland"
    kundennummer:     Optional[str] = None
    ansprechpartner:  str = "Sven Terhardt"
    mwst_prozent:     float = 19.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "width_mm": 3600, "depth_mm": 2000, "height_mm": 2200,
                    "with_roof": True, "with_floor": True,
                    "walls": "full", "wall_material": "wpc", "wall_wpc_color": "teak",
                    "roller_door": False, "with_solar": False,
                    "frame_color": "anthrazitgrau",
                },
                "preise": {
                    "grundkorpus": 3060.0,
                    "wand": 1320.0,
                    "boden": None,
                    "rolltor": None,
                    "fahrradstaender": 290.0,
                    "solar": None,
                    "solar_pro_panel": False,
                    "lieferkosten": 100.0,
                    "extras": [
                        {"beschreibung": "LED Lichter\ninklusive", "menge": 1.0, "einheit": "Stk", "einzelpreis": 150.0}
                    ],
                },
                "angebots_nr": "AN-1001",
                "datum": "04.06.2026",
                "anrede": "Herrn",
                "name": "Max Mustermann",
                "firma": "Musterfirma GmbH",
                "strasse": "Musterstraße 1",
                "plz": "12345",
                "ort": "Musterstadt",
                "land": "Deutschland",
                "kundennummer": "1002",
                "ansprechpartner": "Sven Terhardt",
                "mwst_prozent": 19.0,
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
