"""
============================================================
CORE IDENTITY ORGAN
============================================================

Project:
    Digital Organism

Build Compatibility:
    0.1.0 through 0.4.0

Organism Name:
    ContinuityNode

Primary Function:
    Maintain stable organism-level identity across executions while
    generating a unique runtime identity for each individual launch.

Locked Field Rule:
    The identity organ should never overwrite locked fields unless
    a future reset_identity() method is explicitly added.

    No reset_identity() method exists in this build.
"""

from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class CoreIdentityError(Exception):
    """Base exception for all Core Identity Organ errors."""


class IdentityLoadError(CoreIdentityError):
    """Raised when the persistent identity file cannot be loaded."""


class IdentityValidationError(CoreIdentityError):
    """Raised when persistent identity data is invalid."""


class IdentityUpdateError(CoreIdentityError):
    """Raised when an identity update violates safety rules."""


class CoreIdentityOrgan:
    """
    Maintains persistent and runtime identity for ContinuityNode.

    Persistent identity:
        Stored in data/identity.json.

    Runtime identity:
        Created fresh every program launch and kept in memory.

    This organ does not:
        - scan the host machine
        - execute shell commands
        - access the network
        - modify unrelated files
    """

    SCHEMA_VERSION = "1.0.0"
    ORGANISM_TYPE = "experimental_software_and_digital_organism_research_model"
    DEFAULT_DESCRIPTION = (
        "ContinuityNode is an experimental software system and digital "
        "organism research model designed to study persistent identity, "
        "runtime instancing, continuity tracking, and controlled divergence "
        "across executions."
    )

    REQUIRED_TOP_LEVEL_FIELDS = [
        "schema_version",
        "organism_name",
        "organism_type",
        "description",
        "birth_timestamp_utc",
        "lineage_id",
        "first_build",
        "current_build",
        "default_runtime_mode",
        "created_by",
        "created_with",
        "identity_locked_fields",
        "allowed_runtime_modes",
        "safety_boundary",
        "last_identity_validation_utc",
    ]

    REQUIRED_SAFETY_FLAGS = [
        "may_create_identity_file",
        "may_update_current_build",
        "may_update_description",
        "may_generate_runtime_instance_id",
        "may_execute_shell_commands",
        "may_access_network",
        "may_modify_unrelated_files",
        "may_scan_environment",
    ]

    RUNTIME_ONLY_FIELDS = [
        "runtime_instance_id",
        "runtime_started_utc",
        "active_mode",
        "runtime",
        "session",
        "events",
        "logs",
        "machine_state",
        "command_results",
    ]

    DEFAULT_LOCKED_FIELDS = [
        "organism_name",
        "birth_timestamp_utc",
        "lineage_id",
        "first_build",
    ]

    DEFAULT_ALLOWED_RUNTIME_MODES = [
        "OBSERVE",
        "DIAGNOSTIC",
        "EXPERIMENTAL",
        "MAINTENANCE",
        "REPLICATION_TEST",
    ]

    def __init__(
        self,
        identity_path: str = "data/identity.json",
        build_version: str = "0.4.0",
        default_name: str = "ContinuityNode",
        default_mode: str = "OBSERVE",
    ) -> None:
        """Initialize identity, validate it, and create runtime identity."""

        self.identity_path = Path(identity_path)
        self.build_version = build_version
        self.default_name = default_name
        self.default_mode = default_mode.upper()

        self.identity: Dict[str, Any] = {}
        self.runtime: Dict[str, Any] = {}

        self.identity = self.ensure_identity_file()
        self.validate_identity(self.identity)

        if self.identity.get("current_build") != self.build_version:
            self.update_current_build(self.build_version)

        self.update_validation_timestamp()
        self.runtime = self.create_runtime_identity(mode=self.default_mode)

    def utc_now_iso(self) -> str:
        """Return the current UTC timestamp in ISO-8601 Z format."""

        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def generate_lineage_id(self) -> str:
        """Generate a stable lineage ID for first identity creation."""

        return f"cn-lineage-{uuid.uuid4().hex[:12]}"

    def generate_runtime_instance_id(self) -> str:
        """Generate a unique runtime ID for this execution."""

        if not self.identity.get("safety_boundary", {}).get("may_generate_runtime_instance_id", False):
            raise IdentityUpdateError(
                "Runtime instance ID generation is not permitted by the identity safety boundary."
            )

        timestamp = self.utc_now_iso().replace("-", "").replace(":", "").replace("Z", "Z")
        short_id = uuid.uuid4().hex[:6]
        return f"cn-run-{timestamp}-{short_id}"

    def ensure_identity_file(self) -> Dict[str, Any]:
        """Load identity.json if present, otherwise create it."""

        if self.identity_path.exists():
            return self.load_identity()

        identity = self.create_default_identity()

        if not identity["safety_boundary"].get("may_create_identity_file", False):
            raise IdentityUpdateError(
                "Default identity safety boundary does not permit identity file creation."
            )

        self.save_identity(identity)
        return identity

    def create_default_identity(self) -> Dict[str, Any]:
        """Create a new persistent identity dictionary."""

        now = self.utc_now_iso()

        return {
            "schema_version": self.SCHEMA_VERSION,
            "organism_name": self.default_name,
            "organism_type": self.ORGANISM_TYPE,
            "description": self.DEFAULT_DESCRIPTION,
            "birth_timestamp_utc": now,
            "lineage_id": self.generate_lineage_id(),
            "first_build": self.build_version,
            "current_build": self.build_version,
            "default_runtime_mode": self.default_mode,
            "created_by": "User",
            "created_with": "Python",
            "identity_locked_fields": list(self.DEFAULT_LOCKED_FIELDS),
            "allowed_runtime_modes": list(self.DEFAULT_ALLOWED_RUNTIME_MODES),
            "safety_boundary": {
                "may_create_identity_file": True,
                "may_update_current_build": True,
                "may_update_description": True,
                "may_generate_runtime_instance_id": True,
                "may_execute_shell_commands": False,
                "may_access_network": False,
                "may_modify_unrelated_files": False,
                "may_scan_environment": False,
            },
            "last_identity_validation_utc": None,
        }

    def load_identity(self) -> Dict[str, Any]:
        """Load persistent identity from disk."""

        try:
            with self.identity_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

        except json.JSONDecodeError as error:
            raise IdentityLoadError(
                f"identity.json exists but could not be parsed as valid JSON: {error}"
            ) from error

        except OSError as error:
            raise IdentityLoadError(
                f"identity.json exists but could not be read: {error}"
            ) from error

        if not isinstance(data, dict):
            raise IdentityLoadError("identity.json must contain a JSON object.")

        return data

    def save_identity(self, identity: Dict[str, Any]) -> None:
        """Save persistent identity to disk."""

        self.reject_runtime_fields(identity)

        try:
            self.identity_path.parent.mkdir(parents=True, exist_ok=True)
            with self.identity_path.open("w", encoding="utf-8") as file:
                json.dump(identity, file, indent=2, sort_keys=False)
                file.write("\n")

        except OSError as error:
            raise IdentityUpdateError(f"Could not save identity file: {error}") from error

    def reject_runtime_fields(self, identity: Dict[str, Any]) -> None:
        """Prevent runtime-only fields from being saved to identity.json."""

        for field in self.RUNTIME_ONLY_FIELDS:
            if field in identity:
                raise IdentityUpdateError(
                    f"Refusing to save runtime-only field to identity.json: {field}"
                )

    def validate_identity(self, identity: Dict[str, Any]) -> bool:
        """Validate the persistent identity structure."""

        if not isinstance(identity, dict):
            raise IdentityValidationError("Identity data must be a dictionary.")

        for field in self.REQUIRED_TOP_LEVEL_FIELDS:
            if field not in identity:
                raise IdentityValidationError(f"Missing required identity field: {field}")

        for field in self.RUNTIME_ONLY_FIELDS:
            if field in identity:
                raise IdentityValidationError(
                    f"Runtime-only field found in persistent identity: {field}"
                )

        locked_fields = identity.get("identity_locked_fields")
        if not isinstance(locked_fields, list):
            raise IdentityValidationError("identity_locked_fields must be a list.")

        for field in self.DEFAULT_LOCKED_FIELDS:
            if field not in locked_fields:
                raise IdentityValidationError(
                    f"Continuity-critical field is missing from identity_locked_fields: {field}"
                )

        for field in locked_fields:
            if field not in identity:
                raise IdentityValidationError(
                    f"Locked field is listed but missing from identity: {field}"
                )

        allowed_modes = identity.get("allowed_runtime_modes")
        if not isinstance(allowed_modes, list) or not allowed_modes:
            raise IdentityValidationError("allowed_runtime_modes must be a non-empty list.")

        allowed_modes_upper = [str(mode).upper() for mode in allowed_modes]
        default_mode = str(identity.get("default_runtime_mode")).upper()

        if default_mode not in allowed_modes_upper:
            raise IdentityValidationError(
                f"default_runtime_mode is not allowed: {identity.get('default_runtime_mode')}"
            )

        safety_boundary = identity.get("safety_boundary")
        if not isinstance(safety_boundary, dict):
            raise IdentityValidationError("safety_boundary must be a dictionary.")

        for flag in self.REQUIRED_SAFETY_FLAGS:
            if flag not in safety_boundary:
                raise IdentityValidationError(f"Missing required safety boundary flag: {flag}")
            if not isinstance(safety_boundary[flag], bool):
                raise IdentityValidationError(f"Safety boundary flag must be boolean: {flag}")

        for flag in [
            "may_execute_shell_commands",
            "may_access_network",
            "may_modify_unrelated_files",
            "may_scan_environment",
        ]:
            if safety_boundary.get(flag) is True:
                raise IdentityValidationError(
                    f"Core Identity Organ safety boundary violation. This flag must be false: {flag}"
                )

        return True

    def update_validation_timestamp(self) -> None:
        """Update last successful identity validation timestamp."""

        self.identity["last_identity_validation_utc"] = self.utc_now_iso()
        self.save_identity(self.identity)

    def create_runtime_identity(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Create the runtime identity object for this execution."""

        requested_mode = (mode or self.identity["default_runtime_mode"]).upper()

        if requested_mode not in self.get_allowed_modes_upper():
            raise IdentityValidationError(f"Requested runtime mode is not allowed: {requested_mode}")

        return {
            "runtime_instance_id": self.generate_runtime_instance_id(),
            "runtime_started_utc": self.utc_now_iso(),
            "active_mode": requested_mode,
            "source_lineage_id": self.identity["lineage_id"],
            "source_organism_name": self.identity["organism_name"],
            "build": self.identity["current_build"],
        }

    def set_runtime_mode(self, mode: str) -> None:
        """Change active runtime mode for this execution only."""

        normalized_mode = mode.upper()

        if normalized_mode not in self.get_allowed_modes_upper():
            raise IdentityValidationError(f"Cannot set runtime mode. Mode is not allowed: {mode}")

        self.runtime["active_mode"] = normalized_mode

    def get_allowed_modes_upper(self) -> list[str]:
        """Return allowed runtime modes normalized to uppercase."""

        return [str(mode).upper() for mode in self.identity["allowed_runtime_modes"]]

    def get_persistent_identity(self) -> Dict[str, Any]:
        """Return a deep copy of persistent identity."""

        return copy.deepcopy(self.identity)

    def get_runtime_identity(self) -> Dict[str, Any]:
        """Return a deep copy of runtime identity."""

        return copy.deepcopy(self.runtime)

    def get_identity_report(self) -> Dict[str, Any]:
        """Return a structured identity report."""

        return {
            "persistent": {
                "organism_name": self.identity["organism_name"],
                "lineage_id": self.identity["lineage_id"],
                "birth_timestamp_utc": self.identity["birth_timestamp_utc"],
                "first_build": self.identity["first_build"],
                "current_build": self.identity["current_build"],
            },
            "runtime": {
                "runtime_instance_id": self.runtime["runtime_instance_id"],
                "runtime_started_utc": self.runtime["runtime_started_utc"],
                "active_mode": self.runtime["active_mode"],
            },
            "classification": {
                "organism_type": self.identity["organism_type"],
                "description": self.identity["description"],
            },
            "safety_boundary": copy.deepcopy(self.identity["safety_boundary"]),
        }

    def update_current_build(self, new_build: str) -> None:
        """Update current_build while preserving first_build."""

        if not self.identity["safety_boundary"].get("may_update_current_build", False):
            raise IdentityUpdateError("Updating current_build is not permitted.")

        if self.is_locked_field("current_build"):
            raise IdentityUpdateError("current_build is unexpectedly locked and cannot be updated.")

        self.identity["current_build"] = new_build
        self.validate_identity(self.identity)
        self.save_identity(self.identity)

    def update_description(self, new_description: str) -> None:
        """Update the human-readable scientific description."""

        if not self.identity["safety_boundary"].get("may_update_description", False):
            raise IdentityUpdateError("Updating description is not permitted.")

        if self.is_locked_field("description"):
            raise IdentityUpdateError("description is locked and cannot be updated.")

        self.identity["description"] = new_description
        self.validate_identity(self.identity)
        self.save_identity(self.identity)

    def is_locked_field(self, field_name: str) -> bool:
        """Check whether an identity field is locked."""

        return field_name in self.identity.get("identity_locked_fields", [])

    def attempt_identity_update(self, field_name: str, value: Any) -> bool:
        """Attempt a controlled update to a persistent identity field."""

        if field_name in self.RUNTIME_ONLY_FIELDS:
            raise IdentityUpdateError(
                f"Cannot update runtime-only field in persistent identity: {field_name}"
            )

        if field_name not in self.identity:
            raise IdentityUpdateError(f"Cannot update unknown identity field: {field_name}")

        if self.is_locked_field(field_name):
            return False

        if field_name in ["safety_boundary", "identity_locked_fields", "allowed_runtime_modes"]:
            raise IdentityUpdateError(
                f"{field_name} cannot be updated through attempt_identity_update()."
            )

        self.identity[field_name] = value
        self.validate_identity(self.identity)
        self.save_identity(self.identity)

        return True

    def compare_locked_fields_before_update(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> None:
        """Ensure locked fields were not changed as a side effect."""

        locked_fields = before.get("identity_locked_fields", [])

        for field in locked_fields:
            if before.get(field) != after.get(field):
                raise IdentityUpdateError(
                    f"Locked identity field was modified without reset_identity(): {field}"
                )
