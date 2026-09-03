"""Weapons, guidance types, countermeasure principles and damage profiles in Nuclear Option."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GuidanceType(str, Enum):
    UNGUIDED = "Unguided"
    INFRARED = "Infrared (IR / Heatseeking)"
    SARH = "Semi-Active Radar Homing (SARH)"
    ARH = "Active Radar Homing (ARH / Fire-and-Forget)"
    ANTI_RADIATION = "Anti-Radiation (ARM / Radar-Homing)"
    OPTICAL_GPS = "Optical / Laser / GNSS"
    BEAM_RIDER = "Laser Beam Riding"


class WarheadClass(str, Enum):
    KINETIC = "Kinetic"
    HE_FRAG = "High-Explosive Fragmentation"
    ARMOR_PIERCING = "Armor-Piercing / Shaped Charge"
    THERMOBARIC = "Thermobaric"
    TACTICAL_NUCLEAR = "Tactical Nuclear (Kiloton range)"
    STRATEGIC_NUCLEAR = "Strategic Nuclear (Megaton range)"


class WeaponProfile(BaseModel):
    key: str
    display_name: str
    guidance: GuidanceType
    warhead: WarheadClass
    typical_range_km: float
    max_speed_mach: float
    countermeasures: List[str] = Field(default_factory=list)
    tactical_advice: str = ""


KNOWN_WEAPONS: Dict[str, WeaponProfile] = {
    "IRMS1": WeaponProfile(
        key="IRMS1",
        display_name="Scimitar IRMS (Short Range AAM)",
        guidance=GuidanceType.INFRARED,
        warhead=WarheadClass.HE_FRAG,
        typical_range_km=8.0,
        max_speed_mach=2.8,
        countermeasures=["Flares", "Throttle Reduction", "High-G Break Turn"],
        tactical_advice="Cut afterburner, pop flares in bursts, turn hard into or 90-degrees across missile flight path.",
    ),
    "SARH1": WeaponProfile(
        key="SARH1",
        display_name="Lance SARH (Medium Range AAM)",
        guidance=GuidanceType.SARH,
        warhead=WarheadClass.HE_FRAG,
        typical_range_km=25.0,
        max_speed_mach=3.5,
        countermeasures=["Chaff", "Radar Notching (beam 90 deg)", "Break Lock of Launch Platform"],
        tactical_advice="Fly perpendicular (beam 90°) to the illuminating radar, drop chaff, dive to break line-of-sight.",
    ),
    "ARH1": WeaponProfile(
        key="ARH1",
        display_name="Scythe ARH (Long Range Active Radar AAM)",
        guidance=GuidanceType.ARH,
        warhead=WarheadClass.HE_FRAG,
        typical_range_km=45.0,
        max_speed_mach=4.0,
        countermeasures=["Chaff", "Notching", "Terrain Masking"],
        tactical_advice="Once active (high-pitch RWR tone), notch the missile itself, dispense chaff, and use terrain.",
    ),
    "AGM1": WeaponProfile(
        key="AGM1",
        display_name="Prowler AGM (Air-to-Ground Missile)",
        guidance=GuidanceType.OPTICAL_GPS,
        warhead=WarheadClass.ARMOR_PIERCING,
        typical_range_km=12.0,
        max_speed_mach=1.5,
        countermeasures=["Hard Cover", "Smoke", "C-RAM Interception"],
        tactical_advice="Interceptable by SPAAG and CIWS if detected early.",
    ),
    "NuclearCruise": WeaponProfile(
        key="NuclearCruise",
        display_name="Tactical Nuclear Cruise Missile",
        guidance=GuidanceType.OPTICAL_GPS,
        warhead=WarheadClass.TACTICAL_NUCLEAR,
        typical_range_km=70.0,
        max_speed_mach=1.8,
        countermeasures=["Long Range SAM Interception", "Air-to-Air Missile Intercept"],
        tactical_advice="Must be intercepted at high priority before reaching terminal phase. Massive EMP and blast radius.",
    ),
}


def lookup_weapon(weapon_key: str) -> Optional[WeaponProfile]:
    """Find a weapon profile by key or substring."""
    for k, v in KNOWN_WEAPONS.items():
        if k.lower() in weapon_key.lower():
            return v
    return None
