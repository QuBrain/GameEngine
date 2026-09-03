"""Native Model Context Protocol (MCP) Server for Nuclear Option Modding SDK.
Allows AI IDEs (Antigravity IDE, Cursor, Claude Desktop, Windsurf) to natively
call reverse-engineering and modding tools via JSON-RPC stdio.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer
from nuclear_engine.extractor.mission_scanner import MissionScanner
from nuclear_engine.tactical_advisor.mission_analyzer import MissionAnalyzer
from nuclear_engine.domain.units import KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS
from nuclear_engine.domain.weapons import KNOWN_WEAPONS


class NuclearMCPServer:
    def __init__(self):
        self.indexer = CodeIndexer()
        self.scanner = MissionScanner()
        self.analyzer = MissionAnalyzer()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_class_api",
                "description": "Inspect clean C# class API (base class, interfaces, fields, methods) from Nuclear Option's 1,216 classes without whole-file token bloat.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string", "description": "The exact C# class name (e.g. 'Aircraft', 'Radar', 'Missile')"}
                    },
                    "required": ["class_name"]
                }
            },
            {
                "name": "get_method_code",
                "description": "Extract the exact implementation source code of a method (5-30 lines) instead of reading a 3,000-line class file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string", "description": "Class containing the method (e.g. 'Aircraft')"},
                        "method_name": {"type": "string", "description": "Name of the method (e.g. 'LockedByMissile', 'TakeDamage')"}
                    },
                    "required": ["class_name", "method_name"]
                }
            },
            {
                "name": "generate_harmony_hook",
                "description": "Generate a ready-to-copy C# BepInEx [HarmonyPatch] snippet with parameters and __instance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string", "description": "Target class"},
                        "method_name": {"type": "string", "description": "Target method"},
                        "patch_type": {"type": "string", "enum": ["Prefix", "Postfix", "Transpiler"], "default": "Prefix"}
                    },
                    "required": ["class_name", "method_name"]
                }
            },
            {
                "name": "find_callers",
                "description": "Find everywhere a method, event, or field is called across all 1,216 game files.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Method, variable, or event name to trace (e.g. 'LockedByMissile')"},
                        "limit": {"type": "integer", "description": "Max results to return", "default": 25}
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "find_subclasses",
                "description": "Find all classes inheriting from a base class or interface (e.g. 'Unit', 'MonoBehaviour').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base_class": {"type": "string", "description": "Base class or interface name"}
                    },
                    "required": ["base_class"]
                }
            },
            {
                "name": "find_enums",
                "description": "Inspect enum values inside a class or search for enum definitions globally (e.g. 'SeekerMode', 'ImpactType').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Class name or enum name to inspect"}
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "search_code",
                "description": "Search for methods or APIs across all game classes matching a keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Keyword to search (e.g. 'Damage', 'Radar', 'Fuel')"},
                        "limit": {"type": "integer", "description": "Max matches", "default": 20}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_mission",
                "description": "Analyze a mission scenario file for tactical threats, air superiority balance, and IADS density.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mission_name": {"type": "string", "description": "Name of mission in MissionEditor or path to mission.json"}
                    },
                    "required": ["mission_name"]
                }
            },
            {
                "name": "verify_mod_patches",
                "description": "Validate that [HarmonyPatch] attributes in a mod match actual game classes, methods, and signatures.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mod_name": {"type": "string", "description": "Name of mod directory under plugins/"}
                    },
                    "required": ["mod_name"]
                }
            },
            {
                "name": "get_game_logs",
                "description": "Read trailing logs from BepInEx mod logger or Unity Player.log.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "enum": ["bepinex", "player"], "default": "bepinex"},
                        "lines": {"type": "integer", "default": 40},
                        "errors_only": {"type": "boolean", "default": False}
                    }
                }
            },
            {
                "name": "get_vehicle_specs",
                "description": "Inspect aircraft flight specs, radar cross section, and hardpoint station configurations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Vehicle name or designation (e.g. 'Revoker', 'FS-12', 'Darkreach')"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "render_mission_map",
                "description": "Render a tactical 2D ASCII radar map of all units and airbases in a mission.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mission_name": {"type": "string", "description": "Name of mission in MissionEditor"},
                        "width": {"type": "integer", "default": 60},
                        "height": {"type": "integer", "default": 24}
                    },
                    "required": ["mission_name"]
                }
            },
            {
                "name": "get_network_rpcs",
                "description": "Query Mirage multiplayer RPCs (ServerRpc, ClientRpc, TargetRpc) and SyncVars.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string", "description": "Filter by class name (e.g. Aircraft, Player)"},
                        "rpc_type": {"type": "string", "description": "Filter by RPC type (ServerRpc, ClientRpc, SyncVar)"},
                        "query": {"type": "string", "description": "Search keyword in method name or parameter"}
                    }
                }
            },
            {
                "name": "create_mission_scenario",
                "description": "Programmatically generate a new valid mission.json scenario in MissionEditor.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Mission name"},
                        "preset": {"type": "string", "enum": ["dogfight", "strike", "naval_patrol"], "default": "dogfight"},
                        "player_faction": {"type": "string", "default": "Boscali"},
                        "enemy_faction": {"type": "string", "default": "Primeva"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "get_audio_events",
                "description": "Inspect game sound effects, SoundManager calls, and cockpit voice warnings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "VoiceWarning, Interface, Effects, Alert"},
                        "class_name": {"type": "string", "description": "Filter by class name"},
                        "query": {"type": "string", "description": "Search keyword"}
                    }
                }
            },
            {
                "name": "validate_mission_scenario",
                "description": "Validate a mission scenario for missing factions, ground collisions, and broken targets.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Mission name in MissionEditor or path to mission.json"}
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "get_method_il",
                "description": "Disassemble class and method to raw CIL bytecode instructions and generate Harmony CodeMatcher transpiler.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string", "description": "Class name (e.g. RadarWarning)"},
                        "method_name": {"type": "string", "description": "Method name (e.g. Start)"},
                        "include_matcher": {"type": "boolean", "description": "Whether to generate Harmony CodeMatcher template"}
                    },
                    "required": ["class_name", "method_name"]
                }
            },
            {
                "name": "create_aircraft_livery",
                "description": "Scaffold a custom aircraft skin package and BepInEx runtime texture loader.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vehicle": {"type": "string", "description": "Aircraft name (e.g. Revoker, Cricket)"},
                        "skin_name": {"type": "string", "description": "Skin name (e.g. GhostSquadron)"},
                        "author": {"type": "string", "description": "Author name"}
                    },
                    "required": ["vehicle", "skin_name"]
                }
            },
            {
                "name": "audit_mod_performance",
                "description": "Audit BepInEx mod source code for performance traps, GC allocations in Update, and stutter hazards.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mod_name": {"type": "string", "description": "Mod directory name in plugins/ (e.g. NuclearTelemetry)"}
                    },
                    "required": ["mod_name"]
                }
            }
        ]





    def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        if name == "get_class_api":
            info = self.indexer.parse_class(args["class_name"])
            if not info:
                return f"Class '{args['class_name']}' not found."
            return {
                "name": info.name,
                "base_class": info.base_class,
                "interfaces": info.interfaces,
                "fields": [{"name": f.name, "type": f.type_name, "access": f.access, "line": f.line_number} for f in info.fields],
                "methods": [{"name": m.name, "return_type": m.return_type, "params": m.parameters, "access": m.access, "line": m.line_number} for m in info.methods],
                "structs": [{"name": s.name, "fields": s.fields, "line": s.line_number} for s in info.structs],
                "events": [{"name": e.name, "type": e.event_type, "line": e.line_number} for e in info.events],
                "enums": [{"name": en.name, "values": en.values, "line": en.line_number} for en in info.enums],
            }

        elif name == "get_method_code":
            res = self.indexer.get_method_source(args["class_name"], args["method_name"])
            if not res:
                return f"Method '{args['method_name']}' not found in '{args['class_name']}'."
            source, line_no = res
            return {"source": source, "start_line": line_no, "class": args["class_name"], "method": args["method_name"]}

        elif name == "generate_harmony_hook":
            patch = self.indexer.generate_harmony_patch(args["class_name"], args["method_name"], patch_type=args.get("patch_type", "Prefix"))
            if not patch:
                return f"Could not generate patch for {args['class_name']}.{args['method_name']}."
            return {"patch": patch}

        elif name == "find_callers":
            callers = self.indexer.find_callers(args["target"], limit=args.get("limit", 25))
            return [{"class": cl, "line": ln, "snippet": sn} for cl, ln, sn in callers]

        elif name == "find_subclasses":
            subs = self.indexer.find_subclasses(args["base_class"])
            return [{"subclass": name, "file": path.name} for name, path in subs]

        elif name == "find_enums":
            target = args["target"]
            info = self.indexer.parse_class(target)
            if info and info.enums:
                return [{"name": en.name, "values": en.values, "line": en.line_number} for en in info.enums]
            
            # Global enum search
            results = []
            self.indexer._ensure_cache()
            for path in self.indexer._class_cache.values():
                c_info = self.indexer.parse_class(path.stem)
                if c_info:
                    for en in c_info.enums:
                        if target.lower() in en.name.lower():
                            results.append({"name": en.name, "values": en.values, "class": c_info.name, "line": en.line_number})
            return results

        elif name == "search_code":
            matches = self.indexer.search_similar_apis(args["query"], max_results=args.get("limit", 20))
            return [{"class": m.class_name, "method": m.name, "parameters": m.parameters, "return_type": m.return_type} for m in matches]

        elif name == "analyze_mission":
            target = args["mission_name"]
            p = Path(target)
            if not p.exists():
                p = config.mission_editor_dir / target / "mission.json"
            if not p.exists():
                return f"Mission '{target}' not found."
            mission = self.scanner.parse_mission(p)
            report = self.analyzer.analyze(mission)
            return {
                "mission_name": report.mission_name,
                "summary": report.summary,
                "air_superiority_balance": report.air_superiority_balance,
                "air_balance_score": report.air_balance_score,
                "threat_assessments": [t.model_dump() for t in report.threat_assessments],
                "tactical_recommendations": report.tactical_recommendations,
            }

        elif name == "verify_mod_patches":
            from nuclear_engine.builder.patch_verifier import PatchVerifier
            verifier = PatchVerifier(self.indexer)
            results = verifier.verify_mod(args["mod_name"])
            return [
                {
                    "target_class": r.target_class,
                    "target_method": r.target_method,
                    "patch_type": r.patch_type,
                    "status": r.status,
                    "valid": r.is_valid,
                    "line": r.line,
                    "issues": [{"severity": i.severity, "message": i.message, "line": i.line} for i in r.issues],
                }
                for r in results
            ]

        elif name == "get_game_logs":
            from nuclear_engine.diagnostics.log_viewer import LogViewer
            viewer = LogViewer()
            entries = viewer.read_entries(
                source=args.get("source", "bepinex"),
                lines=args.get("lines", 40),
                errors_only=args.get("errors_only", False),
            )
            return [{"source": e.source, "level": e.level, "message": e.message} for e in entries]

        elif name == "get_vehicle_specs":

            from nuclear_engine.domain.vehicle_inspector import VehicleInspector
            v = VehicleInspector.get_vehicle(args["name"])
            if not v:
                return f"Vehicle '{args['name']}' not found."
            return {
                "name": v.name,
                "designation": v.designation,
                "role": v.role,
                "empty_weight_kg": v.empty_weight_kg,
                "max_takeoff_weight_kg": v.max_takeoff_weight_kg,
                "top_speed_mach": v.top_speed_mach,
                "rcs_m2": v.rcs_m2,
                "radar_type": v.radar_type,
                "hardpoints": [{"station": h.station_index, "name": h.name, "max_weight_kg": h.max_weight_kg, "weapons": h.compatible_weapons} for h in v.hardpoints],
            }

        elif name == "render_mission_map":
            from nuclear_engine.tactical_advisor.map_renderer import TacticalMapRenderer
            res = self.scanner.load_latest_mission_file(args["mission_name"])
            if not res:
                return f"Mission '{args['mission_name']}' not found."
            path, mission = res
            renderer = TacticalMapRenderer(mission)
            return renderer.render_ascii(width=args.get("width", 60), height=args.get("height", 24))

        elif name == "get_network_rpcs":
            from nuclear_engine.extractor.rpc_inspector import RPCInspector
            inspector = RPCInspector()
            results = inspector.query(
                class_filter=args.get("class_name"),
                rpc_type=args.get("rpc_type"),
                search_query=args.get("query"),
            )
            return [
                {
                    "type": r.endpoint_type,
                    "class": r.declaring_class,
                    "name": r.name,
                    "parameters": r.parameters,
                    "attributes": r.attributes,
                    "line": r.line_number,
                }
                for r in results
            ]

        elif name == "create_mission_scenario":
            from nuclear_engine.domain.mission_generator import MissionFactory
            path = MissionFactory.save_to_mission_editor(
                mission_name=args["name"],
                preset=args.get("preset", "dogfight"),
                player_faction=args.get("player_faction", "Boscali"),
                enemy_faction=args.get("enemy_faction", "Primeva"),
            )
            return {"status": "created", "path": str(path), "name": args["name"]}

        elif name == "get_audio_events":
            from nuclear_engine.extractor.audio_inspector import AudioInspector
            inspector = AudioInspector()
            results = inspector.query(
                category=args.get("category"),
                class_filter=args.get("class_name"),
                search_query=args.get("query"),
            )
            return [
                {
                    "category": a.category,
                    "class": a.class_name,
                    "event": a.event_name,
                    "mixer": a.mixer_group,
                    "method": a.trigger_method,
                    "line": a.line_number,
                }
                for a in results
            ]

        elif name == "validate_mission_scenario":
            from nuclear_engine.domain.mission_validator import MissionValidator
            res = MissionValidator.validate_file(args["target"])
            return {
                "mission_name": res.mission_name,
                "is_valid": res.is_valid,
                "error_count": res.error_count,
                "warning_count": res.warning_count,
                "issues": [i.__dict__ for i in res.issues],
            }

        elif name == "get_method_il":
            from nuclear_engine.extractor.il_inspector import ILInspector
            inspector = ILInspector()
            method = inspector.get_method_il(args["class_name"], args["method_name"])
            if not method:
                return {"error": f"Method {args['class_name']}.{args['method_name']} not found."}
            data = {
                "class_name": method.class_name,
                "method_name": method.method_name,
                "signature": method.signature,
                "code_size": method.code_size,
                "instructions": [
                    {"offset": inst.offset, "opcode": inst.opcode, "operand": inst.operand}
                    for inst in method.instructions
                ]
            }
            if args.get("include_matcher"):
                data["matcher_template"] = inspector.generate_matcher_template(method)
            return data

        elif name == "create_aircraft_livery":
            from nuclear_engine.builder.livery_scaffolder import LiveryScaffolder
            out_dir = LiveryScaffolder.scaffold(
                vehicle_name=args["vehicle"],
                skin_name=args["skin_name"],
                author=args.get("author", "Modder"),
            )
            return {"status": "created", "path": str(out_dir)}

        elif name == "audit_mod_performance":
            from nuclear_engine.diagnostics.code_auditor import CodeAuditor
            result = CodeAuditor.audit_mod(args["mod_name"])
            return {
                "mod_name": result.mod_name,
                "is_clean": result.is_clean,
                "critical_count": result.critical_count,
                "warning_count": result.warning_count,
                "issues": [i.__dict__ for i in result.issues],
            }

        raise ValueError(f"Unknown tool: {name}")





    def run(self):
        """Standard JSON-RPC 2.0 stdio server loop for MCP."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            # MCP Initialize
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "nuclear-option-sdk",
                            "version": "1.0.0"
                        }
                    }
                }
                self._send(resp)

            elif method == "notifications/initialized":
                pass

            # List Tools
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": self.get_tools()
                    }
                }
                self._send(resp)

            # Call Tool
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                try:
                    result_data = self.call_tool(tool_name, arguments)
                    text_content = json.dumps(result_data, indent=2) if not isinstance(result_data, str) else result_data
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": text_content
                                }
                            ]
                        }
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                self._send(resp)

            else:
                if msg_id is not None:
                    self._send({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found"
                        }
                    })

    def _send(self, obj: Dict[str, Any]):
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()


def start_mcp_server():
    server = NuclearMCPServer()
    server.run()


if __name__ == "__main__":
    start_mcp_server()
