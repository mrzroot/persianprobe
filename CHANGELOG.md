# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-24

First release.

### Added
- `persianprobe`: 14 probes run through python, node, bun, perl, sqlite, jq, go and awk (whatever is installed): Persian/Arabic digits, separators, `\d`/`\w`, length, ی/ي, sorting, JSON encoding, NFKC, Jalali and fa-IR formatting.
- Verdicts: portability traps (runtimes disagree) and "no runtime gets it right", each with a per-runtime fix.
- `persianprobe xray TEXT [--fix]`: look-alike and invisible characters in a string, and a normalized copy.
- `--json`, `--raw`, `--strict`, `--list`, `--locale`, `--runtimes`, `--probes`.
