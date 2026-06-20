"""
============================================================
NETWORK CARTOGRAPHY ORGAN
============================================================

Project:
    Digital Organism

Build:
    0.4.0

Organism Name:
    ContinuityNode

Primary Function:
    Prepare controlled active discovery of approved local network ranges
    using strict scope, rate limits, timeout controls, and audit logs.

Build 0.4.0 Behavior:
    Dry-run skeleton only.

    This organ creates a policy file, validates scan boundaries, reads
    Sensorium's passive topology seed matrix, builds a dry-run discovery
    plan, writes a report, and appends audit events.

    It does not send network probes.
"""

from __future__ import annotations

import copy
import ipaddress
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class NetworkCartographyError(Exception):
    """Base exception for all Network Cartography Organ errors."""


class CartographyPolicyError(NetworkCartographyError):
    """Raised when the policy is missing, malformed, unsafe, or invalid."""


class CartographyScopeError(NetworkCartographyError):
    """Raised when approved scopes are invalid or outside safety boundaries."""


class CartographyAuditError(NetworkCartographyError):
    """Raised when the audit log cannot be written."""


class CartographyReportError(NetworkCartographyError):
    """Raised when the report cannot be created or saved."""


class CartographySafetyError(NetworkCartographyError):
    """Raised when a requested action violates safety boundaries."""


class NetworkCartographyOrgan:
    """
    Prepares controlled active network discovery plans.

    Build 0.4.0 does not perform active network probing.

    It creates:
        - a default policy file
        - a dry-run discovery plan
        - a report file
        - JSONL audit events
    """

    SCHEMA_VERSION = "1.0.0"
    DEFAULT_MODE = "DRY_RUN_ONLY"
    DEFAULT_ALLOWED_PROBE_TYPES = ["tcp_connect"]
    DEFAULT_ALLOWED_TCP_PORTS = [80, 443]
    DEFAULT_DISALLOWED_TCP_PORTS = [
        21, 23, 25, 110, 143, 3306, 5432, 6379, 9200
    ]

    def __init__(
        self,
        core_identity: Any,
        sensorium_snapshot: Dict[str, Any],
        policy_path: str = "data/network_cartography_policy.json",
        report_path: str = "data/network_cartography_report.json",
        audit_log_path: str = "data/network_cartography_audit_log.jsonl",
        enabled: bool = False,
    ) -> None:
        """Initialize the Network Cartography Organ."""

        self.core_identity = core_identity
        self.sensorium_snapshot = sensorium_snapshot
        self.policy_path = Path(policy_path)
        self.report_path = Path(report_path)
        self.audit_log_path = Path(audit_log_path)
        self.enabled = enabled

        self.policy_created_automatically = False
        self.policy: Dict[str, Any] = {}
        self.report: Dict[str, Any] = {}

        self.policy = self.ensure_policy_file()
        self.validate_policy(self.policy)

    def utc_now_iso(self) -> str:
        """Return the current UTC timestamp in ISO-8601 Z format."""

        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def generate_report_id(self) -> str:
        """Generate a unique network cartography report ID."""

        timestamp = self.utc_now_iso().replace("-", "").replace(":", "").replace("Z", "Z")
        return f"cartography-{timestamp}-{uuid.uuid4().hex[:6]}"

    def ensure_policy_file(self) -> Dict[str, Any]:
        """Load policy file or create default policy if missing."""

        if self.policy_path.exists():
            return self.load_policy()

        policy = self.create_default_policy()
        self.policy_created_automatically = True
        self.save_policy(policy)
        return policy

    def create_default_policy(self) -> Dict[str, Any]:
        """
        Create a default dry-run-safe policy.

        cartography_enabled is intentionally false.
        """

        derived_scopes = self.derive_private_scopes_from_sensorium()

        return {
            "schema_version": self.SCHEMA_VERSION,
            "cartography_enabled": False,
            "requires_explicit_approval": True,
            "approved_scopes": derived_scopes,
            "scope_source": "sensorium_derived_private_ranges_pending_user_review",
            "allow_private_ranges_only": True,
            "max_hosts_per_run": 32,
            "max_ports_per_host": 4,
            "probe_timeout_seconds": 0.75,
            "delay_between_probes_seconds": 0.1,
            "allowed_probe_types": list(self.DEFAULT_ALLOWED_PROBE_TYPES),
            "allowed_tcp_ports": list(self.DEFAULT_ALLOWED_TCP_PORTS),
            "disallowed_tcp_ports": list(self.DEFAULT_DISALLOWED_TCP_PORTS),
            "audit_logging_enabled": True,
            "store_raw_banners": False,
            "service_fingerprinting_enabled": False,
            "credential_testing_enabled": False,
            "vulnerability_testing_enabled": False,
            "active_cartography_implemented": False,
            "notes": [
                "Build 0.4.0 is dry-run only.",
                "No active network probes are sent by this build.",
                "Review approved_scopes before any future active cartography build.",
                "Active probing belongs to a later build with explicit enablement."
            ],
        }

    def load_policy(self) -> Dict[str, Any]:
        """Load cartography policy from disk."""

        try:
            with self.policy_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise CartographyPolicyError(
                f"network_cartography_policy.json could not be parsed: {error}"
            ) from error
        except OSError as error:
            raise CartographyPolicyError(
                f"network_cartography_policy.json could not be read: {error}"
            ) from error

        if not isinstance(data, dict):
            raise CartographyPolicyError(
                "network_cartography_policy.json must contain a JSON object."
            )

        return data

    def save_policy(self, policy: Dict[str, Any]) -> None:
        """Save cartography policy to disk."""

        try:
            self.policy_path.parent.mkdir(parents=True, exist_ok=True)
            with self.policy_path.open("w", encoding="utf-8") as file:
                json.dump(policy, file, indent=2, sort_keys=False)
                file.write("\n")
        except OSError as error:
            raise CartographyPolicyError(
                f"Could not save network cartography policy: {error}"
            ) from error

    def validate_policy(self, policy: Dict[str, Any]) -> bool:
        """Validate the network cartography policy."""

        required_fields = [
            "schema_version",
            "cartography_enabled",
            "requires_explicit_approval",
            "approved_scopes",
            "scope_source",
            "allow_private_ranges_only",
            "max_hosts_per_run",
            "max_ports_per_host",
            "probe_timeout_seconds",
            "delay_between_probes_seconds",
            "allowed_probe_types",
            "allowed_tcp_ports",
            "disallowed_tcp_ports",
            "audit_logging_enabled",
            "store_raw_banners",
            "service_fingerprinting_enabled",
            "credential_testing_enabled",
            "vulnerability_testing_enabled",
            "active_cartography_implemented",
        ]

        for field in required_fields:
            if field not in policy:
                raise CartographyPolicyError(
                    f"Missing required cartography policy field: {field}"
                )

        if policy["requires_explicit_approval"] is not True:
            raise CartographyPolicyError("requires_explicit_approval must be true.")

        if policy["allow_private_ranges_only"] is not True:
            raise CartographyPolicyError("allow_private_ranges_only must be true.")

        for flag in [
            "store_raw_banners",
            "service_fingerprinting_enabled",
            "credential_testing_enabled",
            "vulnerability_testing_enabled",
            "active_cartography_implemented",
        ]:
            if policy[flag] is not False:
                raise CartographyPolicyError(f"{flag} must be false in Build 0.4.0.")

        if int(policy["max_hosts_per_run"]) < 0 or int(policy["max_hosts_per_run"]) > 256:
            raise CartographyPolicyError("max_hosts_per_run must be between 0 and 256.")

        if int(policy["max_ports_per_host"]) < 0 or int(policy["max_ports_per_host"]) > 16:
            raise CartographyPolicyError("max_ports_per_host must be between 0 and 16.")

        for probe_type in policy["allowed_probe_types"]:
            if probe_type not in self.DEFAULT_ALLOWED_PROBE_TYPES:
                raise CartographyPolicyError(f"Probe type is not allowed: {probe_type}")

        self.validate_tcp_ports(policy["allowed_tcp_ports"])
        self.validate_tcp_ports(policy["disallowed_tcp_ports"])
        self.validate_approved_scopes(policy["approved_scopes"])

        return True

    def validate_tcp_ports(self, ports: List[Any]) -> bool:
        """Validate a list of TCP ports."""

        for port in ports:
            if not isinstance(port, int):
                raise CartographyPolicyError(f"TCP port must be an integer: {port}")
            if port < 1 or port > 65535:
                raise CartographyPolicyError(f"TCP port out of range: {port}")
        return True

    def derive_private_scopes_from_sensorium(self) -> List[str]:
        """Derive private IPv4 network scopes from the Sensorium snapshot."""

        scopes = set()
        network_interfaces = self.sensorium_snapshot.get("network_interfaces", {})
        interfaces = network_interfaces.get("interfaces", [])

        for interface in interfaces:
            for ipv4_record in interface.get("ipv4_addresses", []):
                network_cidr = ipv4_record.get("network_cidr")
                if not network_cidr:
                    continue

                if not ipv4_record.get("is_private"):
                    continue

                if (
                    ipv4_record.get("is_loopback")
                    or ipv4_record.get("is_link_local")
                    or ipv4_record.get("is_multicast")
                ):
                    continue

                try:
                    network = ipaddress.ip_network(network_cidr, strict=False)
                    if network.version == 4 and network.is_private:
                        scopes.add(str(network))
                except ValueError:
                    continue

        return sorted(scopes)

    def validate_approved_scopes(self, scopes: List[str]) -> bool:
        """Validate approved CIDR scopes."""

        for scope in scopes:
            try:
                network = ipaddress.ip_network(scope, strict=False)
            except ValueError as error:
                raise CartographyScopeError(f"Invalid approved scope: {scope}") from error

            if network.version != 4:
                raise CartographyScopeError(f"Only IPv4 scopes are supported: {scope}")

            if not network.is_private:
                raise CartographyScopeError(f"Public/non-private scope is not allowed: {scope}")

            if network.is_loopback:
                raise CartographyScopeError(f"Loopback scope is not allowed: {scope}")

            if network.is_multicast:
                raise CartographyScopeError(f"Multicast scope is not allowed: {scope}")

            if network.is_link_local:
                raise CartographyScopeError(f"Link-local scope is not allowed: {scope}")

        return True

    def limit_scope_hosts(self, scope: str, max_hosts: int) -> List[str]:
        """Return a capped dry-run list of candidate host IPs."""

        network = ipaddress.ip_network(scope, strict=False)
        candidates = []

        for host in network.hosts():
            candidates.append(str(host))
            if len(candidates) >= max_hosts:
                break

        return candidates

    def create_dry_run_plan(self) -> Dict[str, Any]:
        """Create a dry-run active discovery plan without sending probes."""

        approved_scopes = self.policy.get("approved_scopes", [])
        max_hosts_per_run = int(self.policy.get("max_hosts_per_run", 0))
        max_ports_per_host = int(self.policy.get("max_ports_per_host", 0))

        allowed_ports = list(self.policy.get("allowed_tcp_ports", []))
        disallowed_ports = set(self.policy.get("disallowed_tcp_ports", []))
        candidate_ports = [port for port in allowed_ports if port not in disallowed_ports][:max_ports_per_host]

        scopes_plan = []
        all_candidate_hosts = []

        for scope in approved_scopes:
            hosts = self.limit_scope_hosts(scope, max_hosts_per_run)

            scopes_plan.append(
                {
                    "scope": scope,
                    "candidate_hosts_limited_count": len(hosts),
                    "candidate_hosts": hosts,
                    "ports_considered": candidate_ports,
                    "planned_probe_count": len(hosts) * len(candidate_ports),
                    "active_probes_sent": 0,
                }
            )

            all_candidate_hosts.extend(hosts)

            if len(all_candidate_hosts) >= max_hosts_per_run:
                all_candidate_hosts = all_candidate_hosts[:max_hosts_per_run]
                break

        return {
            "plan_generated": True,
            "dry_run_only": True,
            "approved_scopes_count": len(approved_scopes),
            "approved_scopes": approved_scopes,
            "candidate_hosts_count": len(all_candidate_hosts),
            "candidate_hosts": all_candidate_hosts,
            "ports_considered": candidate_ports,
            "planned_probe_count": len(all_candidate_hosts) * len(candidate_ports),
            "active_probes_sent": 0,
            "notes": [
                "This is a dry-run plan only.",
                "No hosts were contacted.",
                "No TCP connections were attempted.",
                "No ICMP packets were sent.",
                "No ports were scanned.",
            ],
        }

    def run_cartography(self) -> Dict[str, Any]:
        """
        Run Network Cartography.

        Build 0.4.0 always performs dry-run only.
        """

        self.validate_policy(self.policy)

        self.write_audit_event(
            {
                "event_type": "cartography_run_started",
                "cartography_mode": self.DEFAULT_MODE,
                "active_discovery_performed": False,
                "enabled_runtime_flag": self.enabled,
                "policy_cartography_enabled": self.policy.get("cartography_enabled"),
            }
        )

        dry_run_plan = self.create_dry_run_plan()

        self.write_audit_event(
            {
                "event_type": "dry_run_plan_created",
                "candidate_hosts_count": dry_run_plan["candidate_hosts_count"],
                "planned_probe_count": dry_run_plan["planned_probe_count"],
                "active_probes_sent": 0,
            }
        )

        report = self.build_cartography_report(dry_run_plan=dry_run_plan)
        self.save_report(report)

        self.write_audit_event(
            {
                "event_type": "cartography_run_completed",
                "report_id": report["report_id"],
                "active_discovery_performed": False,
                "active_probes_sent": 0,
            }
        )

        self.report = report
        return copy.deepcopy(report)

    def probe_host_tcp(self, target_ip: str, target_port: int) -> Dict[str, Any]:
        """Placeholder for future TCP connect probing."""

        raise CartographySafetyError(
            "TCP probing is not implemented or permitted in Build 0.4.0."
        )

    def probe_host_icmp_placeholder(self, target_ip: str) -> Dict[str, Any]:
        """Placeholder for possible future ICMP reachability."""

        raise CartographySafetyError(
            "ICMP probing is not implemented or permitted in Build 0.4.0."
        )

    def build_cartography_report(self, dry_run_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Build the Network Cartography report."""

        identity_report = self.core_identity.get_identity_report()
        persistent = identity_report["persistent"]
        runtime = identity_report["runtime"]
        topology_seed = self.sensorium_snapshot.get("topology_seed_matrix", {})

        report = {
            "schema_version": self.SCHEMA_VERSION,
            "report_id": self.generate_report_id(),
            "report_timestamp_utc": self.utc_now_iso(),
            "cartography_mode": self.DEFAULT_MODE,
            "active_discovery_performed": False,
            "source_runtime_instance_id": runtime["runtime_instance_id"],
            "source_lineage_id": persistent["lineage_id"],
            "source_organism_name": persistent["organism_name"],
            "source_build": persistent["current_build"],
            "source_sensorium_snapshot_id": self.sensorium_snapshot.get("snapshot_id"),
            "source_topology_seed_matrix_id": topology_seed.get("matrix_id"),
            "policy_created_automatically": self.policy_created_automatically,
            "policy_path": str(self.policy_path),
            "report_path": str(self.report_path),
            "audit_log_path": str(self.audit_log_path),
            "policy": self.get_policy_summary(),
            "dry_run_plan": dry_run_plan,
            "topology_seed_summary": {
                "matrix_id": topology_seed.get("matrix_id"),
                "matrix_type": topology_seed.get("matrix_type"),
                "nodes_count": topology_seed.get("nodes_count", 0),
                "edges_count": topology_seed.get("edges_count", 0),
                "active_scan_performed": topology_seed.get("active_scan_performed", False),
            },
            "probe_summary": {
                "hosts_considered": dry_run_plan.get("candidate_hosts_count", 0),
                "hosts_probed": 0,
                "ports_considered": len(dry_run_plan.get("ports_considered", [])),
                "ports_probed": 0,
                "responsive_hosts": 0,
                "errors": 0,
            },
            "safety_summary": {
                "public_ranges_excluded": True,
                "private_ranges_only": True,
                "scope_limit_enforced": True,
                "rate_limit_enforced": True,
                "active_cartography_implemented": False,
                "active_probes_sent": 0,
                "credential_testing_performed": False,
                "vulnerability_testing_performed": False,
                "service_fingerprinting_performed": False,
                "banner_grabbing_performed": False,
            },
            "notes": [
                "Build 0.4.0 is dry-run only.",
                "No active probes were sent.",
                "No TCP sockets were opened.",
                "No ICMP probes were sent.",
                "No port scanning was performed.",
                "This report prepares structure for future controlled active discovery.",
            ],
        }

        self.validate_report(report)
        return report

    def get_policy_summary(self) -> Dict[str, Any]:
        """Return a safe summary of the loaded policy."""

        fields = [
            "cartography_enabled",
            "requires_explicit_approval",
            "approved_scopes",
            "scope_source",
            "allow_private_ranges_only",
            "max_hosts_per_run",
            "max_ports_per_host",
            "probe_timeout_seconds",
            "delay_between_probes_seconds",
            "allowed_probe_types",
            "allowed_tcp_ports",
            "audit_logging_enabled",
            "store_raw_banners",
            "service_fingerprinting_enabled",
            "credential_testing_enabled",
            "vulnerability_testing_enabled",
            "active_cartography_implemented",
        ]

        return {field: copy.deepcopy(self.policy.get(field)) for field in fields}

    def validate_report(self, report: Dict[str, Any]) -> bool:
        """Validate the cartography report structure and safety claims."""

        required_fields = [
            "schema_version",
            "report_id",
            "report_timestamp_utc",
            "cartography_mode",
            "active_discovery_performed",
            "source_runtime_instance_id",
            "source_lineage_id",
            "source_organism_name",
            "source_build",
            "source_sensorium_snapshot_id",
            "source_topology_seed_matrix_id",
            "policy",
            "dry_run_plan",
            "topology_seed_summary",
            "probe_summary",
            "safety_summary",
            "notes",
        ]

        for field in required_fields:
            if field not in report:
                raise CartographyReportError(
                    f"Missing required cartography report field: {field}"
                )

        if report["active_discovery_performed"] is not False:
            raise CartographySafetyError(
                "Build 0.4.0 report cannot claim active discovery was performed."
            )

        if report["safety_summary"]["active_probes_sent"] != 0:
            raise CartographySafetyError("Build 0.4.0 report cannot contain active probes.")

        if report["dry_run_plan"]["active_probes_sent"] != 0:
            raise CartographySafetyError("Dry-run plan cannot contain active probes.")

        return True

    def save_report(self, report: Dict[str, Any]) -> None:
        """Save the cartography report to disk."""

        self.validate_report(report)

        try:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            with self.report_path.open("w", encoding="utf-8") as file:
                json.dump(report, file, indent=2, sort_keys=False)
                file.write("\n")
        except OSError as error:
            raise CartographyReportError(
                f"Could not save network cartography report: {error}"
            ) from error

    def get_cartography_report(self) -> Dict[str, Any]:
        """Return a copy of the current cartography report."""

        if not self.report:
            self.run_cartography()

        return copy.deepcopy(self.report)

    def write_audit_event(self, event: Dict[str, Any]) -> None:
        """Append a JSONL audit event."""

        if self.policy and self.policy.get("audit_logging_enabled") is not True:
            return

        audit_event = {
            "timestamp_utc": self.utc_now_iso(),
            "organ": "NetworkCartographyOrgan",
            "build_behavior": "dry_run_only",
            "active_discovery_performed": False,
            "active_probes_sent": 0,
            **event,
        }

        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as file:
                json.dump(audit_event, file, sort_keys=False)
                file.write("\n")
        except OSError as error:
            raise CartographyAuditError(
                f"Could not write network cartography audit event: {error}"
            ) from error
