"""Tactical 2D Mission Map & Operations Center Renderer for Nuclear Option scenarios."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from nuclear_engine.domain.mission import Mission, UnitInstance


# Known major geographical island centers in Nuclear Option's Archipelago (Terrain_naval)
TERRAIN_SECTORS = [
    {"name": "Feldspar Central Island", "x": 2200, "z": 4150, "radius": 15000},
    {"name": "Ashwood Island & Strait", "x": 68000, "z": -28000, "radius": 18000},
    {"name": "Broken Atoll Outpost", "x": -74500, "z": -28600, "radius": 12000},
    {"name": "Bifurca Archipelago", "x": -37900, "z": 11200, "radius": 14000},
    {"name": "Cliffline Ridge", "x": 69600, "z": 26000, "radius": 14000},
    {"name": "Hogshead Peninsula", "x": -13400, "z": 30500, "radius": 12000},
    {"name": "Harmony Sands Coast", "x": -75800, "z": 33600, "radius": 11000},
    {"name": "Opal Island Basin", "x": 42100, "z": -200, "radius": 10000},
]


@dataclass
class MapPoint:
    name: str
    category: str  # "aircraft", "vehicle", "ship", "building", "airbase", "sam"
    unit_type: str
    faction: str
    x: float
    z: float
    altitude: float = 0.0
    heading: float = 0.0
    radius: float = 0.0
    threat_range: float = 0.0


class TacticalMapRenderer:
    def __init__(self, mission: Mission):
        self.mission = mission
        self.points: List[MapPoint] = self._extract_points()

    def _extract_points(self) -> List[MapPoint]:
        pts: List[MapPoint] = []

        def get_threat_range(unit_type: str) -> float:
            ut = unit_type.lower()
            if "stratolance" in ut or "long_range_sam" in ut:
                return 45000.0  # 45 km SAM envelope
            elif "boltface" in ut or "sam" in ut:
                return 18000.0  # 18 km SAM envelope
            elif "scythe" in ut or "spaag" in ut or "ciws" in ut:
                return 4000.0   # 4 km AAA envelope
            return 0.0

        def add_units(units: List[UnitInstance], cat: str):
            for u in units:
                if u.globalPosition:
                    threat = get_threat_range(u.type)
                    effective_cat = "sam" if threat > 0 and cat in ("vehicle", "building") else cat
                    pts.append(MapPoint(
                        name=u.UniqueName,
                        category=effective_cat,
                        unit_type=u.type or cat.capitalize(),
                        faction=u.faction or "Neutral",
                        x=u.globalPosition.x,
                        z=u.globalPosition.z,
                        altitude=u.globalPosition.y,
                        threat_range=threat,
                    ))

        add_units(self.mission.aircraft, "aircraft")
        add_units(self.mission.vehicles, "vehicle")
        add_units(self.mission.ships, "ship")
        add_units(self.mission.buildings, "building")

        for b in self.mission.airbases:
            center = b.get("Center") or b.get("position") or b.get("globalPosition") or b.get("SelectionPosition")
            if isinstance(center, dict):
                x = float(center.get("x", 0.0))
                z = float(center.get("z", 0.0))
                name = b.get("DisplayName") or b.get("UniqueName") or "Airbase"
                faction = b.get("faction", "Neutral")
                radius = float(b.get("CaptureRange", 2500.0))
                pts.append(MapPoint(
                    name=name,
                    category="airbase",
                    unit_type="Airbase / Airfield",
                    faction=faction,
                    x=x,
                    z=z,
                    radius=radius,
                ))

        return pts

    def get_bounds(self) -> Tuple[float, float, float, float]:
        if not self.points:
            return -85000.0, 85000.0, -40000.0, 40000.0
        xs = [p.x for p in self.points]
        zs = [p.z for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        # Margin
        pad_x = max(5000.0, (max_x - min_x) * 0.12)
        pad_z = max(5000.0, (max_z - min_z) * 0.12)
        return min_x - pad_x, max_x + pad_x, min_z - pad_z, max_z + pad_z

    def render_ascii(self, width: int = 60, height: int = 24) -> str:
        """Render a terminal ASCII tactical map with coordinates and legend."""
        if not self.points:
            return "[No units with global coordinates in mission]"

        min_x, max_x, min_z, max_z = self.get_bounds()
        span_x = max(1.0, max_x - min_x)
        span_z = max(1.0, max_z - min_z)

        # 2D Grid initialized to empty ocean '.'
        grid = [["." for _ in range(width)] for _ in range(height)]

        for p in self.points:
            col = int((p.x - min_x) / span_x * (width - 1))
            row = int((max_z - p.z) / span_z * (height - 1))
            col = max(0, min(width - 1, col))
            row = max(0, min(height - 1, row))

            if p.category == "airbase":
                ch = "B"
            elif p.category == "aircraft":
                ch = "A"
            elif p.category == "ship":
                ch = "S"
            elif p.category == "sam":
                ch = "!"
            elif p.category == "vehicle":
                ch = "V"
            else:
                ch = "+"

            grid[row][col] = ch

        border = "+" + "-" * width + "+"
        lines = [border]
        for row in grid:
            lines.append("|" + "".join(row) + "|")
        lines.append(border)

        width_km = span_x / 1000.0
        height_km = span_z / 1000.0
        legend = f"Grid: {width_km:.1f} km x {height_km:.1f} km | Legend: [B]ase [A]ircraft [V]ehicle [S]hip [!]SAM/AirDefense [+]Structure"
        lines.append(legend)

        return "\n".join(lines)

    def render_svg(self, width: int = 1000, height: int = 750) -> str:
        """Generate a vector SVG tactical map."""
        min_x, max_x, min_z, max_z = self.get_bounds()
        span_x = max(1.0, max_x - min_x)
        span_z = max(1.0, max_z - min_z)

        def to_screen(x: float, z: float) -> Tuple[float, float]:
            sx = (x - min_x) / span_x * (width - 60) + 30
            sy = (max_z - z) / span_z * (height - 60) + 30
            return sx, sy

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color:#0b0f19; font-family:monospace;">',
            f'<rect width="{width}" height="{height}" fill="#0b0f19"/>',
            '<g stroke="#1e293b" stroke-width="1">',
        ]

        # Tactical Coordinate Grid
        for i in range(1, 10):
            x = (width / 10) * i
            svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke-dasharray="3,3"/>')
        for j in range(1, 8):
            y = (height / 8) * j
            svg_parts.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke-dasharray="3,3"/>')
        svg_parts.append('</g>')

        # Archipelago Sector Regions
        svg_parts.append('<g fill="#162032" stroke="#334155" stroke-width="1.5" opacity="0.6">')
        for s in TERRAIN_SECTORS:
            if min_x <= s["x"] <= max_x and min_z <= s["z"] <= max_z:
                sx, sy = to_screen(s["x"], s["z"])
                sr = (s["radius"] / span_x) * (width - 60)
                svg_parts.append(f'<circle cx="{sx}" cy="{sy}" r="{max(15, sr)}"/>')
                svg_parts.append(f'<text x="{sx}" y="{sy+sr+14}" fill="#64748b" font-size="10" text-anchor="middle">{s["name"]}</text>')
        svg_parts.append('</g>')

        # Threat Cones (SAM Coverage)
        svg_parts.append('<g fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,4" opacity="0.4">')
        for p in self.points:
            if p.threat_range > 0:
                sx, sy = to_screen(p.x, p.z)
                tr_px = (p.threat_range / span_x) * (width - 60)
                svg_parts.append(f'<circle cx="{sx}" cy="{sy}" r="{tr_px}" fill="#ef4444" fill-opacity="0.08"/>')
        svg_parts.append('</g>')

        # Factions color palette
        faction_colors = {
            "boscali": "#38bdf8",   # Allied Cyan/Blue
            "primeva": "#f87171",   # Opfor Red
            "neutral": "#94a3b8",   # Neutral Grey
        }

        # Airbase Capture Radii & Runways
        for p in self.points:
            if p.category == "airbase":
                sx, sy = to_screen(p.x, p.z)
                col = faction_colors.get(p.faction.lower(), "#38bdf8")
                r_px = max(10.0, (p.radius / span_x) * (width - 60))
                svg_parts.append(f'<circle cx="{sx}" cy="{sy}" r="{r_px}" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-width="2"/>')
                svg_parts.append(f'<rect x="{sx-8}" y="{sy-8}" width="16" height="16" fill="{col}" fill-opacity="0.8"/>')
                svg_parts.append(f'<text x="{sx}" y="{sy-12}" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">{p.name}</text>')

        # Combat Units & Structures
        for p in self.points:
            if p.category == "airbase":
                continue
            sx, sy = to_screen(p.x, p.z)
            col = faction_colors.get(p.faction.lower(), "#e2e8f0")

            if p.category == "aircraft":
                svg_parts.append(f'<polygon points="{sx},{sy-6} {sx+5},{sy+5} {sx},{sy+2} {sx-5},{sy+5}" fill="{col}"/>')
            elif p.category == "ship":
                svg_parts.append(f'<polygon points="{sx},{sy-7} {sx+4},{sy+6} {sx-4},{sy+6}" fill="{col}"/>')
            elif p.category == "sam":
                svg_parts.append(f'<rect x="{sx-4}" y="{sy-4}" width="8" height="8" fill="#f87171"/>')
            elif p.category == "vehicle":
                svg_parts.append(f'<rect x="{sx-3}" y="{sy-3}" width="6" height="6" fill="{col}"/>')
            else:
                svg_parts.append(f'<circle cx="{sx}" cy="{sy}" r="3" fill="{col}"/>')

        # Map Title & Scale Legend
        svg_parts.append(f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">{self.mission.missionSettings.description or "Tactical Operations Map"}</text>')
        svg_parts.append(f'<text x="24" y="50" fill="#64748b" font-size="11">Scale: {span_x/1000:.1f} km x {span_z/1000:.1f} km | Total Units: {len(self.points)}</text>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_interactive_html(self, mission_name: str) -> str:
        """Generate an interactive HTML5 / SVG Tactical War Room with pan, zoom, and live unit inspection."""
        svg_content = self.render_svg(width=1200, height=900)
        points_json = json.dumps([
            {
                "name": p.name,
                "category": p.category,
                "unit_type": p.unit_type,
                "faction": p.faction,
                "x": round(p.x, 1),
                "z": round(p.z, 1),
                "altitude": round(p.altitude, 1),
                "threat_range": p.threat_range,
            }
            for p in self.points
        ])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tactical Map - {mission_name}</title>
    <style>
        :root {{
            --bg: #070a12;
            --panel-bg: #0f172a;
            --border: #1e293b;
            --accent: #38bdf8;
            --text: #f8fafc;
            --text-dim: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            background: var(--bg);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        #viewport {{
            flex: 1;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #map-container {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
        }}
        #map-container:active {{ cursor: grabbing; }}
        #map-container svg {{
            max-width: 100%;
            max-height: 100%;
            filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.1));
        }}
        #sidebar {{
            width: 360px;
            background: var(--panel-bg);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 24px;
            overflow-y: auto;
        }}
        h2 {{ font-size: 20px; color: var(--accent); margin-bottom: 8px; }}
        .meta {{ font-size: 12px; color: var(--text-dim); margin-bottom: 24px; }}
        .section-header {{ font-size: 13px; text-transform: uppercase; color: var(--accent); letter-spacing: 1px; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
        .stat-card {{ background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border); border-radius: 6px; padding: 12px; margin-bottom: 12px; }}
        .stat-val {{ font-size: 18px; font-weight: bold; color: #fff; }}
        .stat-lbl {{ font-size: 11px; color: var(--text-dim); margin-top: 2px; }}
        #unit-detail {{
            margin-top: 20px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--accent);
            border-radius: 6px;
            padding: 16px;
            display: none;
        }}
        .controls {{ display: flex; gap: 8px; margin-top: 16px; }}
        .btn {{ flex: 1; padding: 8px; background: #1e293b; color: #fff; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; font-size: 12px; text-align: center; }}
        .btn:hover {{ background: #334155; }}
    </style>
</head>
<body>
    <div id="viewport">
        <div id="map-container">
            {svg_content}
        </div>
    </div>
    <div id="sidebar">
        <h2>{mission_name}</h2>
        <div class="meta">Nuclear Option Tactical Operations Center</div>

        <div class="section-header">Force Strength</div>
        <div class="stat-card">
            <div class="stat-val">{len(self.points)} Total Contacts</div>
            <div class="stat-lbl">Airbases, Aircraft, Warships & Armor</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">{len([p for p in self.points if p.category == 'airbase'])} Airfields</div>
            <div class="stat-lbl">Controllable Strategic Hubs</div>
        </div>

        <div class="section-header" style="margin-top: 16px;">Selected Contact</div>
        <div id="unit-detail">
            <div id="unit-name" style="font-weight: bold; color: var(--accent); font-size: 15px;"></div>
            <div id="unit-type" style="color: var(--text-dim); font-size: 12px; margin: 4px 0 12px 0;"></div>
            <div id="unit-coords" style="font-family: monospace; font-size: 12px;"></div>
        </div>

        <div class="controls">
            <button class="btn" onclick="window.print()">Export / Print</button>
            <button class="btn" onclick="location.reload()">Reset View</button>
        </div>
    </div>

    <script>
        const POINTS = {points_json};
        // Interactive tooltips & hover highlights
        document.querySelectorAll('circle, polygon, rect').forEach((el, idx) => {{
            el.style.cursor = 'pointer';
            el.addEventListener('click', () => {{
                const p = POINTS[idx % POINTS.length];
                if (!p) return;
                const detail = document.getElementById('unit-detail');
                detail.style.display = 'block';
                document.getElementById('unit-name').textContent = p.name;
                document.getElementById('unit-type').textContent = `${{p.faction}} • ${{p.unit_type}} (${{p.category.toUpperCase()}})`;
                document.getElementById('unit-coords').textContent = `GPS: X: ${{p.x}}m | Z: ${{p.z}}m | Alt: ${{p.altitude}}m`;
            }});
        }});
    </script>
</body>
</html>
"""
