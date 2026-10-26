from __future__ import annotations

import json
from typing import List, Optional

from . import __version__
from .matrix import Result
from .probes import PROBES

MARK = {"ok": "✓", "miss": "✗", "na": "–"}
RT_ORDER = ["python", "node", "bun", "perl", "sqlite", "jq", "go", "awk"]


def _pad(s: str, w: int) -> str:
    return s + " " * max(0, w - len(s))


def _c(txt: str, code: str, on: bool) -> str:
    return f"\033[{code}m{txt}\033[0m" if on else txt


def text(res: Result, raw: bool = False, color: bool = False, only_probes: Optional[List[str]] = None) -> str:
    rts = [k for k in RT_ORDER if k in res.versions and k not in res.failed]
    probes = [p for p in PROBES if p.id in res.cells and (not only_probes or p.id in only_probes)]
    out = [f"persianprobe {__version__} · LC_ALL={res.locale}"]
    for k in RT_ORDER:
        if k in res.versions:
            out.append(f"  {k:<7} {res.versions[k]}" + (f"   FAILED: {res.failed[k]}" if k in res.failed else ""))
    out.append("")
    w0 = max(len(p.id) for p in probes) + 2
    w1 = max(len(p.expect_view or p.expect) for p in probes) + 2
    ws = {k: max(len(k), max((len((res.cells[p.id].get(k).raw if raw else res.cells[p.id].get(k).view) if res.cells[p.id].get(k) and res.cells[p.id][k].status != "na" else "-") + 4 for p in probes), default=2)) + 1 for k in rts}
    head = _pad("probe", w0) + _pad("expected", w1) + "".join(_pad(k, ws[k]) for k in rts)
    out.append(head)
    out.append("-" * len(head))
    for p in probes:
        row = _pad(p.id, w0) + _pad(p.expect_view or p.expect, w1)
        for k in rts:
            c = res.cells[p.id].get(k)
            if c is None or c.status == "na":
                cell = "-"
            else:
                cell = (c.raw if raw else c.view) + " " + MARK[c.status]
            if c is not None and c.status == "miss":
                row += _c(_pad(cell, ws[k]), "31", color)
            elif c is not None and c.status == "ok":
                row += _c(_pad(cell, ws[k]), "32", color)
            else:
                row += _pad(cell, ws[k])
        out.append(row.rstrip())
    out.append("")
    out.append("✓ matches what a Persian-speaking user expects · ✗ does not · - not available in that runtime")
    out.append("")

    traps = [p for p in probes if res.verdict(p.id) == "disagree"]
    allmiss = [p for p in probes if res.verdict(p.id) == "all-miss"]
    rest = [p for p in probes if res.verdict(p.id) == "ok"]
    out.append(f"{len(probes)} probes · {len(traps)} portability traps (runtimes disagree) · {len(allmiss)} that no runtime gets right · {len(rest)} fine where available")
    out.append("")
    for title, group, tag in (("PORTABILITY TRAPS: the same code gives different answers", traps, "disagree"),
                              ("NO RUNTIME GETS IT RIGHT: you must handle it yourself", allmiss, "all-miss")):
        if not group:
            continue
        out.append(_c(f"{title} [{len(group)}]", "33", color))
        out.append("")
        for p in group:
            cs = res.cells[p.id]
            ok = [k for k in rts if k in cs and cs[k].status == "ok"]
            bad = [k for k in rts if k in cs and cs[k].status == "miss"]
            out.append(f"✗ {p.id} · {p.title}")
            if ok:
                out.append(f"    right:  {', '.join(ok)}")
            out.append(f"    wrong:  {', '.join(bad)}")
            out.append(f"    why:    {p.why}")
            seen = {}
            for k in bad:
                snip = p.fix.get(k) or p.fix.get("*")
                if snip:
                    seen.setdefault(snip, []).append(k)
            first = True
            for snip, ks in seen.items():
                lab = "fix:    " if first else "        "
                first = False
                lines = snip.split("\n")
                out.append(f"    {lab}[{', '.join(ks) if snip != p.fix.get('*') or len(seen) > 1 else 'all'}] {lines[0]}")
                for extra in lines[1:]:
                    out.append(f"            {extra}")
            out.append("")
    gaps = [(p, [k for k in rts if k in res.cells[p.id] and res.cells[p.id][k].status == "na"]) for p in probes if res.verdict(p.id) == "ok"]
    gaps = [(p, g) for p, g in gaps if g]
    if gaps:
        out.append("CAPABILITY GAPS: fine where it exists, missing elsewhere")
        out.append("")
        for p, g in gaps:
            out.append(f"· {p.id}: not built in for {', '.join(g)}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def as_json(res: Result) -> str:
    data = {"tool": "persianprobe", "version": __version__, "locale": res.locale, "runtimes": res.versions, "failed": res.failed, "probes": []}
    for p in PROBES:
        if p.id not in res.cells:
            continue
        data["probes"].append({"id": p.id, "title": p.title, "expected": p.expect, "verdict": res.verdict(p.id),
                               "results": {k: {"value": c.raw, "status": c.status} for k, c in res.cells[p.id].items()}})
    return json.dumps(data, indent=2, ensure_ascii=False)


def listing() -> str:
    out = []
    for p in PROBES:
        out.append(f"{p.id}: {p.title}  (expected: {p.expect_view or p.expect})")
        for k, v in p.idiom.items():
            out.append(f"    {k:<7} {v}")
    return "\n".join(out) + "\n"
