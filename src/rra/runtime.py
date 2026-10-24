"""Runtime platform details recorded alongside reproducibility receipts."""
from __future__ import annotations

import platform
from pathlib import Path

import numpy as np


def runtime_versions() -> dict[str, object]:
    cpu_model = None
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    try:
        build = np.show_config(mode="dicts").get("Build Dependencies", {}).get("blas", {})
        blas = {key: build[key] for key in ("name", "version") if key in build}
        if not blas:
            blas = None
    except (AttributeError, TypeError, ValueError):
        blas = None
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "blas": blas,
    }
