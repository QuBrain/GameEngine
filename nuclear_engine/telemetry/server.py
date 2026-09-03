"""Async WebSocket and UDP telemetry receiver server for Nuclear Option."""

import asyncio
import json
import logging
import socket
from typing import Callable, List, Optional
import websockets

from nuclear_engine.telemetry.state import TelemetryState, RadarContact, RWRWarning

logger = logging.getLogger("nuclear_engine.telemetry")


class TelemetryServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, udp_port: int = 8766):
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.current_state = TelemetryState()
        self._subscribers: List[Callable[[TelemetryState], None]] = []
        self._server = None

    def add_subscriber(self, callback: Callable[[TelemetryState], None]):
        self._subscribers.append(callback)

    def _update_state(self, data: dict):
        self.current_state.connected = True
        self.current_state.vehicle_name = data.get("vehicle", self.current_state.vehicle_name)
        self.current_state.altitude_asl_m = data.get("alt_asl", self.current_state.altitude_asl_m)
        self.current_state.altitude_agl_m = data.get("alt_agl", self.current_state.altitude_agl_m)
        self.current_state.speed_airspeed_mps = data.get("speed_mps", self.current_state.speed_airspeed_mps)
        self.current_state.speed_mach = data.get("mach", self.current_state.speed_mach)
        self.current_state.heading_deg = data.get("heading", self.current_state.heading_deg)
        self.current_state.g_force = data.get("g", self.current_state.g_force)

        # Parse coordinates
        pos = data.get("pos")
        if isinstance(pos, dict):
            self.current_state.position_x = pos.get("x", 0.0)
            self.current_state.position_y = pos.get("y", 0.0)
            self.current_state.position_z = pos.get("z", 0.0)

        # Parse contacts
        contacts = []
        for c in data.get("contacts", []):
            contacts.append(
                RadarContact(
                    id=c.get("id", ""),
                    display_name=c.get("name", "Unknown"),
                    distance_m=c.get("dist", 0.0),
                    bearing_deg=c.get("bearing", 0.0),
                    altitude_m=c.get("alt", 0.0),
                    speed_mps=c.get("speed", 0.0),
                    is_hostile=c.get("hostile", True),
                )
            )
        self.current_state.contacts = contacts

        # Parse RWR
        rwr_threats = []
        for r in data.get("rwr", []):
            rwr_threats.append(
                RWRWarning(
                    source_id=r.get("id", ""),
                    emitter_type=r.get("type", "SEARCH"),
                    bearing_deg=r.get("bearing", 0.0),
                    signal_strength=r.get("strength", 1.0),
                    is_missile_active=r.get("launch", False),
                )
            )
        self.current_state.rwr_threats = rwr_threats

    async def _handle_connection(self, websocket):
        logger.info(f"Telemetry client connected: {websocket.remote_address}")
        self.current_state.connected = True
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self._update_state(data)
                    for sub in self._subscribers:
                        sub(self.current_state)
                except json.JSONDecodeError:
                    continue
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.current_state.connected = False
            logger.info("Telemetry client disconnected.")

    def listen_udp_sync(self, max_packets: Optional[int] = None, timeout: float = 2.0):
        """Synchronous UDP listener for CLI dashboard."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.udp_port))
        sock.settimeout(timeout)

        count = 0
        try:
            while max_packets is None or count < max_packets:
                try:
                    data, _ = sock.recvfrom(4096)
                    msg = json.loads(data.decode("utf-8"))
                    self._update_state(msg)
                    for sub in self._subscribers:
                        sub(self.current_state)
                    count += 1
                except socket.timeout:
                    break
        finally:
            sock.close()

    def render_hud(self) -> str:
        s = self.current_state
        return (
            f"+-------------------- COCKPIT TELEMETRY --------------------+\n"
            f"| ALT ASL: {s.altitude_asl_m:>7.1f} m   ALT AGL: {s.altitude_agl_m:>7.1f} m   HEADING: {s.heading_deg:>5.1f}* |\n"
            f"| SPEED:   M {s.speed_mach:>5.2f}    G-FORCE: {s.g_force:>6.1f} G    CONTACTS: {len(s.contacts):>4} |\n"
            f"| RWR ALERTS: {len(s.rwr_threats):<2}        STATUS: {'CONNECTED' if s.connected else 'DISCONNECTED':<12}             |\n"
            f"+-----------------------------------------------------------+"
        )

    async def start(self):
        self._server = await websockets.serve(self._handle_connection, self.host, self.port)
        logger.info(f"Telemetry server listening on ws://{self.host}:{self.port}")
