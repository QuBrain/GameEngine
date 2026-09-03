using BepInEx.Configuration;
using UnityEngine;

namespace NuclearTelemetry
{
    public static class ModConfig
    {
        // 1. General Settings
        public static ConfigEntry<bool> Enabled { get; private set; }

        // 2. Hotkeys
        public static ConfigEntry<KeyCode> ToggleKey { get; private set; }

        // 3. Gameplay / Multipliers
        public static ConfigEntry<float> Multiplier { get; private set; }

        public static void Initialize(ConfigFile config)
        {
            Enabled = config.Bind(
                "General",
                "Enabled",
                true,
                "Master switch to enable or disable NuclearTelemetry."
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
        }
    }
}
