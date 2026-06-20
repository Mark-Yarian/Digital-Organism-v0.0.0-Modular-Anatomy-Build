"""
============================================================
ORGANS PACKAGE
============================================================

This package contains modular software organs for the Digital Organism
project.

Current Build:
    0.4.0

Current Organism:
    ContinuityNode

Current organs:

    core_identity.py
        Maintains persistent identity and runtime identity.

    sensorium.py
        Collects a safe runtime/environment snapshot and passive
        network topology seed matrix.

    network_cartography.py
        Prepares controlled active network discovery plans using
        approved scopes, strict safety policy, and audit logs.

Design Rule:
    Each organ should have:
        - a clearly defined responsibility
        - explicit input and output boundaries
        - controlled state behavior
        - documented safety limits
        - minimal coupling to other organs

Future organs may include:

    memory.py
        Stores structured internal records and observations.

    event_bus.py
        Routes internal organism events.

    metabolism.py
        Manages runtime cycles and heartbeat behavior.

    reflex.py
        Handles safe automatic responses.

    immune.py
        Enforces safety rules and action boundaries.

    tool_use.py
        Executes approved tools through explicit safety gates.

    telemetry.py
        Tracks runtime metrics and organism health.

    interface.py
        Provides CLI, dashboard, or user-facing control surfaces.
"""

__all__ = [
    "core_identity",
    "sensorium",
    "network_cartography",
]
