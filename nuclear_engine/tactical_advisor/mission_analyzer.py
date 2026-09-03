"""Tactical Mission Analyzer: Computes force balance, air defense coverage, and objective vulnerability."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from nuclear_engine.domain.mission import Mission, UnitInstance
from nuclear_engine.domain.units import lookup_unit, UnitCategory, AirRole


@dataclass
class FactionStrength:
    name: str
    fighter_count: int = 0
    bomber_count: int = 0
    attack_helo_count: int = 0
    air_defense_count: int = 0
    ground_combat_count: int = 0
    warship_count: int = 0
    total_units: int = 0
    air_superiority_score: float = 0.0
    air_defense_score: float = 0.0


@dataclass
class MissionAnalysisReport:
    mission_name: str
    factions: Dict[str, FactionStrength] = field(default_factory=dict)
    key_threats: List[str] = field(default_factory=list)
    tactical_recommendations: List[str] = field(default_factory=list)
    objective_summaries: List[str] = field(default_factory=list)


class MissionAnalyzer:
    def analyze(self, mission: Mission, mission_name: str = "Mission") -> MissionAnalysisReport:
        report = MissionAnalysisReport(mission_name=mission_name)

        # 1. Initialize faction strengths
        for f in mission.factions:
            report.factions[f.factionName] = FactionStrength(name=f.factionName)

        # 2. Categorize all units
        all_units: List[UnitInstance] = (
            mission.aircraft + mission.vehicles + mission.ships + mission.buildings
        )

        for u in all_units:
            faction_name = u.faction or "Neutral"
            if faction_name not in report.factions:
                report.factions[faction_name] = FactionStrength(name=faction_name)

            f_str = report.factions[faction_name]
            f_str.total_units += 1

            profile = lookup_unit(u.type or u.UniqueName)
            if profile:
                if profile.category == UnitCategory.AIRCRAFT:
                    if profile.role == AirRole.AIR_SUPERIORITY.value:
                        f_str.fighter_count += 1
                        f_str.air_superiority_score += 3.0
                    elif profile.role == AirRole.MULTIROLE.value:
                        f_str.fighter_count += 1
                        f_str.air_superiority_score += 2.0
                    elif profile.role == AirRole.STRATEGIC_BOMBER.value:
                        f_str.bomber_count += 1
                    else:
                        f_str.fighter_count += 1
                        f_str.air_superiority_score += 1.0
                elif profile.category == UnitCategory.HELICOPTER:
                    f_str.attack_helo_count += 1
                    f_str.air_superiority_score += 0.5
                elif profile.category == UnitCategory.AIR_DEFENSE:
                    f_str.air_defense_count += 1
                    f_str.air_defense_score += 2.5
                elif profile.category == UnitCategory.WARSHIP:
                    f_str.warship_count += 1
                    f_str.air_defense_score += 3.0
                elif profile.category == UnitCategory.GROUND_VEHICLE:
                    f_str.ground_combat_count += 1

        # 3. Analyze Objectives
        for obj in mission.objectives:
            if obj.Hidden:
                continue
            desc = f"Objective '{obj.DisplayName or obj.UniqueName}' ({obj.Type}) for faction '{obj.Faction}': targets {len(obj.targetUnits)} units."
            report.objective_summaries.append(desc)

        # 4. Generate tactical balance & insights
        faction_list = list(report.factions.keys())
        if len(faction_list) >= 2:
            f1_name, f2_name = faction_list[0], faction_list[1]
            f1, f2 = report.factions[f1_name], report.factions[f2_name]

            # Air superiority comparison
            if f1.air_superiority_score > f2.air_superiority_score * 1.5:
                report.tactical_recommendations.append(
                    f"✈️ Air Dominance: {f1_name} holds significant air combat advantage ({f1.air_superiority_score:.1f} vs {f2.air_superiority_score:.1f})."
                )
            elif f2.air_superiority_score > f1.air_superiority_score * 1.5:
                report.tactical_recommendations.append(
                    f"✈️ Air Dominance: {f2_name} controls the skies ({f2.air_superiority_score:.1f} vs {f1.air_superiority_score:.1f})."
                )
            else:
                report.tactical_recommendations.append(
                    f"⚔️ Contested Airspace: Fighter capability is evenly matched between {f1_name} and {f2_name}."
                )

            # Air defense / SEAD recommendation
            for fname, fstrength in [(f1_name, f1), (f2_name, f2)]:
                if fstrength.air_defense_count > 3 or fstrength.warship_count > 0:
                    report.key_threats.append(
                        f"🛡️ High Threat IADS: {fname} fields {fstrength.air_defense_count} SAM/SPAAG batteries and {fstrength.warship_count} warships. SEAD/DEAD and low-altitude terrain masking required."
                    )

        return report
