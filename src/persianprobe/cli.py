from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__, matrix, render, xray
from .probes import BY_ID


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "xray":
        ap = argparse.ArgumentParser(prog="persianprobe xray", description="X-ray a Persian string: look-alike and invisible characters.")
        ap.add_argument("text", nargs="?", help="the text ('-' reads stdin)")
        ap.add_argument("-f", "--file", help="read the text from a UTF-8 file")
        ap.add_argument("--fix", action="store_true", help="also print the normalized text")
        ap.add_argument("--digits", choices=["keep", "fa", "en"], default="keep", help="with --fix: Persian or ASCII digits")
        a = ap.parse_args(argv[1:])
        if a.file:
            s = open(a.file, encoding="utf-8").read().rstrip("\n")
        elif a.text == "-" or (a.text is None and not sys.stdin.isatty()):
            s = sys.stdin.read().rstrip("\n")
        elif a.text is not None:
            s = a.text
        else:
            ap.error("give some text, -f FILE, or pipe it in")
        sys.stdout.write(xray.render(s, fix=a.fix, digits=a.digits))
        return 0

    ap = argparse.ArgumentParser(prog="persianprobe", description=(
        "Run the same Persian-text probes through every runtime on this machine and show where they disagree. "
        "Use `persianprobe xray TEXT` to inspect a string."))
    ap.add_argument("--runtimes", help="comma list, e.g. python,node,sqlite (default: all found)")
    ap.add_argument("--probes", help="comma list of probe ids (see --list)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--raw", action="store_true", help="show raw values instead of ASCII-safe views")
    ap.add_argument("--locale", default="C.UTF-8", help="LC_ALL for the child processes (default C.UTF-8)")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--list", action="store_true", help="list the probes and the idiom used per runtime")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any probe is a trap or is wrong everywhere")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--version", action="version", version=f"persianprobe {__version__}")
    a = ap.parse_args(argv)
    if a.list:
        sys.stdout.write(render.listing())
        return 0
    only = [x.strip() for x in a.runtimes.split(",")] if a.runtimes else None
    pids = [x.strip() for x in a.probes.split(",")] if a.probes else None
    if pids:
        bad = [p for p in pids if p not in BY_ID]
        if bad:
            ap.error("unknown probe(s): " + ", ".join(bad) + " (see --list)")
    res = matrix.run(only=only, timeout=a.timeout, locale=a.locale)
    if not res.versions:
        sys.stderr.write("no runtime found\n")
        return 2
    color = sys.stdout.isatty() and not a.no_color
    sys.stdout.write((render.as_json(res) + "\n") if a.json else render.text(res, raw=a.raw, color=color, only_probes=pids))
    if a.strict and any(res.verdict(p) in ("disagree", "all-miss") for p in res.cells):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
