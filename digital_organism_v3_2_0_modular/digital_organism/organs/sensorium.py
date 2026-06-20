"""
============================================================
SENSORIUM ORGAN
============================================================

Project:
    Digital Organism

Build Compatibility:
    0.2.0 through 0.4.0

Organism Name:
    ContinuityNode

Primary Function:
    Collect a safe, read-only snapshot of the local runtime environment.

Build 0.3.0+ Expansion:
    Adds passive network mapping:
        - local network interfaces
        - IPv4/subnet/CIDR derivation
        - optional psutil support
        - passive ARP / neighbor cache collection
        - passive network connection inventory if psutil is available
        - topology seed matrix

Important Boundary:
    Sensorium does not actively scan the network.
"""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False


class SensoriumError(Exception):
    """Base exception for all Sensorium Organ errors."""


class SensoriumSnapshotError(SensoriumError):
    """Raised when the sensorium snapshot cannot be created or saved."""


class SensoriumSafetyError(SensoriumError):
    """Raised when an operation violates the Sensorium safety boundary."""


class SensoriumOrgan:
    """
    Collects a safe, read-only snapshot of the runtime environment.

    This organ observes known local state.
    It does not actively discover unknown hosts.
    """

    SCHEMA_VERSION = "1.1.0"
    DEFAULT_MODE = "READ_ONLY"
    ALLOWED_MODES = ["READ_ONLY"]

    SAFE_ENVIRONMENT_KEYS = [
        "OS",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
        "PROCESSOR_LEVEL",
        "PROCESSOR_REVISION",
        "COMPUTERNAME",
        "USERDOMAIN",
        "USERNAME",
        "USER",
        "HOME",
        "HOMEPATH",
        "HOMEDRIVE",
        "SHELL",
        "PATH",
        "PATHEXT",
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
        "TERM",
        "LANG",
    ]

    SENSITIVE_ENVIRONMENT_KEY_FRAGMENTS = [
        "TOKEN",
        "SECRET",
        "KEY",
        "PASSWORD",
        "PASS",
        "AUTH",
        "CREDENTIAL",
        "COOKIE",
        "SESSION",
        "PRIVATE",
        "CERT",
        "DATABASE_URL",
        "DB_URL",
        "CONNECTION_STRING",
        "ACCESS",
        "BEARER",
    ]

    COMMANDS_TO_CHECK = [
        "python", "python3", "pip", "pip3", "git", "where", "which",
        "ipconfig", "ifconfig", "tracert", "traceroute", "ping",
        "netstat", "nslookup", "powershell", "pwsh", "cmd", "bash",
        "sh", "arp", "ip", "route",
    ]

    READ_ONLY_NETWORK_COMMANDS_BY_OS = {
        "Windows": [["arp", "-a"]],
        "Linux": [["ip", "neigh"], ["arp", "-n"]],
        "Darwin": [["arp", "-a"]],
    }

    COMMAND_TIMEOUT_SECONDS = 3
    COMMAND_OUTPUT_LIMIT_CHARS = 25000

    def __init__(
        self,
        core_identity: Any,
        snapshot_path: str = "data/sensorium_snapshot.json",
        mode: str = "READ_ONLY",
    ) -> None:
        """Initialize the Sensorium Organ."""

        self.core_identity = core_identity
        self.snapshot_path = Path(snapshot_path)
        self.mode = mode.upper()
        self.snapshot: Dict[str, Any] = {}

        if self.mode not in self.ALLOWED_MODES:
            raise SensoriumSafetyError(f"Sensorium mode is not allowed: {self.mode}")

    def utc_now_iso(self) -> str:
        """Return current UTC time in ISO-8601 format."""

        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def generate_snapshot_id(self) -> str:
        """Generate a unique sensorium snapshot ID."""

        timestamp = self.utc_now_iso().replace("-", "").replace(":", "").replace("Z", "Z")
        return f"sensorium-{timestamp}-{uuid.uuid4().hex[:6]}"

    def generate_topology_matrix_id(self) -> str:
        """Generate a unique passive topology seed matrix ID."""

        timestamp = self.utc_now_iso().replace("-", "").replace(":", "").replace("Z", "Z")
        return f"topology-seed-{timestamp}-{uuid.uuid4().hex[:6]}"

    def create_snapshot(self) -> Dict[str, Any]:
        """Create a complete Sensorium snapshot."""

        if self.mode != "READ_ONLY":
            raise SensoriumSafetyError("Sensorium snapshot creation requires READ_ONLY mode.")

        identity_report = self.core_identity.get_identity_report()
        persistent = identity_report["persistent"]
        runtime = identity_report["runtime"]

        network_interfaces = self.collect_network_interfaces()
        arp_table = self.collect_arp_table()
        network_connections = self.collect_network_connections()
        topology_seed_matrix = self.build_topology_seed_matrix(
            network_interfaces=network_interfaces,
            arp_table=arp_table,
            network_connections=network_connections,
        )

        snapshot = {
            "schema_version": self.SCHEMA_VERSION,
            "snapshot_id": self.generate_snapshot_id(),
            "snapshot_timestamp_utc": self.utc_now_iso(),
            "source_runtime_instance_id": runtime["runtime_instance_id"],
            "source_lineage_id": persistent["lineage_id"],
            "source_organism_name": persistent["organism_name"],
            "source_active_mode": runtime["active_mode"],
            "source_build": persistent["current_build"],
            "sensorium_mode": self.mode,
            "host": self.collect_host_info(),
            "python": self.collect_python_info(),
            "filesystem": self.collect_filesystem_info(),
            "process": self.collect_process_info(),
            "user_context": self.collect_user_context(),
            "environment": self.collect_environment_summary(),
            "commands": self.check_command_availability(),
            "network_observation": self.collect_network_observation(),
            "network_interfaces": network_interfaces,
            "arp_table": arp_table,
            "network_connections": network_connections,
            "topology_seed_matrix": topology_seed_matrix,
            "safety_boundary": self.get_safety_boundary(),
        }

        self.validate_snapshot(snapshot)
        self.snapshot = snapshot
        return copy.deepcopy(snapshot)

    def create_and_save_snapshot(self) -> Dict[str, Any]:
        """Create a Sensorium snapshot and save it to disk."""

        snapshot = self.create_snapshot()
        self.save_snapshot(snapshot)
        return copy.deepcopy(snapshot)

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate basic Sensorium snapshot structure and safety."""

        required_fields = [
            "schema_version", "snapshot_id", "snapshot_timestamp_utc",
            "source_runtime_instance_id", "source_lineage_id",
            "source_organism_name", "source_active_mode", "source_build",
            "sensorium_mode", "host", "python", "filesystem", "process",
            "user_context", "environment", "commands", "network_observation",
            "network_interfaces", "arp_table", "network_connections",
            "topology_seed_matrix", "safety_boundary",
        ]

        for field in required_fields:
            if field not in snapshot:
                raise SensoriumSnapshotError(f"Missing required sensorium field: {field}")

        safety_boundary = snapshot["safety_boundary"]

        for flag in [
            "may_execute_general_shell_commands",
            "may_execute_active_network_scans",
            "may_probe_remote_hosts",
            "may_scan_ports",
            "may_access_external_network",
            "may_modify_system",
            "may_scan_private_documents",
            "may_store_raw_environment_values",
            "may_store_raw_username",
            "may_store_process_names",
        ]:
            if safety_boundary.get(flag) is True:
                raise SensoriumSafetyError(f"Sensorium safety violation: {flag}")

        if snapshot["topology_seed_matrix"].get("active_scan_performed") is not False:
            raise SensoriumSafetyError("Sensorium topology matrix must be passive only.")

        return True

    def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Save the Sensorium snapshot to disk."""

        self.validate_snapshot(snapshot)

        if not snapshot["safety_boundary"].get("may_write_snapshot_file", False):
            raise SensoriumSafetyError("Snapshot writing is not permitted.")

        try:
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            with self.snapshot_path.open("w", encoding="utf-8") as file:
                json.dump(snapshot, file, indent=2, sort_keys=False)
                file.write("\n")
        except OSError as error:
            raise SensoriumSnapshotError(f"Could not save sensorium snapshot: {error}") from error

    def collect_host_info(self) -> Dict[str, Any]:
        """Collect safe host metadata."""

        try:
            hostname = socket.gethostname()
        except OSError:
            hostname = None

        return {
            "hostname": hostname,
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
        }

    def collect_python_info(self) -> Dict[str, Any]:
        """Collect Python interpreter metadata."""

        return {
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "build": list(platform.python_build()),
            "sys_prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "virtual_environment_detected": sys.prefix != sys.base_prefix,
            "psutil_available": PSUTIL_AVAILABLE,
        }

    def collect_filesystem_info(self) -> Dict[str, Any]:
        """Collect basic filesystem context without recursive scanning."""

        cwd = Path.cwd()
        script_directory = Path(__file__).resolve().parent
        project_root_guess = script_directory.parent

        try:
            home_detected = bool(str(Path.home()))
        except RuntimeError:
            home_detected = False

        return {
            "current_working_directory": str(cwd),
            "script_directory": str(script_directory),
            "project_root_guess": str(project_root_guess),
            "home_directory_detected": home_detected,
            "home_directory_label": "available" if home_detected else "unavailable",
            "data_directory": str(self.snapshot_path.parent),
            "snapshot_path": str(self.snapshot_path),
            "recursive_filesystem_scan_performed": False,
        }

    def collect_process_info(self) -> Dict[str, Any]:
        """Collect current-process metadata only."""

        try:
            parent_process_id = os.getppid()
        except AttributeError:
            parent_process_id = None

        return {
            "process_id": os.getpid(),
            "parent_process_id": parent_process_id,
            "process_list_scan_performed": False,
            "process_modification_performed": False,
        }

    def collect_user_context(self) -> Dict[str, Any]:
        """Collect non-sensitive user/session context."""

        detected = any(os.environ.get(key) for key in ["USERNAME", "USER", "LOGNAME"])

        return {
            "user_name_detected": detected,
            "user_name_label": "available" if detected else "unavailable",
            "login_context_available": detected,
            "raw_user_name_stored": False,
        }

    def collect_environment_summary(self) -> Dict[str, Any]:
        """Collect a safe environment variable summary."""

        env_keys = list(os.environ.keys())
        included_keys = [key for key in self.SAFE_ENVIRONMENT_KEYS if key in os.environ]
        sensitive_categories = self.detect_sensitive_environment_keys(env_keys)

        return {
            "environment_variable_count": len(env_keys),
            "included_environment_keys": included_keys,
            "raw_environment_values_stored": False,
            "sensitive_environment_categories_detected": sensitive_categories,
            "sensitive_environment_keys_detected": bool(sensitive_categories),
        }

    def detect_sensitive_environment_keys(self, env_keys: List[str]) -> List[str]:
        """Detect sensitive-looking environment variable categories by key name only."""

        detected_categories = set()
        upper_keys = [key.upper() for key in env_keys]

        for key in upper_keys:
            for fragment in self.SENSITIVE_ENVIRONMENT_KEY_FRAGMENTS:
                if fragment in key:
                    detected_categories.add(fragment)

        return sorted(detected_categories)

    def check_command_availability(self) -> Dict[str, bool]:
        """Check whether common commands appear available without executing them."""

        return {command: shutil.which(command) is not None for command in self.COMMANDS_TO_CHECK}

    def collect_network_observation(self) -> Dict[str, Any]:
        """Collect minimal passive network observation metadata."""

        success = False
        count = 0

        try:
            hostname = socket.gethostname()
            _name, _aliases, addresses = socket.gethostbyname_ex(hostname)
            success = True
            count = len(addresses)
        except OSError:
            success = False
            count = 0

        return {
            "network_scan_performed": False,
            "active_network_scan_performed": False,
            "external_network_access_performed": False,
            "public_ip_lookup_performed": False,
            "ping_performed": False,
            "port_scan_performed": False,
            "traceroute_performed": False,
            "local_hostname_resolution_attempted": True,
            "local_hostname_resolution_success": success,
            "local_hostname_address_count": count,
        }

    def collect_network_interfaces(self) -> Dict[str, Any]:
        """Collect passive local network interface information."""

        if PSUTIL_AVAILABLE:
            interfaces = self.collect_network_interfaces_psutil()
            method = "psutil.net_if_addrs"
        else:
            interfaces = self.collect_network_interfaces_standard_library_fallback()
            method = "standard_library_fallback"

        ipv4_count = sum(len(record.get("ipv4_addresses", [])) for record in interfaces)

        return {
            "collection_attempted": True,
            "collection_method": method,
            "psutil_available": PSUTIL_AVAILABLE,
            "active_scan_performed": False,
            "interface_count": len(interfaces),
            "ipv4_address_count": ipv4_count,
            "interfaces": interfaces,
        }

    def collect_network_interfaces_psutil(self) -> List[Dict[str, Any]]:
        """Collect network interface data using psutil."""

        records: List[Dict[str, Any]] = []
        addrs_by_interface = psutil.net_if_addrs()  # type: ignore[union-attr]

        try:
            stats_by_interface = psutil.net_if_stats()  # type: ignore[union-attr]
        except Exception:
            stats_by_interface = {}

        for interface_name, addresses in addrs_by_interface.items():
            ipv4_addresses = []
            ipv6_addresses = []
            mac_addresses = []

            for addr in addresses:
                address = getattr(addr, "address", None)
                netmask = getattr(addr, "netmask", None)
                broadcast = getattr(addr, "broadcast", None)

                if not address:
                    continue

                if addr.family == socket.AF_INET:
                    ipv4_addresses.append(self.build_ipv4_record(address, netmask, broadcast))
                elif addr.family == socket.AF_INET6:
                    ipv6_addresses.append(
                        {
                            "ip_address": address,
                            "is_loopback": address == "::1",
                            "is_link_local": address.lower().startswith("fe80"),
                            "raw_scope_id_may_be_present": "%" in address,
                        }
                    )
                elif self.looks_like_mac_address(address):
                    mac_addresses.append(
                        {
                            "mac_address_stored": "hashed",
                            "mac_address_hash": self.hash_mac_address(address),
                            "raw_mac_address_stored": False,
                        }
                    )

            stats = stats_by_interface.get(interface_name)

            records.append(
                {
                    "interface_name": interface_name,
                    "interface_status_available": stats is not None,
                    "is_up": getattr(stats, "isup", None) if stats else None,
                    "speed_mbps": getattr(stats, "speed", None) if stats else None,
                    "mtu": getattr(stats, "mtu", None) if stats else None,
                    "mac_addresses": mac_addresses,
                    "ipv4_addresses": ipv4_addresses,
                    "ipv6_addresses": ipv6_addresses,
                }
            )

        return records

    def collect_network_interfaces_standard_library_fallback(self) -> List[Dict[str, Any]]:
        """Minimal fallback when psutil is unavailable."""

        try:
            hostname = socket.gethostname()
            _name, _aliases, addresses = socket.gethostbyname_ex(hostname)
            ipv4_records = [self.build_ipv4_record(ip, None, None) for ip in addresses]
        except OSError:
            ipv4_records = []

        return [
            {
                "interface_name": "standard_library_hostname_resolution",
                "interface_status_available": False,
                "is_up": None,
                "speed_mbps": None,
                "mtu": None,
                "mac_addresses": [],
                "ipv4_addresses": ipv4_records,
                "ipv6_addresses": [],
            }
        ]

    def build_ipv4_record(self, ip_address: str, netmask: Optional[str], broadcast: Optional[str]) -> Dict[str, Any]:
        """Build a normalized IPv4 address record."""

        prefix_length = None
        network_cidr = None

        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if netmask:
                interface = ipaddress.ip_interface(f"{ip_address}/{netmask}")
                prefix_length = interface.network.prefixlen
                network_cidr = str(interface.network)

            return {
                "ip_address": ip_address,
                "netmask": netmask,
                "prefix_length": prefix_length,
                "network_cidr": network_cidr,
                "broadcast": broadcast,
                "is_private": ip_obj.is_private,
                "is_loopback": ip_obj.is_loopback,
                "is_link_local": ip_obj.is_link_local,
                "is_multicast": ip_obj.is_multicast,
                "ip_version": ip_obj.version,
            }
        except ValueError:
            return {
                "ip_address": ip_address,
                "netmask": netmask,
                "prefix_length": prefix_length,
                "network_cidr": network_cidr,
                "broadcast": broadcast,
                "is_private": None,
                "is_loopback": None,
                "is_link_local": None,
                "is_multicast": None,
                "ip_version": None,
                "parse_error": True,
            }

    def collect_arp_table(self) -> Dict[str, Any]:
        """Collect passive ARP / neighbor cache entries through a strict allowlist."""

        system_name = platform.system()
        commands = self.READ_ONLY_NETWORK_COMMANDS_BY_OS.get(system_name, [])
        command_results = []
        entries: List[Dict[str, Any]] = []

        for command in commands:
            result = self.run_read_only_observation_command(command)
            command_results.append(result)

            if not result["executed"] or result["return_code"] != 0:
                continue

            output = result.get("stdout", "")

            if system_name == "Windows" and command[:2] == ["arp", "-a"]:
                entries.extend(self.parse_arp_output_windows(output))
            elif system_name in ["Linux", "Darwin"] and command[:2] == ["arp", "-a"]:
                entries.extend(self.parse_arp_output_linux_mac(output))
            elif system_name == "Linux" and command[:2] == ["ip", "neigh"]:
                entries.extend(self.parse_ip_neigh_output_linux(output))
            elif system_name == "Linux" and command[:2] == ["arp", "-n"]:
                entries.extend(self.parse_arp_output_linux_mac(output))

        deduped_entries = self.dedupe_arp_entries(entries)

        return {
            "collection_attempted": bool(commands),
            "collection_method": "strict_read_only_command_allowlist",
            "platform_system": system_name,
            "allowed_commands_considered": commands,
            "read_only_commands_executed": sum(1 for r in command_results if r["executed"]),
            "active_scan_performed": False,
            "entries_count": len(deduped_entries),
            "entries": deduped_entries,
            "command_results_summary": [
                {
                    "command": result["command"],
                    "executed": result["executed"],
                    "return_code": result["return_code"],
                    "stdout_truncated": result["stdout_truncated"],
                    "stderr_truncated": result["stderr_truncated"],
                    "error": result["error"],
                }
                for result in command_results
            ],
        }

    def run_read_only_observation_command(self, command: List[str]) -> Dict[str, Any]:
        """Execute an allowlisted read-only network observation command."""

        if not self.is_allowed_read_only_network_command(command):
            raise SensoriumSafetyError(f"Command is not allowlisted: {command}")

        executable = command[0]

        if shutil.which(executable) is None:
            return {
                "command": command,
                "executed": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "stdout_truncated": False,
                "stderr_truncated": False,
                "error": f"Executable not found on PATH: {executable}",
            }

        try:
            completed = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.COMMAND_TIMEOUT_SECONDS,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stdout_truncated = self.truncate_text(completed.stdout)
            stderr, stderr_truncated = self.truncate_text(completed.stderr)

            return {
                "command": command,
                "executed": True,
                "return_code": completed.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "executed": True,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "stdout_truncated": False,
                "stderr_truncated": False,
                "error": "Command timed out.",
            }
        except OSError as error:
            return {
                "command": command,
                "executed": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "stdout_truncated": False,
                "stderr_truncated": False,
                "error": str(error),
            }

    def is_allowed_read_only_network_command(self, command: List[str]) -> bool:
        """Confirm a command exactly matches the OS allowlist."""

        return command in self.READ_ONLY_NETWORK_COMMANDS_BY_OS.get(platform.system(), [])

    def truncate_text(self, text: str) -> Tuple[str, bool]:
        """Truncate command output to prevent excessive snapshot size."""

        if len(text) <= self.COMMAND_OUTPUT_LIMIT_CHARS:
            return text, False
        return text[: self.COMMAND_OUTPUT_LIMIT_CHARS], True

    def parse_arp_output_windows(self, output: str) -> List[Dict[str, Any]]:
        """Parse Windows arp -a output."""

        entries: List[Dict[str, Any]] = []
        current_interface = None
        interface_pattern = re.compile(r"Interface:\s+([\d\.]+)\s+---")
        entry_pattern = re.compile(r"^\s*([\d\.]+)\s+([0-9a-fA-F\-]{17})\s+(\w+)\s*$")

        for line in output.splitlines():
            interface_match = interface_pattern.search(line)
            if interface_match:
                current_interface = interface_match.group(1)
                continue

            entry_match = entry_pattern.match(line)
            if entry_match:
                entries.append(
                    self.build_arp_entry(
                        ip_address=entry_match.group(1),
                        mac_address=entry_match.group(2).replace("-", ":").lower(),
                        interface=current_interface,
                        entry_type=entry_match.group(3).lower(),
                        source="windows_arp_a",
                    )
                )

        return entries

    def parse_arp_output_linux_mac(self, output: str) -> List[Dict[str, Any]]:
        """Parse common Linux/macOS arp output."""

        entries: List[Dict[str, Any]] = []
        mac_pattern = r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})"
        ip_pattern = r"(\d{1,3}(?:\.\d{1,3}){3})"

        for line in output.splitlines():
            ip_match = re.search(ip_pattern, line)
            mac_match = re.search(mac_pattern, line)

            if not ip_match or not mac_match:
                continue

            interface = None
            on_match = re.search(r"\bon\s+([A-Za-z0-9_\-\.]+)", line)
            if on_match:
                interface = on_match.group(1)

            entries.append(
                self.build_arp_entry(
                    ip_address=ip_match.group(1),
                    mac_address=mac_match.group(1).lower(),
                    interface=interface,
                    entry_type="observed",
                    source="arp_output",
                )
            )

        return entries

    def parse_ip_neigh_output_linux(self, output: str) -> List[Dict[str, Any]]:
        """Parse Linux ip neigh output."""

        entries: List[Dict[str, Any]] = []
        pattern = re.compile(
            r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
            r"dev\s+(?P<iface>[^\s]+).*?"
            r"(?:lladdr\s+(?P<mac>[0-9a-fA-F:]{17}))?.*?"
            r"(?P<state>REACHABLE|STALE|DELAY|PROBE|FAILED|INCOMPLETE|PERMANENT|NOARP)?$"
        )

        for line in output.splitlines():
            match = pattern.search(line)
            if not match:
                continue

            entries.append(
                self.build_arp_entry(
                    ip_address=match.group("ip"),
                    mac_address=match.group("mac"),
                    interface=match.group("iface"),
                    entry_type=(match.group("state") or "unknown").lower(),
                    source="linux_ip_neigh",
                )
            )

        return entries

    def build_arp_entry(
        self,
        ip_address: str,
        mac_address: Optional[str],
        interface: Optional[str],
        entry_type: str,
        source: str,
    ) -> Dict[str, Any]:
        """Build a normalized ARP / neighbor cache entry."""

        ip_parse = self.safe_parse_ip(ip_address)

        return {
            "ip_address": ip_address,
            "ip_version": ip_parse.get("ip_version"),
            "is_private": ip_parse.get("is_private"),
            "is_loopback": ip_parse.get("is_loopback"),
            "is_link_local": ip_parse.get("is_link_local"),
            "mac_address_stored": "hashed" if mac_address else "unavailable",
            "mac_address_hash": self.hash_mac_address(mac_address) if mac_address else None,
            "raw_mac_address_stored": False,
            "interface": interface,
            "entry_type": entry_type,
            "source": source,
            "confidence": 0.7,
        }

    def dedupe_arp_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate ARP entries."""

        seen = set()
        deduped = []

        for entry in entries:
            key = (entry.get("ip_address"), entry.get("mac_address_hash"), entry.get("interface"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)

        return deduped

    def collect_network_connections(self) -> Dict[str, Any]:
        """Collect passive current network connection inventory if psutil exists."""

        if not PSUTIL_AVAILABLE:
            return {
                "collection_attempted": False,
                "collection_method": "psutil_unavailable",
                "psutil_available": False,
                "active_connections_initiated": False,
                "process_names_stored": False,
                "connections_count": 0,
                "connections": [],
            }

        try:
            raw_connections = psutil.net_connections(kind="inet")  # type: ignore[union-attr]
        except Exception as error:
            return {
                "collection_attempted": True,
                "collection_method": "psutil.net_connections",
                "psutil_available": True,
                "active_connections_initiated": False,
                "process_names_stored": False,
                "error": str(error),
                "connections_count": 0,
                "connections": [],
            }

        connections = []

        for conn in raw_connections:
            local_ip = getattr(conn.laddr, "ip", None) if conn.laddr else None
            local_port = getattr(conn.laddr, "port", None) if conn.laddr else None
            remote_ip = getattr(conn.raddr, "ip", None) if conn.raddr else None
            remote_port = getattr(conn.raddr, "port", None) if conn.raddr else None

            connections.append(
                {
                    "family": str(conn.family),
                    "type": str(conn.type),
                    "status": conn.status,
                    "local_address": local_ip,
                    "local_port": local_port,
                    "remote_address": remote_ip,
                    "remote_port": remote_port,
                    "pid_available": conn.pid is not None,
                    "pid": conn.pid,
                    "process_name_stored": False,
                    "connection_initiated_by_sensorium": False,
                }
            )

        return {
            "collection_attempted": True,
            "collection_method": "psutil.net_connections",
            "psutil_available": True,
            "active_connections_initiated": False,
            "process_names_stored": False,
            "connections_count": len(connections),
            "connections": connections,
        }

    def build_topology_seed_matrix(
        self,
        network_interfaces: Dict[str, Any],
        arp_table: Dict[str, Any],
        network_connections: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a passive graph-like topology seed matrix."""

        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        local_host_id = "local-host"
        nodes[local_host_id] = {
            "node_id": local_host_id,
            "node_type": "self",
            "ip_addresses": [],
            "network_cidrs": [],
            "mac_address_hashes": [],
            "confidence": 1.0,
            "evidence": ["local_interface"],
        }

        for interface in network_interfaces.get("interfaces", []):
            interface_name = interface.get("interface_name")

            for mac in interface.get("mac_addresses", []):
                mac_hash = mac.get("mac_address_hash")
                if mac_hash and mac_hash not in nodes[local_host_id]["mac_address_hashes"]:
                    nodes[local_host_id]["mac_address_hashes"].append(mac_hash)

            for ipv4 in interface.get("ipv4_addresses", []):
                ip_address = ipv4.get("ip_address")
                network_cidr = ipv4.get("network_cidr")

                if ip_address and ip_address not in nodes[local_host_id]["ip_addresses"]:
                    nodes[local_host_id]["ip_addresses"].append(ip_address)

                if network_cidr:
                    if network_cidr not in nodes[local_host_id]["network_cidrs"]:
                        nodes[local_host_id]["network_cidrs"].append(network_cidr)

                    network_node_id = f"network-{network_cidr}"
                    nodes.setdefault(
                        network_node_id,
                        {
                            "node_id": network_node_id,
                            "node_type": "derived_local_subnet",
                            "network_cidr": network_cidr,
                            "confidence": 0.85,
                            "evidence": ["derived_subnet", "local_interface"],
                        },
                    )
                    edges.append(
                        {
                            "source": local_host_id,
                            "target": network_node_id,
                            "relationship": "attached_to_derived_subnet",
                            "interface": interface_name,
                            "confidence": 0.85,
                            "evidence": ["local_interface"],
                        }
                    )

        for entry in arp_table.get("entries", []):
            ip_address = entry.get("ip_address")
            if not ip_address:
                continue

            node_id = f"neighbor-{ip_address}"
            nodes.setdefault(
                node_id,
                {
                    "node_id": node_id,
                    "node_type": "neighbor_observed",
                    "ip_addresses": [ip_address],
                    "mac_address_hash": entry.get("mac_address_hash"),
                    "confidence": entry.get("confidence", 0.7),
                    "evidence": ["arp_table"],
                },
            )
            edges.append(
                {
                    "source": local_host_id,
                    "target": node_id,
                    "relationship": "same_l2_neighbor_cache",
                    "interface": entry.get("interface"),
                    "confidence": entry.get("confidence", 0.7),
                    "evidence": ["arp_table"],
                }
            )

        for connection in network_connections.get("connections", []):
            remote_address = connection.get("remote_address")
            if not remote_address:
                continue

            remote_node_id = f"remote-{remote_address}"
            nodes.setdefault(
                remote_node_id,
                {
                    "node_id": remote_node_id,
                    "node_type": "remote_endpoint_observed",
                    "ip_addresses": [remote_address],
                    **self.safe_parse_ip(remote_address),
                    "confidence": 0.55,
                    "evidence": ["passive_connection"],
                },
            )
            edges.append(
                {
                    "source": local_host_id,
                    "target": remote_node_id,
                    "relationship": "has_passive_connection_record",
                    "local_port": connection.get("local_port"),
                    "remote_port": connection.get("remote_port"),
                    "status": connection.get("status"),
                    "confidence": 0.55,
                    "evidence": ["passive_connection"],
                }
            )

        return {
            "matrix_id": self.generate_topology_matrix_id(),
            "matrix_type": "passive_observation_seed",
            "active_scan_performed": False,
            "subnet_scan_performed": False,
            "port_scan_performed": False,
            "service_fingerprinting_performed": False,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges,
            "notes": [
                "This is a passive topology seed matrix, not a complete network map.",
                "The matrix is derived from local interfaces, local neighbor cache, and passive connection state.",
                "Active network discovery belongs to the Network Cartography Organ.",
            ],
        }

    def get_safety_boundary(self) -> Dict[str, bool]:
        """Return the Sensorium Organ safety boundary."""

        return {
            "read_only_observation": True,
            "may_write_snapshot_file": True,
            "may_check_command_availability": True,
            "may_execute_general_shell_commands": False,
            "may_execute_read_only_network_observation_commands": True,
            "may_execute_active_network_scans": False,
            "may_probe_remote_hosts": False,
            "may_scan_ports": False,
            "may_perform_ping_sweep": False,
            "may_perform_traceroute": False,
            "may_fingerprint_services": False,
            "may_access_external_network": False,
            "may_lookup_public_ip": False,
            "may_modify_system": False,
            "may_scan_private_documents": False,
            "may_store_raw_environment_values": False,
            "may_store_raw_username": False,
            "may_store_raw_mac_addresses": False,
            "may_store_process_names": False,
        }

    def get_sensorium_report(self) -> Dict[str, Any]:
        """Return a short summary report of the current Sensorium snapshot."""

        if not self.snapshot:
            self.create_snapshot()

        commands = self.snapshot["commands"]
        network_interfaces = self.snapshot["network_interfaces"]
        arp_table = self.snapshot["arp_table"]
        network_connections = self.snapshot["network_connections"]
        topology = self.snapshot["topology_seed_matrix"]

        return {
            "snapshot_id": self.snapshot["snapshot_id"],
            "snapshot_timestamp_utc": self.snapshot["snapshot_timestamp_utc"],
            "sensorium_mode": self.snapshot["sensorium_mode"],
            "platform_system": self.snapshot["host"]["platform_system"],
            "platform_release": self.snapshot["host"]["platform_release"],
            "machine": self.snapshot["host"]["machine"],
            "python_version": self.snapshot["python"]["python_version"],
            "python_implementation": self.snapshot["python"]["implementation"],
            "psutil_available": self.snapshot["python"]["psutil_available"],
            "current_working_directory": self.snapshot["filesystem"]["current_working_directory"],
            "snapshot_path": self.snapshot["filesystem"]["snapshot_path"],
            "environment_variable_count": self.snapshot["environment"]["environment_variable_count"],
            "sensitive_environment_keys_detected": self.snapshot["environment"]["sensitive_environment_keys_detected"],
            "commands_checked_count": len(commands),
            "commands_available_count": sum(1 for available in commands.values() if available),
            "general_shell_commands_executed": False,
            "read_only_network_commands_executed": arp_table.get("read_only_commands_executed", 0),
            "network_interface_count": network_interfaces.get("interface_count", 0),
            "ipv4_address_count": network_interfaces.get("ipv4_address_count", 0),
            "arp_entry_count": arp_table.get("entries_count", 0),
            "network_connection_count": network_connections.get("connections_count", 0),
            "topology_node_count": topology.get("nodes_count", 0),
            "topology_edge_count": topology.get("edges_count", 0),
            "active_network_scan_performed": topology.get("active_scan_performed", False),
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the current full Sensorium snapshot."""

        return copy.deepcopy(self.snapshot)

    def safe_parse_ip(self, ip_address: str) -> Dict[str, Any]:
        """Safely parse an IP address and return basic metadata."""

        try:
            ip_obj = ipaddress.ip_address(ip_address)
            return {
                "ip_version": ip_obj.version,
                "is_private": ip_obj.is_private,
                "is_loopback": ip_obj.is_loopback,
                "is_link_local": ip_obj.is_link_local,
                "is_multicast": ip_obj.is_multicast,
                "parse_error": False,
            }
        except ValueError:
            return {
                "ip_version": None,
                "is_private": None,
                "is_loopback": None,
                "is_link_local": None,
                "is_multicast": None,
                "parse_error": True,
            }

    def looks_like_mac_address(self, value: str) -> bool:
        """Return True if a string looks like a MAC address."""

        if not value:
            return False

        colon_pattern = r"^[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$"
        dash_pattern = r"^[0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5}$"
        return bool(re.match(colon_pattern, value) or re.match(dash_pattern, value))

    def hash_mac_address(self, mac_address: Optional[str]) -> Optional[str]:
        """Hash a MAC address instead of storing it raw."""

        if not mac_address:
            return None

        normalized = mac_address.strip().lower().replace("-", ":")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{digest[:24]}"
