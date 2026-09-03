# Nuclear Option Modding SDK

If you are developing BepInEx mods or custom missions for Nuclear Option, this SDK provides an automated development environment with IDE autocomplete for game code, hot-reload compilation, patch validation, and inspection tools.

Repository: https://github.com/Username/NuclearOption-SDK

## What You Can Do With It

- **Write C# mods with full IDE IntelliSense:** Automatically decompiles and publicizes Assembly-CSharp, Mirage (multiplayer), and Rewired (input). VS Code and Rider will autocomplete internal game classes (Aircraft, CombatHUD, RadarWarning, Missile) with hover docstrings.
- **Instant compilation and hot-reload:** Native dotnet build runs in under 1 second. The file watcher (`no watch <ModName>`) detects file saves and automatically rebuilds, validates patches, and deploys the DLL to your Steam plugins folder in under 600 ms.
- **Verify Harmony patches before launching:** Static patch verification (`no verify-patches <ModName>`) checks your `[HarmonyPatch]` target classes, method names, and parameter types against current game binaries to catch typos and signature mismatches before runtime.
- **Inspect multiplayer network endpoints:** The RPC inspector (`no rpc Aircraft`) lists all 179 Mirage ServerRpc, ClientRpc, and SyncVar endpoints with parameter types so you know how the game synchronizes state.
- **Inspect flight models and hardpoints:** Look up aircraft specs (`no vehicle revoker`) including empty weight, top speed, radar cross section, countermeasures, and all weapon stations with weight limits and compatible ordnance.
- **Render tactical mission maps:** Generate an interactive 2D browser radar map (`no mission-map "Defend" --web`) with real archipelago coordinates, airbase capture radii, and SAM threat envelopes.
- **Generate mission scenarios from code:** Programmatically create playable `mission.json` scenarios (`no new-mission "Skirmish" --preset dogfight`) ready to open in the in-game editor.
- **Search game APIs offline:** Generates a standalone searchable HTML documentation portal (`no docs`) for all 1,200+ decompiled classes.
- **Package for Thunderstore:** One-command packaging (`no pack <ModName>`) that compiles in Release mode, creates manifest.json and a 256x256 icon, and outputs a ready-to-upload zip archive.

## Quick Start

Requirements: Windows, Python 3.12+, .NET SDK 8.0 or 9.0, uv package manager.

```bash
# Clone and initialize
git clone https://github.com/Username/NuclearOption-SDK.git
cd NuclearOption-SDK
uv sync

# Index game assemblies and configure IDE autocomplete
uv run no decompile
uv run no publicize
uv run no sync-ide

# Scaffold a new mod project
uv run no new-mod MyMod

# Watch and auto-deploy while coding
uv run no watch MyMod
```
