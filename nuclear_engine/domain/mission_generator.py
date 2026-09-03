"""Programmatic Mission Generator & Scenario Factory for Nuclear Option."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from nuclear_engine.config import config
from nuclear_engine.domain.mission import (
    Mission,
    MissionSettings,
    Faction,
    Objective,
    UnitInstance,
    Vector3,
    Quaternion,
    SavedLoadout,
    WeaponSlot,
)


class MissionFactory:
    """Generates valid, game-ready Nuclear Option mission.json files."""

    @staticmethod
    def create_mission(
        name: str,
        preset: str = "dogfight",
        player_faction: str = "Boscali",
        enemy_faction: str = "Primeva",
        time_of_day: float = 14.0,
    ) -> Mission:
        settings = MissionSettings(
            description=f"Generated {preset.upper()} scenario for {player_faction}.",
            playerMode="Singleplayer",
            allowRespawn=True,
            playerStartingRank=2,
            nuclearEscalationThreshold=0.0,
            strategicEscalationThreshold=0.0,
        )

        factions = [
            Faction(factionName=player_faction, startingBalance=50000.0, reserveAirframes=10),
            Faction(factionName=enemy_faction, startingBalance=50000.0, reserveAirframes=10),
        ]

        # Standard Airbases from Terrain_naval
        airbases: List[Dict[str, Any]] = [
            {
                "UniqueName": "Central Airbase",
                "DisplayName": "Feldspar International",
                "faction": player_faction,
                "Center": {"x": 2206.0, "y": 8.0, "z": 4153.0},
                "CaptureRange": 2600.0,
            },
            {
                "UniqueName": "Enemy Forward Base",
                "DisplayName": "Broken Atoll",
                "faction": enemy_faction,
                "Center": {"x": -74591.8, "y": 12.5, "z": -28639.3},
                "CaptureRange": 2600.0,
            },
        ]

        aircraft: List[UnitInstance] = []
        vehicles: List[UnitInstance] = []
        ships: List[UnitInstance] = []
        buildings: List[UnitInstance] = []
        objectives: List[Objective] = []

        if preset == "dogfight":
            # Player Aircraft
            player_ac = UnitInstance(
                UniqueName="Alpha-1 (Player)",
                type="Aircraft_Revoker",
                faction=player_faction,
                playerControlled=True,
                playerControlledPriority=1,
                skill=1.0,
                bravery=1.0,
                fuel=1.0,
                globalPosition=Vector3(x=2206.0, y=3500.0, z=6000.0),
                rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                savedLoadout=SavedLoadout(Selected=[WeaponSlot(Key="AAM_Short"), WeaponSlot(Key="AAM_Medium")]),
            )
            aircraft.append(player_ac)

            # 2 Enemy Fighters
            enemy_1 = UnitInstance(
                UniqueName="Bandit-1",
                type="Aircraft_Revoker",
                faction=enemy_faction,
                playerControlled=False,
                skill=0.8,
                bravery=0.7,
                fuel=1.0,
                globalPosition=Vector3(x=2206.0, y=3800.0, z=18000.0),
                rotation=Quaternion(x=0.0, y=1.0, z=0.0, w=0.0),  # Facing south
                savedLoadout=SavedLoadout(Selected=[WeaponSlot(Key="AAM_Short"), WeaponSlot(Key="AAM_Medium")]),
            )
            enemy_2 = UnitInstance(
                UniqueName="Bandit-2",
                type="Aircraft_Ifrit",
                faction=enemy_faction,
                playerControlled=False,
                skill=0.75,
                bravery=0.6,
                fuel=1.0,
                globalPosition=Vector3(x=3500.0, y=3700.0, z=18500.0),
                rotation=Quaternion(x=0.0, y=1.0, z=0.0, w=0.0),
                savedLoadout=SavedLoadout(Selected=[WeaponSlot(Key="AAM_Short")]),
            )
            aircraft.extend([enemy_1, enemy_2])

            objectives.append(Objective(
                UniqueName="Obj_AirSuperiority",
                DisplayName="Achieve Air Superiority",
                Faction=player_faction,
                Type="DestroyUnits",
                targetUnits=["Bandit-1", "Bandit-2"],
            ))

        elif preset == "strike":
            # Player Strike Aircraft
            player_ac = UnitInstance(
                UniqueName="Hammer-1 (Player)",
                type="Aircraft_Ifrit",
                faction=player_faction,
                playerControlled=True,
                playerControlledPriority=1,
                skill=1.0,
                bravery=1.0,
                fuel=1.0,
                globalPosition=Vector3(x=2206.0, y=2000.0, z=4153.0),
                rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                savedLoadout=SavedLoadout(Selected=[WeaponSlot(Key="AGM_Heavy"), WeaponSlot(Key="AAM_Short")]),
            )
            aircraft.append(player_ac)

            # Target Radar & SAM site
            radar = UnitInstance(
                UniqueName="Target_EarlyWarningRadar",
                type="Building_RadarStation",
                faction=enemy_faction,
                globalPosition=Vector3(x=15000.0, y=45.0, z=12000.0),
            )
            sam = UnitInstance(
                UniqueName="Target_BoltfaceSAM",
                type="Vehicle_BoltfaceSAM",
                faction=enemy_faction,
                globalPosition=Vector3(x=15200.0, y=45.0, z=12100.0),
            )
            buildings.append(radar)
            vehicles.append(sam)

            objectives.append(Objective(
                UniqueName="Obj_StrikeRadar",
                DisplayName="Destroy Early Warning Radar Installation",
                Faction=player_faction,
                Type="DestroyUnits",
                targetUnits=["Target_EarlyWarningRadar"],
            ))

        else:  # naval_patrol
            player_ac = UnitInstance(
                UniqueName="Valkyrie-1 (Player)",
                type="Aircraft_Medusa",
                faction=player_faction,
                playerControlled=True,
                playerControlledPriority=1,
                skill=1.0,
                fuel=1.0,
                globalPosition=Vector3(x=2206.0, y=1500.0, z=4153.0),
                rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
            )
            aircraft.append(player_ac)

            warship = UnitInstance(
                UniqueName="Hostile_MissileCorvette",
                type="Ship_Corvette",
                faction=enemy_faction,
                globalPosition=Vector3(x=25000.0, y=0.0, z=20000.0),
            )
            ships.append(warship)

            objectives.append(Objective(
                UniqueName="Obj_SinkCorvette",
                DisplayName="Interdict and Neutralize Hostile Warship",
                Faction=player_faction,
                Type="DestroyUnits",
                targetUnits=["Hostile_MissileCorvette"],
            ))

        return Mission(
            JsonVersion=1,
            MapKey={"Type": "GameWorldPrefab", "Path": "Terrain_naval"},
            missionSettings=settings,
            environment={
                "timeOfDay": time_of_day,
                "timeFactor": 0.0,
                "weatherIntensity": 0.0,
                "cloudAltitude": 2000.0,
                "windSpeed": 2.0,
                "windHeading": 90.0,
            },
            factions=factions,
            airbases=airbases,
            aircraft=aircraft,
            vehicles=vehicles,
            ships=ships,
            buildings=buildings,
            objectives=objectives,
        )

    @classmethod
    def save_to_mission_editor(
        cls,
        mission_name: str,
        preset: str = "dogfight",
        player_faction: str = "Boscali",
        enemy_faction: str = "Primeva",
        target_dir: Optional[Path] = None,
    ) -> Path:
        """Create and write scenario directly to Nuclear Option's MissionEditor directory or custom path."""
        mission = cls.create_mission(
            name=mission_name,
            preset=preset,
            player_faction=player_faction,
            enemy_faction=enemy_faction,
        )

        out_dir = target_dir or (config.mission_editor_dir / mission_name)
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "mission.json"

        data = mission.model_dump()
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return file_path

