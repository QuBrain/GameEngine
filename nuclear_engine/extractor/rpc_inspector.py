"""Multiplayer & Mirage RPC / SyncVar Inspector for Nuclear Option."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

from nuclear_engine.config import config


@dataclass
class NetworkEndpoint:
    endpoint_type: str  # "ServerRpc", "ClientRpc", "TargetRpc", "SyncVar"
    declaring_class: str
    name: str
    parameters: str
    attributes: str
    file_name: str
    line_number: int


class RPCInspector:
    def __init__(self, source_dir: Optional[Path] = None):
        self.source_dir = source_dir or (config.workspace_root / "no_code_analysis" / "source")
        self._endpoints_cache: Optional[List[NetworkEndpoint]] = None

    def scan_all(self, force_rescan: bool = False) -> List[NetworkEndpoint]:
        if self._endpoints_cache is not None and not force_rescan:
            return self._endpoints_cache

        endpoints: List[NetworkEndpoint] = []
        if not self.source_dir.exists():
            return []

        rpc_attr_regex = re.compile(r"\[(ServerRpc|ClientRpc|TargetRpc)(?:\((.*?)\))?\]")
        syncvar_attr_regex = re.compile(r"\[SyncVar(?:\((.*?)\))?\]")
        method_regex = re.compile(r"(?:public|private|protected|internal)?\s*(?:override|virtual|async)?\s*([\w<>\[\], ?]+)\s+([A-Za-z0-9_]+)\s*\((.*?)\)")
        field_regex = re.compile(r"(?:public|private|protected|internal)?\s*([\w<>\[\], ?]+)\s+([A-Za-z0-9_]+)\s*;")

        for file_path in self.source_dir.rglob("*.cs"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            current_class = file_path.stem

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Look for RPC attributes
                rpc_match = rpc_attr_regex.search(stripped)
                if rpc_match:
                    ep_type = rpc_match.group(1)
                    ep_attrs = rpc_match.group(2) or ""

                    # Inspect following lines for method declaration
                    for j in range(i + 1, min(i + 5, len(lines))):
                        m_line = lines[j].strip()
                        m_match = method_regex.search(m_line)
                        if m_match and not m_line.startswith("//"):
                            m_name = m_match.group(2)
                            m_params = m_match.group(3)
                            endpoints.append(NetworkEndpoint(
                                endpoint_type=ep_type,
                                declaring_class=current_class,
                                name=m_name,
                                parameters=m_params,
                                attributes=ep_attrs,
                                file_name=file_path.name,
                                line_number=j + 1,
                            ))
                            break

                # Look for SyncVar attributes
                sync_match = syncvar_attr_regex.search(stripped)
                if sync_match:
                    ep_attrs = sync_match.group(1) or ""
                    for j in range(i + 1, min(i + 4, len(lines))):
                        f_line = lines[j].strip()
                        f_match = field_regex.search(f_line)
                        if f_match and not f_line.startswith("//"):
                            f_name = f_match.group(2)
                            f_type = f_match.group(1)
                            endpoints.append(NetworkEndpoint(
                                endpoint_type="SyncVar",
                                declaring_class=current_class,
                                name=f_name,
                                parameters=f_type,
                                attributes=ep_attrs,
                                file_name=file_path.name,
                                line_number=j + 1,
                            ))
                            break

        self._endpoints_cache = endpoints
        return endpoints

    def query(
        self,
        class_filter: Optional[str] = None,
        rpc_type: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[NetworkEndpoint]:
        endpoints = self.scan_all()
        results: List[NetworkEndpoint] = []

        for ep in endpoints:
            if class_filter and class_filter.lower() not in ep.declaring_class.lower():
                continue
            if rpc_type and rpc_type.lower() != ep.endpoint_type.lower():
                continue
            if search_query:
                q = search_query.lower()
                if q not in ep.name.lower() and q not in ep.parameters.lower() and q not in ep.declaring_class.lower():
                    continue
            results.append(ep)

        return results
