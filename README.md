# NuclearEngine ⚡

> An intelligent tactical analysis, game data exploration, mission engine, and telemetry system for **[Nuclear Option](https://store.steampowered.com/app/2158680/Nuclear_Option/)**.

---

## 🎯 Features

- **Mission Intelligence & Parsing:** Automatically discovers and parses mission files (`mission.json`) from the Nuclear Option Mission Editor (`%LOCALAPPDATA%Low/Shockfront/NuclearOption`).
- **Tactical Advisor & Combat Math:** Analyzes force structures, air defense envelopes, radar line-of-sight horizons, and Doppler notch gates.
- **Game Engine & Code Decompilation:** Automated decompiler pipeline for `Assembly-CSharp.dll` with instant search for flight models, weapons, and game systems.
- **Domain Encyclopedia:** Rich database of aircraft (Cricket, Compass, Revoker, Ifrit, Medusa, Darkreach, Tarantula), weapons, radars, and counter-tactics.
- **Live Telemetry Bridge:** WebSocket and UDP server ready to receive real-time flight data from in-game BepInEx plugins.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (Astral `uv` recommended)
- .NET 8 / 9 (optional, for ILSpy decompilation)
- Nuclear Option installed via Steam

### Installation
```bash
# Setup environment & dependencies
uv venv --python 3.12
.venv\Scripts\activate
uv pip install -e .
```

### CLI Commands

```bash
# Check system status and game path detection
nuclear-engine status

# List all missions in your editor directory
nuclear-engine missions

# Run a deep tactical balance analysis on a mission
nuclear-engine analyze "Boscali HQ"
nuclear-engine analyze "Defend"

# Browse unit encyclopedia
nuclear-engine units
nuclear-engine units --category "AirDefense"

# Browse weapon encyclopedia and counter-tactics
nuclear-engine weapons

# Decompile Assembly-CSharp.dll (takes ~30s)
nuclear-engine decompile

# Search decompiled game code
nuclear-engine code "Radar"
nuclear-engine code "Missile"

# Calculate Doppler Notch radar evasion
nuclear-engine doppler 250 90
```

---

## 📂 Project Structure

```
GameEngine/
├── nuclear_engine/               # Core Python System
│   ├── config.py                 # Auto-detection of Steam & AppData paths
│   ├── domain/                   # Pydantic schemas (Mission, Units, Weapons)
│   ├── extractor/                # Mission scanner & ILSpy C# decompiler
│   ├── tactical_advisor/         # Combat math & force balance analyzer
│   ├── telemetry/                # Live WebSocket server & telemetry models
│   └── cli.py                    # Rich-powered Terminal UI
├── plugins/                      # BepInEx C# Mods
│   └── NuclearTelemetry/         # In-game telemetry exporter
└── tests/                        # Pytest suite
```
