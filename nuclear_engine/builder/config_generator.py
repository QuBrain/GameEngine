"""Generates typed BepInEx configuration boilerplate for Nuclear Option mods."""

from pathlib import Path
from nuclear_engine.config import config


def generate_config_file(mod_name: str) -> Path:
    """Creates a ModConfig.cs file inside plugins/<ModName>/."""
    mod_dir = config.workspace_root / "plugins" / mod_name
    if not mod_dir.exists():
        raise FileNotFoundError(f"Mod '{mod_name}' not found in {config.workspace_root / 'plugins'}")

    target_file = mod_dir / "ModConfig.cs"

    content = f"""using BepInEx.Configuration;
using UnityEngine;

namespace {mod_name}
{{
    public static class ModConfig
    {{
        // 1. General Settings
        public static ConfigEntry<bool> Enabled {{ get; private set; }}

        // 2. Hotkeys
        public static ConfigEntry<KeyCode> ToggleKey {{ get; private set; }}

        // 3. Gameplay / Multipliers
        public static ConfigEntry<float> Multiplier {{ get; private set; }}

        public static void Initialize(ConfigFile config)
        {{
            Enabled = config.Bind(
                "General",
                "Enabled",
                true,
                "Master switch to enable or disable {mod_name}."
            );

            ToggleKey = config.Bind(
                "Controls",
                "ToggleKey",
                KeyCode.F8,
                "Keyboard shortcut to toggle mod functions in flight."
            );

            Multiplier = config.Bind(
                "Tweaks",
                "Multiplier",
                1.0f,
                new ConfigDescription("Custom modifier value (0.1 to 5.0)", new AcceptableValueRange<float>(0.1f, 5.0f))
            );
        }}
    }}
}}
"""
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    return target_file
