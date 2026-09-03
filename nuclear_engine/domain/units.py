"""Known unit profiles, roles, and tactical characteristics in Nuclear Option."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UnitCategory(str, Enum):
    AIRCRAFT = "Aircraft"
    HELICOPTER = "Helicopter"
    GROUND_VEHICLE = "GroundVehicle"
    AIR_DEFENSE = "AirDefense"
    WARSHIP = "Warship"
    STRUCTURE = "Structure"


class AirRole(str, Enum):
    LIGHT_ATTACK = "Light Attack / COIN"
    AIR_SUPERIORITY = "Air Superiority"
    MULTIROLE = "Multirole Fighter"
    ELECTRONIC_WARFARE = "Electronic Warfare / SEAD"
    STRATEGIC_BOMBER = "Heavy Strategic Bomber"
    ATTACK_HELICOPTER = "Attack Helicopter"
    VTOL_TRANSPORT = "VTOL Transport / Gunship"


class UnitProfile(BaseModel):
    key: str
    display_name: str
    category: UnitCategory
    role: Optional[str] = None
    radar_cross_section: float = 1.0  # Normalized RCS multiplier (e.g. 0.05 for stealth, 5.0 for heavy)
    crew: int = 1
    has_radar: bool = False
    has_rwr: bool = True
    has_jammer: bool = False
    description: str = ""
    common_weapons: List[str] = Field(default_factory=list)


# Registry of known Nuclear Option airframes & vehicles
KNOWN_AIRCRAFT: Dict[str, UnitProfile] = {
    "CI-22": UnitProfile(
        key="CI-22",
        display_name="CI-22 'Cricket'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.LIGHT_ATTACK.value,
        radar_cross_section=0.6,
        crew=1,
        has_radar=False,
        has_rwr=True,
        description="Agile, lightweight single-engine turboprop COIN and light attack aircraft. Low heat signature.",
        common_weapons=["20mm Gunpod", "IRMS-2", "Rocket Pods", "Light Bombs"],
    ),
    "T/A-30": UnitProfile(
        key="T/A-30",
        display_name="T/A-30 'Compass'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.LIGHT_ATTACK.value,
        radar_cross_section=1.2,
        crew=2,
        has_radar=True,
        has_rwr=True,
        description="Twin turboprop multirole trainer/strike aircraft with high loiter endurance and precision optics.",
        common_weapons=["30mm Autocannon", "AGM-68", "Glide Bombs", "IRMS-2"],
    ),
    "SA-42": UnitProfile(
        key="SA-42",
        display_name="SA-42 'Revoker'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.MULTIROLE.value,
        radar_cross_section=0.8,
        crew=1,
        has_radar=True,
        has_rwr=True,
        description="Single-engine delta-canard light multirole fighter. High agility, Mach 1.6+ capability.",
        common_weapons=["25mm Cannon", "SARH-2", "ARH-1", "AGM-68", "Bombs"],
    ),
    "FS-12": UnitProfile(
        key="FS-12",
        display_name="FS-12 'Ifrit'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.AIR_SUPERIORITY.value,
        radar_cross_section=0.15,
        crew=1,
        has_radar=True,
        has_rwr=True,
        description="Heavy twin-engine stealth air superiority fighter. Internal weapon bays and thrust vectoring.",
        common_weapons=["30mm Rotary", "ARH-1 Scythe", "IRMS-2", "Stealth cruise missiles"],
    ),
    "EW-25": UnitProfile(
        key="EW-25",
        display_name="EW-25 'Medusa'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.ELECTRONIC_WARFARE.value,
        radar_cross_section=1.5,
        crew=2,
        has_radar=True,
        has_rwr=True,
        has_jammer=True,
        description="Dedicated Electronic Attack / SEAD twin-engine jet. Powerful active phased-array jamming pods.",
        common_weapons=["Anti-Radiation Missiles", "Stand-off Jammers", "Decoys"],
    ),
    "Darkreach": UnitProfile(
        key="Darkreach",
        display_name="EB-52 / 'Darkreach'",
        category=UnitCategory.AIRCRAFT,
        role=AirRole.STRATEGIC_BOMBER.value,
        radar_cross_section=0.08,
        crew=2,
        has_radar=True,
        has_rwr=True,
        description="Heavy stealth flying-wing supersonic bomber capable of launching tactical and strategic nuclear weapons.",
        common_weapons=["Heavy Rotary Launcher", "Cruise Missiles", "Hypersonic A2G", "Nuclear Warheads"],
    ),
    "AttackHelo1": UnitProfile(
        key="AttackHelo1",
        display_name="AH-99 'Tarantula'",
        category=UnitCategory.HELICOPTER,
        role=AirRole.ATTACK_HELICOPTER.value,
        radar_cross_section=1.0,
        crew=2,
        has_radar=True,
        has_rwr=True,
        description="Heavy tandem attack helicopter with mast-mounted radar, 30mm turret, and internal anti-tank missile bays.",
        common_weapons=["30mm Turret", "AGM-1", "Hydra Rocket Pods", "IRMS"],
    ),
}

KNOWN_GROUND_UNITS: Dict[str, UnitProfile] = {
    "SPAAG1": UnitProfile(
        key="SPAAG1",
        display_name="Boltstrike SPAAG",
        category=UnitCategory.AIR_DEFENSE,
        role="Short-range Air Defense",
        radar_cross_section=2.0,
        has_radar=True,
        description="Dual 35mm radar-guided anti-aircraft artillery vehicle with integrated search and tracking radar.",
    ),
    "Truck2-LADS": UnitProfile(
        key="Truck2-LADS",
        display_name="LADS SAM Launcher",
        category=UnitCategory.AIR_DEFENSE,
        role="Surface-to-Air Missile",
        has_radar=False,
        description="Low Altitude Air Defense System launching high-agility short-to-medium range SAMs.",
    ),
    "Truck2-FC": UnitProfile(
        key="Truck2-FC",
        display_name="Fire Control Radar Truck",
        category=UnitCategory.AIR_DEFENSE,
        role="Fire Control / Illumination",
        has_radar=True,
        description="High-power fire control radar truck providing illumination for long-range surface-to-air missiles.",
    ),
    "Truck2-TBM": UnitProfile(
        key="Truck2-TBM",
        display_name="Theater Ballistic Missile Truck",
        category=UnitCategory.GROUND_VEHICLE,
        role="Ballistic Strike",
        description="Heavy mobile launcher for tactical and nuclear ballistic missiles.",
    ),
    "radarStation1": UnitProfile(
        key="radarStation1",
        display_name="Early Warning Radar Station",
        category=UnitCategory.STRUCTURE,
        role="Early Warning / Air Search",
        has_radar=True,
        description="Large stationary air search radar with massive 100+ km detection volume.",
    ),
    "CRAMTrailer1": UnitProfile(
        key="CRAMTrailer1",
        display_name="C-RAM Stationary Trailer",
        category=UnitCategory.AIR_DEFENSE,
        role="Point Defense",
        has_radar=True,
        description="Rapid-fire CIWS / C-RAM trailer intercepting incoming missiles and artillery shells.",
    ),
}

KNOWN_NAVAL_UNITS: Dict[str, UnitProfile] = {
    "FleetCarrier1": UnitProfile(
        key="FleetCarrier1",
        display_name="Fleet Supercarrier",
        category=UnitCategory.WARSHIP,
        role="Naval Aviation Capital Ship",
        radar_cross_section=25.0,
        has_radar=True,
        description="Nuclear-powered aircraft carrier with catapults, arrestor gear, extensive CIWS and VLS defense.",
    ),
    "Destroyer1": UnitProfile(
        key="Destroyer1",
        display_name="Guided Missile Destroyer",
        category=UnitCategory.WARSHIP,
        role="Multi-mission Surface Combatant",
        radar_cross_section=12.0,
        has_radar=True,
        description="Advanced warship with phased-array radar, VLS missile cells, and heavy 76mm/127mm naval gun.",
    ),
    "Frigate1": UnitProfile(
        key="Frigate1",
        display_name="Guided Missile Frigate",
        category=UnitCategory.WARSHIP,
        role="Escort / Air Defense",
        radar_cross_section=8.0,
        has_radar=True,
        description="General-purpose escort warship with point defense and anti-ship missile batteries.",
    ),
}


def lookup_unit(unit_key: str) -> Optional[UnitProfile]:
    """Look up a unit profile by exact key or substring."""
    key_clean = unit_key.split("_")[0]  # strip instance numbering like SPAAG1_1
    for table in (KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS):
        if unit_key in table:
            return table[unit_key]
        if key_clean in table:
            return table[key_clean]
        for k, v in table.items():
            if k.lower() in unit_key.lower():
                return v
    return None
