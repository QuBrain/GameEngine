"""Data structures representing real-time player telemetry and tactical environment."""

from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class RadarContact:
    id: str
    display_name: str
    distance_m: float
    bearing_deg: float
    altitude_m: float
    speed_mps: float
    is_hostile: bool
    is_locked: bool = False


@dataclass
class RWRWarning:
    source_id: str
    emitter_type: str  # e.g., 'SEARCH', 'TRACK', 'MISSILE_LAUNCH'
    bearing_deg: float
    signal_strength: float
    is_missile_active: bool = False


@dataclass
class TelemetryState:
    timestamp: float = field(default_factory=time.time)
    connected: bool = False
    vehicle_name: str = "Unknown"
    altitude_asl_m: float = 0.0
    altitude_agl_m: float = 0.0
    speed_airspeed_mps: float = 0.0
    speed_mach: float = 0.0
    g_force: float = 1.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    heading_deg: float = 0.0
    fuel_remaining_percent: float = 100.0
    master_arm: bool = False
    flare_count: int = 0
    chaff_count: int = 0
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    contacts: List[RadarContact] = field(default_factory=list)
    rwr_threats: List[RWRWarning] = field(default_factory=list)


    @property
    def has_incoming_missile(self) -> bool:
        return any(t.is_missile_active for t in self.rwr_threats)
