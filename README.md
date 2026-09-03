# Nuclear Option Modding SDK

[![Target Game](https://img.shields.io/badge/Game-Nuclear%20Option-red?style=flat-square)](https://store.steampowered.com/app/2158680/Nuclear_Option/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-Astral-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)
[![.NET SDK](https://img.shields.io/badge/.NET-8.0%20%7C%209.0-512BD4?style=flat-square&logo=dotnet&logoColor=white)](https://dotnet.microsoft.com/)
[![Mod Framework](https://img.shields.io/badge/Mod%20Loader-BepInEx%205-F49342?style=flat-square)](https://github.com/BepInEx/BepInEx)
[![Protocol](https://img.shields.io/badge/Protocol-MCP%20Server-007ACC?style=flat-square)](https://modelcontextprotocol.io/)

[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Test Suite](https://img.shields.io/badge/Tests-33%20passed-2ea44f?style=flat-square)](https://docs.pytest.org/)


NuclearEngine is a development toolkit and code intelligence system for the combat flight simulator [Nuclear Option](https://store.steampowered.com/app/2158680/Nuclear_Option/). It provides reverse engineering tools, a token-efficient code indexer, automated BepInEx mod scaffolding, compilation and deployment pipelines, and a Model Context Protocol (MCP) server for integration with development environments.

---


## Philosophy: AI-Assisted Modding and Accessibility

Modding a compiled game often presents a steep barrier to entry: developers must navigate hundreds of decompiled C# source files, understand undocumented internal engine lifecycles, and master Harmony bytecode patching conventions. For beginners, this steep learning curve can easily lead to frustration; for experienced programmers, searching through thousands of lines of decompiled assemblies is repetitive and time-consuming.

Artificial intelligence serves as a practical developer tool in this workflow. Using AI as an assistive coding partner is not a shortcut that replaces programming skill, but an effective way to accelerate reverse engineering, locate relevant game APIs, and clarify obscure internal logic. This toolkit was intentionally designed to support AI collaboration, providing token-efficient queries and a native Model Context Protocol (MCP) server so that human developers and AI assistants alike can explore Nuclear Option's codebase without exceeding context windows.


Whether you write every line of code by hand, collaborate with an AI assistant, or are building your very first game mod, the objective of this project is to demystify the game's internal systems and make mod development accessible, transparent, and approachable for everyone.

---

## Requirements


- **Operating System:** Windows 10 or 11
- **Python:** 3.12 or newer, managed via [Astral `uv`](https://docs.astral.sh/uv/)
- **.NET SDK:** .NET 8.0 or 9.0 SDK installed (providing Roslyn compiler `csc`)
- **Game:** Nuclear Option installed via Steam

---

## Setup

Synchronize dependencies with `uv`:

```bash
uv sync
```

Decompile the game's core assembly (`Assembly-CSharp.dll`):

```bash
uv run no decompile
```

Generate the publicized reference assembly for full IDE autocomplete:

```bash
uv run no publicize
```

---

## Mod Development and Code Intelligence

The CLI provides targeted query commands to extract specific class members, methods, and call hierarchies without reading complete multi-thousand-line C# files into context.

### Class and Method Queries

```bash
# View class inheritance, interfaces, fields, and method signatures
uv run no api Aircraft
uv run no api Radar

# Extract only the implementation source code of a specific method
uv run no method Aircraft LockedByMissile
uv run no method Radar WarningFlash

# Generate a BepInEx Harmony patch template for a method
uv run no hook Aircraft LockedByMissile
uv run no hook Radar EstimateDetection --patch-type Postfix
```

### Call Hierarchy and Inheritance

```bash
# Locate all call sites and references to a method, field, or event
uv run no callers LockedByMissile

# Display all classes that inherit from a specified base class or interface
uv run no subclasses Unit
uv run no subclasses MonoBehaviour

# List nested structs defined in a class
uv run no structs MissileWarning

# List C# events defined in a class
uv run no events Aircraft

# View enum values by class name or enum name
uv run no enums SeekerMode
uv run no enums UnitState
```

### API Search

```bash
# Search for methods and signatures across all 1,200+ game classes
uv run no sim "Radar"
uv run no sim "Countermeasure"
```

---

## Machine-Readable JSON Output

All code inspection commands support the `--json` (`-j`) flag to output structured JSON data for scripting, editor extensions, and external tooling:

```bash
uv run no api Aircraft --json
uv run no method Aircraft LockedByMissile --json
uv run no hook Aircraft LockedByMissile --json
uv run no callers LockedByMissile --json
uv run no subclasses Unit --json
uv run no enums SeekerMode --json
```

---

## Mod Build and Deployment Pipeline

The SDK includes a build and packaging pipeline tailored for BepInEx 5 plugins:

### 1. Scaffold a New Mod

```bash
uv run no new-mod CombatTracker
```

Creates a project directory under `plugins/CombatTracker/` containing a `.csproj` and boilerplate `Plugin.cs` with an initial Harmony patch.

### 2. Compile the Mod

```bash
uv run no build CombatTracker
```

Compiles the C# plugin using the Roslyn compiler directly against the game's managed assemblies, runtime libraries, BepInEx core, and the publicized `Assembly-CSharp.dll`.

### 3. Deploy to the Game

```bash
uv run no deploy CombatTracker
```

Compiles the mod and copies the resulting DLL directly to the Steam game installation directory:
`<SteamPath>/Nuclear Option/BepInEx/plugins/<ModName>.dll`.

### 4. Verify Harmony Patches

Validate that all `[HarmonyPatch]` attributes in your mod target classes and methods that actually exist in the current game version:

```bash
uv run no verify-patches CombatTracker
uv run no verify-patches CombatTracker --json
```

### 5. Generate Mod Configuration

Add a typed BepInEx configuration boilerplate (`ModConfig.cs`) to your mod:

```bash
uv run no add-config CombatTracker
```

### 6. Package for Thunderstore / Distribution

Package your mod into a distribution zip archive containing `manifest.json`, `icon.png`, `README.md`, and compiled binaries:

```bash
uv run no pack CombatTracker
uv run no pack CombatTracker --json
```

Output is written to `dist/<ModName>_<Version>.zip` ready for upload to Thunderstore or r2modman.

### 7. Launch Game

```bash
uv run no run-game
```

Launches Nuclear Option through Steam protocol.


---

## Log Viewer and Diagnostics

Inspect and stream logs from the game and BepInEx mods with syntax highlighting:

```bash
# View last 50 lines of BepInEx mod logs
uv run no logs

# View last 100 lines of Unity engine logs (Player.log)
uv run no logs --source player -n 100

# Show only warnings and errors
uv run no logs --errors-only

# Stream logs live in real time during flight
uv run no logs --follow

# Output logs in JSON format
uv run no logs -n 25 --json
```

---

## Multi-Assembly Decompilation

In addition to `Assembly-CSharp.dll`, the SDK can decompile and index any managed game assembly (e.g., Mirage multiplayer networking, Rewired input):

```bash
# Decompile Mirage networking stack
uv run no decompile Mirage

# Decompile Rewired input manager
uv run no decompile Rewired_Core
```

Decompiled sources are saved to `no_code_analysis/source/<Assembly>/` and are immediately searchable via `api`, `method`, `sim`, and `callers`.

---

## Assembly Publicizer and IntelliSense

Unity game assemblies enforce `private` and `internal` access restrictions on internal fields and methods. The SDK incorporates an assembly publicizer that rewrites metadata flags to `public`:

```bash
uv run no publicize
```

The output is written to `lib/publicized/Assembly-CSharp.dll`.

---

## IDE Integration and Autocomplete

The SDK provides automatic configuration for Visual Studio, JetBrains Rider, and VS Code (C# Dev Kit and OmniSharp):

```bash
uv run no sync-ide
```

### Components Configured

1. **Master Solution (`plugins/NuclearMods.sln`):** Automatically discovers and links all mod projects in the `plugins/` folder.
2. **Global MSBuild Properties (`plugins/Directory.Build.props`):** Automatically provides references to `Assembly-CSharp.dll` (publicized), `Mirage.dll`, `UnityEngine.dll`, and BepInEx for every mod project without manual XML editing.
3. **C# XML Documentation Tooltips (`lib/publicized/Assembly-CSharp.xml`):** Injects docstrings into the publicized assembly so that hovering over classes and methods (`Aircraft.LockedByMissile`, `Radar.EstimateDetection`, `Missile.Explode`) displays descriptive summaries directly in your editor.
4. **Native `dotnet build` Compatibility:** Mods can be compiled directly through your editor or terminal (`dotnet build`) with zero NuGet restore errors or missing assembly warnings.


---

## Model Context Protocol (MCP) Server

The SDK implements an MCP server over standard I/O (JSON-RPC 2.0), allowing AI-assisted IDEs (Antigravity IDE, Cursor, Claude Desktop, Windsurf) to call code intelligence tools directly:

```bash
uv run no mcp
```

### Registered Tools

- `get_class_api`: Returns class hierarchy, fields, methods, structs, events, and enums.
- `get_method_code`: Extracts method source code and line numbers.
- `generate_harmony_hook`: Generates BepInEx Harmony prefix/postfix patches.
- `find_callers`: Finds references across all source files.
- `find_subclasses`: Finds derived classes for any base type.
- `find_enums`: Queries enum definitions and values.
- `search_code`: Searches methods and signatures matching a keyword.
- `analyze_mission`: Evaluates tactical threats and force balance in a mission scenario.

Workspace configuration is located in `.agents/mcp_config.json`.

---

## Interactive Terminal Interface

An interactive terminal interface provides keyboard-driven query capabilities:

```bash
uv run no tui
```

Enter a search term (e.g., `Aircraft`, `Radar`, `LockedByMissile`, `subclasses Unit`). Press `Enter` to display the matching API overview, source code, Harmony hook, or callers. Press `Esc` or type `clear` to return to the search view. Press `q` to exit.

---

## Mission and Tactical Analysis

The domain module parses Nuclear Option scenario files (`mission.json`) from the Mission Editor directory:

```bash
# Discover local user missions
uv run no missions

# Run tactical analysis on a specific mission
uv run no analyze "MissionName"

# Inspect unit database (aircraft, air defenses, warships)
uv run no units
uv run no units --category aircraft

# Inspect missile guidance envelopes and countermeasure profiles
uv run no weapons

# Compute pulse-Doppler radar notch gate status
uv run no doppler 250 85
```

---

## Airframe and Hardpoint Intelligence

Inspect vehicle performance, radar cross sections (RCS), countermeasure reserves, and weapon station layouts:

```bash
# List all indexed vehicles and flight metrics
uv run no vehicles

# Inspect Revoker fighter specifications and hardpoint stations
uv run no vehicle revoker

# Inspect stealth bomber hardpoints and loadout compatibility in JSON format
uv run no vehicle darkreach --json
```

---

## Offline API Documentation

Generate a standalone, client-side searchable HTML and JSON documentation portal for all 1,200+ decompiled game classes:

```bash
uv run no docs
```

The documentation is written to `docs/api/index.html` and can be opened in any web browser completely offline.

---

## Tactical Mission Map

Render a 2D radar plot of airbases, factories, SAM batteries, and naval units from mission scenarios:

```bash
# Render terminal ASCII radar map
uv run no mission-map "Boscali HQ"

# Export vector SVG tactical map
uv run no mission-map "Boscali HQ" --svg
```

---

## Directory Structure


```
GameEngine/
├── .agents/
│   └── mcp_config.json        # MCP server configuration for IDE integration
├── .vscode/
│   ├── tasks.json             # Build, deploy, and launch tasks
│   └── launch.json            # Unity debugger attachment configuration
├── lib/
│   └── publicized/            # Publicized game assemblies for IDE autocomplete
├── no_code_analysis/          # Decompiled C# sources and decompiler cache
├── nuclear_engine/
│   ├── builder/               # Mod build and deployment pipeline
│   ├── domain/                # Data models for missions, units, weapons
│   ├── extractor/             # Code indexer, decompiler, publicizer
│   ├── tactical_advisor/      # Combat math and mission analysis
│   ├── telemetry/             # Network models for flight telemetry
│   ├── cli.py                 # Command-line interface entry point
│   ├── config.py              # Path resolution (Steam, AppData, Managed)
│   ├── mcp_server.py          # Native Model Context Protocol server
│   └── tui.py                 # Interactive terminal search interface
├── plugins/                   # Source directories for C# BepInEx mods
│   └── NuclearTelemetry/      # Telemetry export plugin
└── tests/                     # Automated test suite
```

---

## Testing

Run the automated test suite with `pytest`:

```bash
uv run pytest
```
