# Discord Post: Nuclear Option Modding SDK

This file contains two versions for posting on Discord:
1. **Thread / Forum Version** (Detailed, for Discord Forums or dedicated channels).
2. **Single-Message Version** (Under 2,000 characters, for standard Discord text channels).

Neither version contains emojis, buzzwords, or em-dashes.

---

## Option 1: Forum / Thread Post (Detailed)

```markdown
**Nuclear Option Modding SDK**

I have built an open source modding toolkit and code intelligence system for Nuclear Option. It streamlines reverse engineering, BepInEx plugin scaffolding, and build pipelines with full IDE autocomplete support.

Repository: https://github.com/Username/NuclearOption-SDK

**Core Features**

1. **Reverse Engineering and API Intelligence**
- Decompiles and indexes all game assemblies (`Assembly-CSharp.dll`, `Mirage.dll`, `Rewired_Core.dll`) across 1,200+ classes.
- Fast CLI search for classes, methods, parameters, and callers.
- Generates publicized assemblies and XML hover documentation for IDE IntelliSense.

2. **Scaffolding and Build Pipeline**
- Generates clean BepInEx 5 mod projects with 5-line `.csproj` files.
- Builds with native `dotnet build` or internal Roslyn compiler in under 1 second without NuGet errors.
- Hot-reload file watcher (`no watch <ModName>`) that detects file saves and automatically rebuilds, verifies patches, and deploys DLLs to Steam plugins in under 600 ms.
- Thunderstore mod packager (`no pack <ModName>`) generating `manifest.json`, clean 256x256 icon, and distribution zip archives.

3. **Patch Verification and Logging**
- Static Harmony patch verifier (`no verify-patches <ModName>`) checking `[HarmonyPatch]` target classes, method signatures, and parameter types against current game binaries before launch.
- Unified log viewer (`no logs`) with filtering for Unity engine (`Player.log`) and BepInEx output.

4. **Multiplayer and Aircraft Intelligence**
- Mirage network inspector (`no rpc Aircraft`) listing all 179 `ServerRpc`, `ClientRpc`, and `SyncVar` endpoints with parameter types.
- Aircraft and hardpoint inspector (`no vehicle revoker`) displaying flight specs, radar cross sections, and weapon station limits.

5. **Tactical Operations and Scenarios**
- Interactive 2D tactical map (`no mission-map "Defend" --web`) rendering real archipelago coordinates, capture zones, and SAM threat envelopes.
- Programmatic scenario generator (`no new-mission "Skirmish" --preset dogfight`) creating ready-to-play `mission.json` files.

6. **Documentation and MCP**
- Offline searchable HTML API documentation (`no docs`) covering all decompiled classes.
- Model Context Protocol (MCP) server (`no mcp`) exposing 15 tools for IDE and AI-assisted workflows.

**Quick Start**
Requirements: Windows, Python 3.12+, .NET SDK 8.0/9.0, uv.

```bash
git clone https://github.com/Username/NuclearOption-SDK.git
cd NuclearOption-SDK
uv sync
uv run no decompile
uv run no publicize
uv run no sync-ide
uv run no new-mod CombatTracker
uv run no build CombatTracker
```
```

---

## Option 2: Compact Single-Message Version (<2,000 Characters)

```markdown
**Nuclear Option Modding SDK**

An open-source toolkit and code intelligence system for Nuclear Option modding:
https://github.com/Username/NuclearOption-SDK

**What It Provides:**
- **Decompiler & Code Indexer:** Indexes 1,200+ classes across `Assembly-CSharp`, `Mirage` multiplayer, and `Rewired`.
- **IDE IntelliSense:** Generates publicized assemblies and XML docstrings for autocomplete in VS Code and Antigravity IDE.
- **Mod Scaffolding & Build:** Builds BepInEx 5 mods via native `dotnet build` in under 1 second without NuGet issues.
- **Hot-Reload Watcher (`no watch`):** Automatically rebuilds, verifies patches, and deploys DLLs to Steam on file save in under 600 ms.
- **Patch Verifier (`no verify-patches`):** Statically checks `[HarmonyPatch]` attributes against game binaries before launch.
- **Multiplayer RPC Inspector (`no rpc`):** Lists 179 `ServerRpc`, `ClientRpc`, and `SyncVar` endpoints with signatures.
- **Vehicle & Hardpoint Inspector (`no vehicle`):** Displays flight performance, radar cross sections, and weapon stations.
- **Tactical Map (`no mission-map --web`):** Interactive browser radar map with airbase capture radii and SAM threat domes.
- **Scenario Factory (`no new-mission`):** Programmatically generates playable `mission.json` scenarios.
- **Offline API Docs (`no docs`):** Standalone searchable HTML documentation for all game classes.
- **Thunderstore Packer (`no pack`):** Packages mods with manifest, clean icon, and zip archive.
- **MCP Server (`no mcp`):** Native Model Context Protocol server exposing 15 tools for IDE and AI-assisted workflows.

**Setup:**
```bash
git clone https://github.com/Username/NuclearOption-SDK.git
cd NuclearOption-SDK
uv sync
uv run no decompile && uv run no publicize && uv run no sync-ide
uv run no new-mod CombatTracker
```
```
