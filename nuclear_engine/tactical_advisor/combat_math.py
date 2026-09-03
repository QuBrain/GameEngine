"""Combat mathematics: Radar horizon, Doppler notch angle, and missile kinematics."""

import math
from typing import Tuple


def calculate_radar_horizon_km(radar_alt_m: float, target_alt_m: float) -> float:
    """
    Calculates optical/radar line-of-sight horizon distance in kilometers taking
    into account the standard 4/3 atmospheric refraction model for radio waves.
    Formula: d ≈ 4.12 * (sqrt(h1) + sqrt(h2))
    """
    h1 = max(0.0, radar_alt_m)
    h2 = max(0.0, target_alt_m)
    return 4.12 * (math.sqrt(h1) + math.sqrt(h2))


def calculate_doppler_closure_speed(
    target_speed_mps: float,
    aspect_angle_deg: float,
    radar_speed_mps: float = 0.0,
) -> float:
    """
    Calculates radial closure rate towards the radar emitter.
    Aspect angle: 0° = direct head-on, 90° = pure beam / notch, 180° = running away.
    """
    aspect_rad = math.radians(aspect_angle_deg)
    # radial speed of target towards radar
    radial_target = target_speed_mps * math.cos(aspect_rad)
    return radar_speed_mps + radial_target


def is_in_doppler_notch(
    target_speed_mps: float,
    aspect_angle_deg: float,
    notch_gate_mps: float = 25.0,
) -> Tuple[bool, str]:
    """
    Determines if the target aircraft is within the Doppler notch gate
    (typically ±25 m/s radial velocity against ground clutter).
    """
    aspect_rad = math.radians(aspect_angle_deg)
    radial_vel = abs(target_speed_mps * math.cos(aspect_rad))

    if radial_vel <= notch_gate_mps:
        return (
            True,
            f"Target is within Doppler notch (radial velocity {radial_vel:.1f} m/s <= {notch_gate_mps} m/s threshold). Ground clutter rejection active.",
        )
    return (
        False,
        f"Target is outside Doppler notch (radial velocity {radial_vel:.1f} m/s). Radar has firm lock.",
    )


def estimate_missile_intercept_time_s(
    distance_km: float, missile_mach: float, target_speed_mach: float = 0.8
) -> float:
    """Rough estimation of missile time-to-impact assuming average sound speed 340 m/s."""
    speed_mps = missile_mach * 340.0
    dist_m = distance_km * 1000.0
    return dist_m / max(100.0, speed_mps)
