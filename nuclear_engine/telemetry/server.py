"""Async WebSocket and JSON telemetry receiver server."""

import asyncio
import json
import logging
from typing import Callable, List, Optional
import websockets

from nuclear_engine.telemetry.state import TelemetryState, RadarContact, RWRWarning

logger = logging.getLogger("nuclear_engine.telemetry")


class TelemetryServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.current_state = TelemetryState()
        self._subscribers: List[Callable[[TelemetryState], None]] = []
        self._server = None

    def add_subscriber(self, callback: Callable[[TelemetryState], None]):
        self._subscribers.append(callback)

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

    def _update_state(self, data: dict):
        self.current_state.vehicle_name = data.get("vehicle", self.current_state.vehicle_name)
        self.current_state.altitude_asl_m = data.get("alt_asl", self.current_state.altitude_asl_m)
        self.current_state.altitude_agl_m = data.get("alt_agl", self.current_state.altitude_agl_m)
        self.current_state.speed_airspeed_mps = data.get("speed_mps", self.current_state.speed_airspeed_mps)
        self.current_state.speed_mach = data.get("mach", self.current_state.speed_mach)
        self.current_state.heading_deg = data.get("heading", self.current_state.heading_deg)
        self.current_state.g_force = data.get("g", self.current_state.g_force)

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

    async def start(self):
        self._server = await websockets.serve(self._handle_connection, self.host, self.port)
        logger.info(f"Telemetry server listening on ws://{self.host}:{self.port}")
