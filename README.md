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

## 🚀 Quickstart mit `uv`

Das gesamte Projekt ist für Astral **`uv`** optimiert. Du benötigst keine manuelle `venv`-Aktivierung – führe einfach alles direkt mit `uv run no` aus!

```bash
# Projekt initialisieren / synchronisieren
uv sync
```

---

## ⚡ Token-Saving Modding & API Commands (`uv run no ...`)

Dieses Tool wurde speziell dafür gebaut, um beim Entwickeln von Nuclear Option Mods **zehntausende LLM-Tokens zu sparen**: Anstatt riesige 3000-Zeilen-Dateien zu durchsuchen, liefert die CLI präzise, kompakte Snippets und fertige BepInEx-Hooks:

```bash
# 1. Saubere C#-Klassen-API anzeigen (Basisklasse, Interfaces, Felder, Methoden mit Parametern & Zeilennummer)
uv run no api Aircraft
uv run no api Radar

# 2. NUR die exakte Methoden-Implementierung ansehen (nur 10-20 Zeilen Code statt 3.000 Zeilen!)
uv run no method Aircraft LockedByMissile
uv run no method Radar WarningFlash

# 3. Fertigen BepInEx Harmony-Patch für eine Methode generieren (Copy & Paste)
uv run no hook Aircraft LockedByMissile
uv run no hook Radar EstimateDetection --patch-type Postfix

# 4. Ähnliche APIs über alle Klassen des Spiels suchen und bündeln
uv run no sim "Radar"
uv run no sim "Missile"
uv run no sim "Fire"

# 5. Schnelle Volltextsuche & Klassen-Suche im Spielcode
uv run no find "Airfoil"
uv run no find "Jammer"

# 6. Missions-Editor Szenarien analysieren
uv run no missions
uv run no analyze "Boscali HQ"

# 7. Spiel-Lexikon & Mechaniken
uv run no units
uv run no weapons
uv run no doppler 300 90
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
