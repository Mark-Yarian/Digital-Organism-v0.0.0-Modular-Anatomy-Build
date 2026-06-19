# Digital Organism v3.2.0 — Modular Anatomy Build

This is the modular split of the Digital Organism program.

## Quick run

```bash
python organism.py --version
python organism.py init --root ./habitat --name "Seed Cell" --force
python organism.py run --root ./habitat --ticks 5
python organism.py status --root ./habitat
```

## Read-only substrate mapping

```bash
python organism.py substrate-map --root ./habitat
```

Trace commands are gated:

```bash
python organism.py substrate-map --root ./habitat --allow-trace --trace-target example.com
```

## Experiment

```bash
python organism.py experiment-init --root ./ecosystem --scenario continuity_under_divergence --force
python organism.py experiment-run --root ./ecosystem --scenario continuity_under_divergence --rounds 25
python organism.py experiment-report --root ./ecosystem --scenario continuity_under_divergence
```

## Layout

```text
organism.py                      launcher
digital_organism/build.py        build metadata
digital_organism/core/           genome, state, runtime, utilities
digital_organism/memory/         memory store
digital_organism/organs/         organism organs
digital_organism/substrate/      read-only machine mapping
digital_organism/colony/         local signal routing
digital_organism/observatory/    metrics/reports/lineage/signal graph
digital_organism/experiments/    experiment definitions
digital_organism/cli/            command-line interface
```

## Safety boundary

The substrate mapper is read-only by default. It does not change routes, firewall rules, services, package managers, files, users, credentials, or OS settings.
