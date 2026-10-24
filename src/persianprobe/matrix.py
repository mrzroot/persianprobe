"""Run every available runtime and compare against what a Persian-speaking user expects."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .adapters import Runtime, runtimes
from .probes import BY_ID, PROBES


@dataclass
class Cell:
    raw: str                 # raw value, or "n/a:reason" / "error" / "missing"
    status: str              # ok | miss | na | fail
    view: str = ""


@dataclass
class Result:
    versions: Dict[str, str] = field(default_factory=dict)
    cells: Dict[str, Dict[str, Cell]] = field(default_factory=dict)   # probe -> runtime -> Cell
    failed: Dict[str, str] = field(default_factory=dict)              # runtime -> error text
    locale: str = ""

    def verdict(self, probe_id: str) -> str:
        cs = [c for c in self.cells.get(probe_id, {}).values() if c.status in ("ok", "miss")]
        if not cs:
            return "n/a"
        ok = sum(c.status == "ok" for c in cs)
        if ok == len(cs):
            return "ok"
        if ok == 0:
            return "all-miss"
        return "disagree"


def parse(out: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for line in out.splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            d[k.strip()] = v.rstrip("\r")
    return d


def run(only: Optional[List[str]] = None, timeout: float = 30.0, locale: str = "C.UTF-8",
        rts: Optional[List[Runtime]] = None) -> Result:
    env = dict(os.environ, LC_ALL=locale, LANG=locale, PYTHONIOENCODING="utf-8")
    res = Result(locale=locale)
    for rt in (rts or runtimes()):
        if only and rt.key not in only:
            continue
        ver = rt.detect()
        if not ver:
            continue
        res.versions[rt.key] = ver
        try:
            data = parse(rt.run(timeout, env))
        except subprocess.TimeoutExpired:
            res.failed[rt.key] = f"timed out after {timeout:.0f}s"
            continue
        except Exception as e:
            res.failed[rt.key] = f"{type(e).__name__}: {e}"
            continue
        if not data:
            res.failed[rt.key] = "produced no output"
            continue
        for p in PROBES:
            if p.id not in p.idiom.keys() and rt.key not in p.idiom:
                continue
            raw = data.get(p.id)
            if raw is None:
                continue
            cells = res.cells.setdefault(p.id, {})
            if raw.startswith("n/a:"):
                cells[rt.key] = Cell(raw, "na", raw[4:])
            else:
                view = p.view(raw)
                status = "ok" if (view == (p.expect_view or p.expect)) or raw == p.expect else "miss"
                cells[rt.key] = Cell(raw, status, view)
    return res
