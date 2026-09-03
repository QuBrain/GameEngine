"""Pydantic schemas for Nuclear Option mission.json structure."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Vector3(BaseModel):
    model_config = ConfigDict(extra="allow")
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Quaternion(BaseModel):
    model_config = ConfigDict(extra="allow")
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


class WeaponSlot(BaseModel):
    model_config = ConfigDict(extra="allow")
    Key: str = ""


class SavedLoadout(BaseModel):
    model_config = ConfigDict(extra="allow")
    Selected: List[WeaponSlot] = Field(default_factory=list)


class UnitInstance(BaseModel):
    model_config = ConfigDict(extra="allow")
    UniqueName: str
    type: str = ""
    faction: str = ""
    playerControlled: bool = False
    playerControlledPriority: int = 0
    skill: float = 1.0
    bravery: float = 0.5
    fuel: float = 1.0
    globalPosition: Optional[Vector3] = None
    rotation: Optional[Quaternion] = None
    savedLoadout: Optional[SavedLoadout] = None


class Faction(BaseModel):
    model_config = ConfigDict(extra="allow")
    factionName: str
    startingBalance: float = 0.0
    regularIncome: float = 0.0
    reserveAirframes: int = 0
    reserveWarheads: int = 0
    startingWarheads: int = 0
    AIAircraftLimit: int = 10


class Objective(BaseModel):
    model_config = ConfigDict(extra="allow")
    UniqueName: str
    DisplayName: str = ""
    Faction: str = ""
    Type: str = "None"
    Hidden: bool = False
    completeOrder: Optional[str] = None
    targetUnits: List[str] = Field(default_factory=list)


class MissionSettings(BaseModel):
    model_config = ConfigDict(extra="allow")
    description: str = ""
    playerMode: str = "Singleplayer"
    allowRespawn: bool = False
    playerStartingRank: int = 0
    nuclearEscalationThreshold: float = 0.0
    strategicEscalationThreshold: float = 0.0


class Mission(BaseModel):
    model_config = ConfigDict(extra="allow")

    JsonVersion: int = 1
    MapKey: Dict[str, Any] = Field(default_factory=dict)
    missionSettings: MissionSettings = Field(default_factory=MissionSettings)
    environment: Dict[str, Any] = Field(default_factory=dict)

    factions: List[Faction] = Field(default_factory=list)
    airbases: List[Dict[str, Any]] = Field(default_factory=list)
    aircraft: List[UnitInstance] = Field(default_factory=list)
    vehicles: List[UnitInstance] = Field(default_factory=list)
    ships: List[UnitInstance] = Field(default_factory=list)
    buildings: List[UnitInstance] = Field(default_factory=list)
    objectives: List[Objective] = Field(default_factory=list)
    outcomes: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def total_unit_count(self) -> int:
        return (
            len(self.aircraft)
            + len(self.vehicles)
            + len(self.ships)
            + len(self.buildings)
        )

    def get_units_by_faction(self, faction_name: str) -> List[UnitInstance]:
        all_units = self.aircraft + self.vehicles + self.ships + self.buildings
        return [u for u in all_units if u.faction.lower() == faction_name.lower()]
