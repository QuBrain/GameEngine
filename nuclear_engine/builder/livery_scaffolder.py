"""Aircraft Livery and Custom Skin Modding Scaffolder for Nuclear Option."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json

from nuclear_engine.config import config


@dataclass
class LiveryMetadata:
    vehicle: str
    skin_name: str
    display_name: str
    author: str
    description: str = ""
    faction_locks: List[str] = field(default_factory=list)
    diffuse_texture: str = "albedo.png"
    normal_texture: str = "normal.png"
    metallic_texture: str = "metallic.png"


class LiveryScaffolder:
    """Scaffolds complete custom aircraft skin packages and BepInEx runtime texture loaders."""

    @classmethod
    def scaffold(
        cls,
        vehicle_name: str,
        skin_name: str,
        author: str = "Modder",
        display_name: Optional[str] = None,
        target_dir: Optional[Path] = None,
    ) -> Path:
        vehicle = vehicle_name.capitalize()
        clean_skin = skin_name.replace(" ", "_")
        root_dir = target_dir or (config.workspace_root / "skins" / vehicle / clean_skin)
        root_dir.mkdir(parents=True, exist_ok=True)

        meta = LiveryMetadata(
            vehicle=vehicle,
            skin_name=clean_skin,
            display_name=display_name or f"{vehicle} - {skin_name}",
            author=author,
            description=f"Custom tactical livery for the {vehicle}.",
            faction_locks=["Boscali", "Primeva"],
            diffuse_texture="albedo.png",
            normal_texture="normal.png",
            metallic_texture="metallic.png",
        )

        # 1. Write livery.json
        json_path = root_dir / "livery.json"
        json_path.write_text(json.dumps(meta.__dict__, indent=2), encoding="utf-8")

        # 2. Write placeholder textures and UV guide
        cls._create_placeholder_texture(root_dir / "albedo.png")
        cls._create_placeholder_texture(root_dir / "normal.png")
        cls._create_placeholder_texture(root_dir / "metallic.png")

        readme_path = root_dir / "README.md"
        readme_path.write_text(f"""# Custom Livery: {meta.display_name}

Vehicle: {vehicle}
Author: {author}

## Texture Guidelines
- `albedo.png`: Base diffuse color map (PNG format, 2048x2048 or 4096x4096 recommended).
- `normal.png`: Tangent-space normal map.
- `metallic.png`: Metallic (R), Occlusion (G), Smoothness (A) map.

Deploy this folder to your Nuclear Option BepInEx plugins directory alongside the generated LiveryLoader.
""", encoding="utf-8")

        # 3. Generate BepInEx C# LiveryLoader script
        loader_path = root_dir / f"{clean_skin}Loader.cs"
        loader_path.write_text(cls._generate_csharp_loader(meta), encoding="utf-8")

        return root_dir

    @staticmethod
    def _create_placeholder_texture(path: Path):
        """Generate a minimal valid 1x1 PNG file if texture doesn't exist."""
        if path.exists():
            return
        # Minimal valid 1x1 PNG binary payload
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x60, 0x60, 0x60, 0x60,
            0x00, 0x00, 0x00, 0x05, 0x00, 0x01, 0xA7, 0x34,
            0x33, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
            0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        path.write_bytes(png_bytes)

    @staticmethod
    def _generate_csharp_loader(meta: LiveryMetadata) -> str:
        return f"""using System;
using System.IO;
using BepInEx;
using HarmonyLib;
using UnityEngine;

namespace NuclearOption.CustomLiveries
{{
    [BepInPlugin("com.nuclearoption.livery.{meta.skin_name.lower()}", "{meta.display_name}", "1.0.0")]
    public class {meta.skin_name}Loader : BaseUnityPlugin
    {{
        private static Texture2D _albedoTex;
        private static string _skinDir;

        private void Awake()
        {{
            _skinDir = Path.Combine(Paths.PluginPath, "{meta.vehicle}", "{meta.skin_name}");
            LoadTextures();

            var harmony = new Harmony("com.nuclearoption.livery.{meta.skin_name.lower()}");
            harmony.PatchAll();
            Logger.LogInfo("Custom Livery '{meta.display_name}' loaded successfully.");
        }}

        private void LoadTextures()
        {{
            string albedoPath = Path.Combine(_skinDir, "{meta.diffuse_texture}");
            if (File.Exists(albedoPath))
            {{
                byte[] data = File.ReadAllBytes(albedoPath);
                _albedoTex = new Texture2D(2, 2);
                _albedoTex.LoadImage(data);
            }}
        }}

        [HarmonyPatch(typeof(Aircraft), nameof(Aircraft.Start))]
        public static class Patch_Aircraft_ApplyLivery
        {{
            [HarmonyPostfix]
            public static void Postfix(Aircraft __instance)
            {{
                if (__instance == null || _albedoTex == null)
                    return;

                if (__instance.name.IndexOf("{meta.vehicle}", StringComparison.OrdinalIgnoreCase) >= 0)
                {{
                    foreach (var renderer in __instance.GetComponentsInChildren<MeshRenderer>())
                    {{
                        foreach (var mat in renderer.materials)
                        {{
                            if (mat.shader.name.Contains("Standard") || mat.shader.name.Contains("Vehicle"))
                            {{
                                mat.mainTexture = _albedoTex;
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
"""
