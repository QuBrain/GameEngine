"""Test suite for domain models and combat math."""

import pytest
from nuclear_engine.domain.units import lookup_unit, UnitCategory, KNOWN_AIRCRAFT
from nuclear_engine.domain.weapons import lookup_weapon, GuidanceType
from nuclear_engine.tactical_advisor.combat_math import (
    calculate_radar_horizon_km,
    calculate_doppler_closure_speed,
    is_in_doppler_notch,
)


def test_unit_lookup():
    revoker = lookup_unit("SA-42")
    assert revoker is not None
    assert revoker.display_name == "SA-42 'Revoker'"
    assert revoker.category == UnitCategory.AIRCRAFT

    boltstrike = lookup_unit("SPAAG1")
    assert boltstrike is not None
    assert boltstrike.category == UnitCategory.AIR_DEFENSE

    helo = lookup_unit("AttackHelo1")
    assert helo is not None
    assert helo.category == UnitCategory.HELICOPTER


def test_weapon_lookup():
    irms = lookup_weapon("IRMS1")
    assert irms is not None
    assert irms.guidance == GuidanceType.INFRARED
    assert "Flares" in irms.countermeasures

    arh = lookup_weapon("ARH1")
    assert arh is not None
    assert arh.guidance == GuidanceType.ARH


def test_radar_horizon():
    # Radar at 100m alt, target at 100m alt
    horizon = calculate_radar_horizon_km(100.0, 100.0)
    # 4.12 * (10 + 10) = 82.4 km
    assert pytest.approx(horizon, 0.1) == 82.4


def test_doppler_notch():
    # 90 degrees beam aspect -> radial velocity is 0
    in_notch, msg = is_in_doppler_notch(target_speed_mps=300.0, aspect_angle_deg=90.0)
    assert in_notch is True

    # 0 degrees head on -> radial velocity is 300 m/s >> 25 m/s threshold
    in_notch, msg = is_in_doppler_notch(target_speed_mps=300.0, aspect_angle_deg=0.0)
    assert in_notch is False
