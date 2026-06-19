# Digital-Organism-v3.2.0-Modular-Anatomy-Build
Digital Organism is a modular Python research prototype for experimenting with bounded software organisms, local memory, organ-based runtime behavior, substrate awareness, colony signaling, lineage tracking, and observatory-style metrics.

# Digital Organism

Digital Organism is a modular Python research prototype designed to explore how a bounded software organism can preserve identity, maintain memory, observe its local machine substrate, communicate with nearby local organisms, adapt over time, and produce measurable experiment data.

The project is structured around the idea of a software organism with a genome, state, memory, organs, substrate awareness, local colony signaling, and an observatory layer. It does not claim machine consciousness. Instead, it provides a testbed for studying continuity, divergence, adaptation, lineage, machine-environment awareness, and signal ecology inside a controlled local runtime.

The current build, **Digital Organism v3.2.0 — Modular Anatomy Build**, separates the system into editable parts: core identity and runtime, organs, memory, substrate mapping, colony routing, observatory metrics, and experiment definitions. The main launcher remains `organism.py`, while the organism body lives inside the `digital_organism/` package.

Key features include:

* Genome, identity hash, traits, drives, and permissions
* Stateful organism runtime with energy, health, stress, hormones, and focus
* Modular organs for perception, immune checks, metabolism, communication, mutation, reproduction, reflection, homeostasis, and substrate awareness
* Read-only machine and OS substrate mapping for Windows, Linux, macOS, BSD, and generic Unix-like systems
* Local-only colony messaging through inbox/outbox folders and a signal router
* Observatory experiments for measuring continuity, divergence, trait drift, signal activity, lineage, and machine-awareness behavior
* First experiment: **Continuity Under Divergence**
* Safety boundaries that prevent network scanning, packet capture, credential collection, privilege escalation, destructive commands, or uncontrolled self-spreading

This project is intended as an experimental framework for digital-organism theory, computational self-modeling, local machine-state awareness, and simulated software ecology.

Start with:
python organism.py --version
python organism.py init --root ./habitat --name "Seed Cell" --force
python organism.py run --root ./habitat --ticks 5

Then the experiment path:
python organism.py experiment-init --root ./ecosystem --scenario continuity_under_divergence --force
python organism.py experiment-run --root ./ecosystem --scenario continuity_under_divergence --rounds 25
python organism.py experiment-report --root ./ecosystem --scenario continuity_under_divergence
