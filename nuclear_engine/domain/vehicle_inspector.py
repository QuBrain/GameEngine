"""Nuclear Option vehicle, airframe, and hardpoint station inspector."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HardpointStation:
    station_index: int
    name: str
    location: str  # "Wingtip Left", "Underwing Left", "Internal Bay", "Fuselage Centerline", etc.
    max_weight_kg: int
    compatible_weapons: List[str]


@dataclass
class VehicleProfile:
    name: str
    designation: str
    role: str
    faction: str
    crew: int
    empty_weight_kg: int
    max_takeoff_weight_kg: int
    top_speed_mach: float
    service_ceiling_m: int
    rcs_m2: float
    radar_type: str
    countermeasures: Dict[str, int]
    hardpoints: List[HardpointStation] = field(default_factory=list)


VEHICLE_DATABASE: Dict[str, VehicleProfile] = {
    "cricket": VehicleProfile(
        name="Cricket",
        designation="CI-22",
        role="Light Attack / Forward Air Control (COIN)",
        faction="All Factions",
        crew=1,
        empty_weight_kg=1850,
        max_takeoff_weight_kg=3400,
        top_speed_mach=0.45,
        service_ceiling_m=7500,
        rcs_m2=1.8,
        radar_type="None (Visual / Optical pod)",
        countermeasures={"flares": 30, "chaff": 30},
        hardpoints=[
            HardpointStation(1, "Left Pylon Outer", "Wing Left", 250, ["IR-Missile (L-90)", "Light Rocket Pod", "Gun Pod 20mm"]),
            HardpointStation(2, "Right Pylon Outer", "Wing Right", 250, ["IR-Missile (L-90)", "Light Rocket Pod", "Gun Pod 20mm"]),
            HardpointStation(3, "Centerline Pod", "Fuselage", 400, ["Recon Pod", "Targeting Pod", "Fuel Tank"]),
        ],
    ),
    "compass": VehicleProfile(
        name="Compass",
        designation="T/A-30",
        role="Light Strike Fighter / Lead-In Trainer",
        faction="All Factions",
        crew=2,
        empty_weight_kg=4200,
        max_takeoff_weight_kg=8500,
        top_speed_mach=0.88,
        service_ceiling_m=12000,
        rcs_m2=2.5,
        radar_type="Pulse-Doppler Mech-Scan",
        countermeasures={"flares": 60, "chaff": 60},
        hardpoints=[
            HardpointStation(1, "Left Wingtip", "Wingtip Left", 150, ["IR-Missile (L-90)"]),
            HardpointStation(2, "Left Underwing", "Wing Left Inner", 650, ["SARH-Missile", "AGM-65 Heavy", "GBU-12", "Rocket Pod"]),
            HardpointStation(3, "Right Underwing", "Wing Right Inner", 650, ["SARH-Missile", "AGM-65 Heavy", "GBU-12", "Rocket Pod"]),
            HardpointStation(4, "Right Wingtip", "Wingtip Right", 150, ["IR-Missile (L-90)"]),
            HardpointStation(5, "Centerline Pylon", "Fuselage Center", 800, ["Drop Tank", "Cluster Munition", "Heavy Bomb"]),
        ],
    ),
    "revoker": VehicleProfile(
        name="Revoker",
        designation="FS-12",
        role="Air Superiority Fighter",
        faction="Boscali / Independent",
        crew=1,
        empty_weight_kg=7800,
        max_takeoff_weight_kg=16500,
        top_speed_mach=1.95,
        service_ceiling_m=16500,
        rcs_m2=1.2,
        radar_type="AESA Multi-Target TWS",
        countermeasures={"flares": 90, "chaff": 90},
        hardpoints=[
            HardpointStation(1, "Left Wingtip", "Wingtip Left", 160, ["IR-Missile (L-90)", "Agile-AAM"]),
            HardpointStation(2, "Left Mid-Wing", "Wing Left Mid", 500, ["SARH-Missile (S-80)", "ARH-Missile", "AGM-48"]),
            HardpointStation(3, "Left Inboard", "Wing Left Inboard", 900, ["Heavy ARH-Missile", "Anti-Radiation Missile", "Fuel Tank"]),
            HardpointStation(4, "Right Inboard", "Wing Right Inboard", 900, ["Heavy ARH-Missile", "Anti-Radiation Missile", "Fuel Tank"]),
            HardpointStation(5, "Right Mid-Wing", "Wing Right Mid", 500, ["SARH-Missile (S-80)", "ARH-Missile", "AGM-48"]),
            HardpointStation(6, "Right Wingtip", "Wingtip Right", 160, ["IR-Missile (L-90)", "Agile-AAM"]),
        ],
    ),
    "ifrit": VehicleProfile(
        name="Ifrit",
        designation="FS-3",
        role="Multi-Role Strike Fighter",
        faction="Primeva",
        crew=1,
        empty_weight_kg=9200,
        max_takeoff_weight_kg=19000,
        top_speed_mach=1.85,
        service_ceiling_m=15000,
        rcs_m2=2.1,
        radar_type="Multi-Mode Pulse Doppler",
        countermeasures={"flares": 120, "chaff": 120},
        hardpoints=[
            HardpointStation(1, "Left Wing Outer", "Wing Left Outer", 250, ["IR-Missile (L-90)"]),
            HardpointStation(2, "Left Wing Mid", "Wing Left Mid", 600, ["ARH-Missile", "AGM Cruise", "Laser Bomb"]),
            HardpointStation(3, "Left Wing Inner", "Wing Left Inner", 1200, ["Heavy Anti-Ship Missile", "Glide Bomb", "Fuel Tank"]),
            HardpointStation(4, "Fuselage Center", "Centerline", 1500, ["Heavy Strike Munition", "Tactical Nuclear Device", "Fuel Pod"]),
            HardpointStation(5, "Right Wing Inner", "Wing Right Inner", 1200, ["Heavy Anti-Ship Missile", "Glide Bomb", "Fuel Tank"]),
            HardpointStation(6, "Right Wing Mid", "Wing Right Mid", 600, ["ARH-Missile", "AGM Cruise", "Laser Bomb"]),
            HardpointStation(7, "Right Wing Outer", "Wing Right Outer", 250, ["IR-Missile (L-90)"]),
        ],
    ),
    "medusa": VehicleProfile(
        name="Medusa",
        designation="EW-25",
        role="Electronic Attack & SEAD",
        faction="All Factions",
        crew=2,
        empty_weight_kg=8600,
        max_takeoff_weight_kg=17500,
        top_speed_mach=1.1,
        service_ceiling_m=14000,
        rcs_m2=3.0,
        radar_type="Wideband Passive RWR / Barrage Jammer",
        countermeasures={"flares": 180, "chaff": 240, "towed_decoys": 4},
        hardpoints=[
            HardpointStation(1, "Left Wing Outer", "Wing Left", 400, ["High-Band Jamming Pod", "Anti-Radiation Missile"]),
            HardpointStation(2, "Left Wing Inner", "Wing Left", 900, ["Long-Range Anti-Radiation Missile", "Fuel Tank"]),
            HardpointStation(3, "Centerline", "Fuselage", 1200, ["Low-Band Core Jammer", "Multi-Sensor Pod"]),
            HardpointStation(4, "Right Wing Inner", "Wing Right", 900, ["Long-Range Anti-Radiation Missile", "Fuel Tank"]),
            HardpointStation(5, "Right Wing Outer", "Wing Right", 400, ["High-Band Jamming Pod", "Anti-Radiation Missile"]),
        ],
    ),
    "darkreach": VehicleProfile(
        name="Darkreach",
        designation="SFB-81",
        role="Strategic Stealth Strike Bomber",
        faction="All Factions",
        crew=2,
        empty_weight_kg=22000,
        max_takeoff_weight_kg=48000,
        top_speed_mach=0.92,
        service_ceiling_m=16000,
        rcs_m2=0.08,
        radar_type="Low-Probability-of-Intercept (LPI) AESA",
        countermeasures={"flares": 120, "chaff": 180, "radar_absorbent_coating": 1},
        hardpoints=[
            HardpointStation(1, "Internal Rotary Launcher Left", "Internal Bay", 4000, ["Hypersonic Glide Vehicle", "Nuclear Cruise Missile", "Heavy Bunker Buster"]),
            HardpointStation(2, "Internal Rotary Launcher Right", "Internal Bay", 4000, ["Hypersonic Glide Vehicle", "Nuclear Cruise Missile", "Heavy Bunker Buster"]),
            HardpointStation(3, "External Left Pylon (Optional)", "Underwing Left", 2500, ["Long-Range Cruise Missile", "External Fuel Tank"]),
            HardpointStation(4, "External Right Pylon (Optional)", "Underwing Right", 2500, ["Long-Range Cruise Missile", "External Fuel Tank"]),
        ],
    ),
    "chicane": VehicleProfile(
        name="Chicane",
        designation="SAH-46",
        role="Stealth Attack Helicopter",
        faction="All Factions",
        crew=2,
        empty_weight_kg=5100,
        max_takeoff_weight_kg=9800,
        top_speed_mach=0.28,
        service_ceiling_m=5000,
        rcs_m2=0.45,
        radar_type="Mast-Mounted Millimeter Wave Radar (MMW)",
        countermeasures={"flares": 90, "chaff": 90, "dircm": 1},
        hardpoints=[
            HardpointStation(1, "Left Outer Stub", "Stub Wing Left", 200, ["Air-to-Air Missile (Light)", "Rocket Pod"]),
            HardpointStation(2, "Left Inner Stub", "Stub Wing Left", 600, ["Laser-Guided ATGM", "Radar-Guided ATGM"]),
            HardpointStation(3, "Right Inner Stub", "Stub Wing Right", 600, ["Laser-Guided ATGM", "Radar-Guided ATGM"]),
            HardpointStation(4, "Right Outer Stub", "Stub Wing Right", 200, ["Air-to-Air Missile (Light)", "Rocket Pod"]),
        ],
    ),
}


class VehicleInspector:
    @staticmethod
    def get_vehicle(name: str) -> Optional[VehicleProfile]:
        """Look up a vehicle by name or designation (case-insensitive)."""
        q = name.strip().lower()
        if q in VEHICLE_DATABASE:
            return VEHICLE_DATABASE[q]
        for v in VEHICLE_DATABASE.values():
            if q == v.designation.lower() or q in v.name.lower():
                return v
        return None

    @staticmethod
    def list_all() -> List[VehicleProfile]:
        return list(VEHICLE_DATABASE.values())
