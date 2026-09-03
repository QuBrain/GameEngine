"""Tactical 2D Mission Map Renderer for Nuclear Option scenarios."""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from nuclear_engine.domain.mission import Mission, UnitInstance


@dataclass
class MapPoint:
    name: str
    category: str  # "aircraft", "vehicle", "ship", "building", "airbase"
    faction: str
    x: float
    z: float


class TacticalMapRenderer:
    def __init__(self, mission: Mission):
        self.mission = mission
        self.points: List[MapPoint] = self._extract_points()

    def _extract_points(self) -> List[MapPoint]:
        pts: List[MapPoint] = []

        def add_units(units: List[UnitInstance], cat: str):
            for u in units:
                if u.globalPosition:
                    pts.append(MapPoint(
                        name=u.UniqueName,
                        category=cat,
                        faction=u.faction or "Neutral",
                        x=u.globalPosition.x,
                        z=u.globalPosition.z,
                    ))

        add_units(self.mission.aircraft, "aircraft")
        add_units(self.mission.vehicles, "vehicle")
        add_units(self.mission.ships, "ship")
        add_units(self.mission.buildings, "building")

        for b in self.mission.airbases:
            pos = b.get("position") or b.get("globalPosition")
            if isinstance(pos, dict):
                x = pos.get("x", 0.0)
                z = pos.get("z", 0.0)
                name = b.get("name") or b.get("DisplayName", "Airbase")
                faction = b.get("faction", "Neutral")
                pts.append(MapPoint(name=name, category="airbase", faction=faction, x=float(x), z=float(z)))

        return pts

    def get_bounds(self) -> Tuple[float, float, float, float]:
        if not self.points:
            return -10000.0, 10000.0, -10000.0, 10000.0
        xs = [p.x for p in self.points]
        zs = [p.z for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        # Margin
        pad_x = max(2000.0, (max_x - min_x) * 0.1)
        pad_z = max(2000.0, (max_z - min_z) * 0.1)
        return min_x - pad_x, max_x + pad_x, min_z - pad_z, max_z + pad_z

    def render_ascii(self, width: int = 60, height: int = 24) -> str:
        """Render a terminal ASCII tactical map."""
        if not self.points:
            return "[No units with global coordinates in mission]"

        min_x, max_x, min_z, max_z = self.get_bounds()
        span_x = max(1.0, max_x - min_x)
        span_z = max(1.0, max_z - min_z)

        # 2D Grid initialized to empty terrain '.'
        grid = [["." for _ in range(width)] for _ in range(height)]


        for p in self.points:
            # Map x -> col [0, width - 1], z -> row [height - 1 down to 0 (North is up)]
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
        legend = f"Grid: {width_km:.1f} km x {height_km:.1f} km | Legend: [A]ircraft [V]ehicle [S]hip [B]ase [+]Structure"
        lines.append(legend)

        return "\n".join(lines)

    def render_svg(self, width: int = 800, height: int = 600) -> str:
        """Generate a vector SVG tactical map."""
        min_x, max_x, min_z, max_z = self.get_bounds()
        span_x = max(1.0, max_x - min_x)
        span_z = max(1.0, max_z - min_z)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color:#0d1117;">',
            f'<rect width="{width}" height="{height}" fill="#0d1117"/>',
            # Grid lines
            '<g stroke="#21262d" stroke-width="1">',
        ]

        for i in range(1, 8):
            x = (width / 8) * i
            svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke-dasharray="4"/>')
        for j in range(1, 6):
            y = (height / 6) * j
            svg_parts.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke-dasharray="4"/>')
        svg_parts.append('</g>')

        # Units
        factions = list(set(p.faction for p in self.points))
        colors = ["#58a6ff", "#f85149", "#3fb950", "#d2a8ff", "#e3b341"]
        faction_color = {f: colors[i % len(colors)] for i, f in enumerate(factions)}

        for p in self.points:
            cx = (p.x - min_x) / span_x * (width - 40) + 20
            cy = (max_z - p.z) / span_z * (height - 40) + 20
            c = faction_color.get(p.faction, "#8b949e")

            if p.category == "airbase":
                svg_parts.append(f'<rect x="{cx-6}" y="{cy-6}" width="12" height="12" fill="none" stroke="{c}" stroke-width="2"/>')
            elif p.category == "aircraft":
                svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{c}"/>')
            elif p.category == "ship":
                svg_parts.append(f'<polygon points="{cx},{cy-5} {cx+4},{cy+5} {cx-4},{cy+5}" fill="{c}"/>')
            else:
                svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="{c}"/>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)
