"""
H.E.R.E.T.I.C. — Host Environment for Realtime Embodiment, Tooling & Interactive Control.

The body does not contain the spirit. It receives it.

This package is the Python-side runtime for the HERETIC host environment. In v0.1 it
covers L0 Grunnr (config, logging, lifecycle, portable paths) and L1 Bifröst (agent
connection, Tailscale-aware routing, error hierarchy).

Layers exposed at package root:
    heretic.grunnr  — L0 Foundation
    heretic.bifrost — L1 Agent Connection

Version follows semantic versioning. The milestones in docs/ROADMAP.md map to minor
version numbers: v0.1 = First Communion, v0.2 = First Voice Out, etc.
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"
__all__ = ["__version__"]
