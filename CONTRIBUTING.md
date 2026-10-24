# Contributing

Thanks for helping! persianprobe is small on purpose: standard library only, no telemetry.

```sh
git clone https://github.com/mrzroot/persianprobe && cd persianprobe
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
python -m persianprobe --demo
```

Ground rules

- **No new runtime dependencies**, and Python 3.9 must keep working.
- **No false claims.** Every probe must state what a Persian-speaking user expects, show the real value each runtime returns, and say why. A new probe needs an adapter in at least two runtimes and a row in `probes.py` (idiom, expected value, why, fix).
- **Adapters use the idiom a developer would naturally write** (`parseInt(s)`, `int(s)`, `/\d/`, `len(s)`), never a workaround that happens to work.
- **Unsupported is not wrong.** A runtime that has no way to do a probe prints `n/a:<reason>`; it must not count as a disagreement.
- Tests must not need any runtime besides Python (tests for other runtimes are skipped when the runtime is missing).
- Add your change to `CHANGELOG.md`.
- Found a tool that already does this? Open an issue; it will be linked in the README and NOVELTY.md.
