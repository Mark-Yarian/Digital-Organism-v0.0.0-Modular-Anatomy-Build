# Digital Organism v3.2.0 Architecture

v3.2.0 splits the prior single-file organism into a modular anatomy.

## Layers

```text
organism.py
  ↓
digital_organism.cli
  ↓
core runtime
  ↓
organs
  ↓
substrate / colony / observatory
```

## Primary edit points

- `digital_organism/core/genome.py`
- `digital_organism/core/state.py`
- `digital_organism/core/runtime.py`
- `digital_organism/organs/*.py`
- `digital_organism/substrate/command_catalog.py`
- `digital_organism/substrate/safety.py`
- `digital_organism/observatory/reports.py`
- `digital_organism/experiments/continuity_under_divergence.py`
