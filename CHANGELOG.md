# Changelog

All notable changes to the Nuclear Option Modding SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-09-04

### Added
- **NOMM Compatibility:** Upgraded `no pack` to produce dual-compatible packages supporting Nuclear Option Mod Manager (NOMM), the NOMNOM manifest registry (`nomnom.json`), and Thunderstore (`manifest.json`, `icon.png`, `BepInEx/plugins/<ModName>/` directory structure).
- **Mission Validator and Scenario Linter (`no validate-mission`):** Statically checks `mission.json` files for undeclared faction assignments, underwater or subterranean spawns, missing objective target IDs, and invalid airbase coordinates.
- **Harmony CIL OpCode Inspector (`no il`):** Disassembles game methods to raw CIL bytecode instructions with offsets and operands. Includes `--matcher` flag to generate ready-to-use Harmony `CodeMatcher` boilerplate for transpiler development.
- **Aircraft Livery and Texture Scaffolder (`no new-livery`):** Automates custom aircraft skin package generation (`skins/<Vehicle>/<SkinName>/`) including `livery.json` metadata, texture placement guides, and a C# BepInEx runtime loader plugin.
- **Performance and Anti-Stutter Code Auditor (`no audit`):** Statically scans mod C# source code for simulation frame-drop hazards, including `FindObjectsOfType` in `Update()`, un-cached `GetComponent` calls, per-frame LINQ heap allocations, and blocking synchronous file or network I/O.
- **IDE F12 Decompilation Navigation:** Enabled `omnisharp.enableDecompilationSupport` in `.vscode/settings.json`, allowing developers to press F12 on any game type or method (`Aircraft`, `CombatHUD`, `LockedByMissile`) to decompile and browse the original C# source code directly inside the IDE without needing dnSpy.
- **Automated Harmony Patch Generator (`no patch`):** Scaffolds 100% typed, compilable Harmony patch classes (`Prefix`, `Postfix`, `Transpiler` with `CodeMatcher`) directly from real in-game signatures.
- **Rich In-Editor XML Docstrings:** Expanded `Assembly-CSharp.xml` with detailed summaries for 35+ core game systems, fields, and events for instant hover explanations.
- **VS Code C# Modding Snippets:** Added `.vscode/csharp.code-snippets` with instant shortcuts (`hprefix`, `hpostfix`, `htranspiler`, `bepmod`, `nolog`, `coroutine`).
- **Model Context Protocol (MCP) Expansion:** Added native `generate_harmony_patch` tool, bringing the total MCP tool count to 20.
- **Automated Test Suite Expansion:** Added comprehensive test coverage in `tests/test_patch_generator.py`, bringing the test suite to 52 passing unit tests.

### Fixed
- **OmniSharp Path Configuration:** Corrected `omnisharp.dotnetPath` in `.vscode/settings.json` and global IDE configuration to point to the .NET installation folder instead of executable name, eliminating `spawn UNKNOWN` errors.
- **Environment PATH Hardening:** Added `.NET` runtime directory (`C:\Program Files\dotnet`) to the user environment PATH variable for seamless child process execution.

---

## [0.2.5] - 2026-09-04

### Added
- **Hot-Reload Mod Watcher (`no watch`):** Monitors mod C# files and executes instantaneous background recompilation, patch validation, and deployment in under 600 ms on file save.
- **Mirage Multiplayer RPC Inspector (`no rpc`):** Indexes 179 network endpoints (`[ServerRpc]`, `[ClientRpc]`, `[TargetRpc]`, `[SyncVar]`) across game assemblies with parameter types and authority requirements.
- **Programmatic Scenario Generator (`no new-mission`):** Programmatically constructs complete `mission.json` scenarios with airbases, aircraft spawns, weapon loadouts, and objectives.
- **Audio and Voice Alert Catalog (`no audio`):** Discovers 54 sound hooks, SoundManager triggers, audio mixer assignments, and cockpit voice warning hooks.
- **Live Flight Telemetry Receiver (`no telemetry`):** Connects to the `NuclearTelemetry` UDP broadcast on port 8766 and renders an ASCII cockpit HUD.
- **Interactive 2D Tactical War Room Map (`no mission-map --web`):** Generates interactive HTML5 radar maps aligned with the true 160 km archipelago coordinate system and airbase capture zones.
- **IDE Intelligence and Docstrings (`no sync-ide`):** Generates master solution `plugins/NuclearMods.sln` and XML documentation for 1,200+ publicized game classes.
