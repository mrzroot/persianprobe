<p align="center"><img src=".github/assets/banner.svg" alt="persianprobe: Does your language handle Persian text the way you think?" width="100%"></p>

<p align="center">
  <a href="https://github.com/mrzroot/persianprobe/releases"><img alt="Latest release" src="https://img.shields.io/github/v/release/mrzroot/persianprobe?style=flat-square"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/mrzroot/persianprobe?style=flat-square"></a>
  <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-3776ab?style=flat-square">
  <img alt="No dependencies" src="https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square">
  <a href="https://github.com/mrzroot/persianprobe/commits"><img alt="Last commit" src="https://img.shields.io/github/last-commit/mrzroot/persianprobe?style=flat-square"></a>
</p>

<p align="center"><a href="https://mrzroot.github.io/persianprobe/">Website</a> · <a href="README.fa.md">فارسی</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="CONTRIBUTING.md">Contributing</a></p>

# persianprobe

**Does your language handle Persian text the way you think it does?** `persianprobe` runs the *same* 14 probes (parse
`۱۲۳`, does `\d` match `۵`, how long is `نامه‌ها`, is `علی` equal to `علي`, how does `sort` order `ا ب پ ت`, how is it
written to JSON...) through every runtime installed on your machine (Python, Node, Bun, Perl, SQLite, jq, Go, awk) and prints
one table: what each one returns, what a Persian-speaking user expects, and where the runtimes disagree, with the fix for each.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

English | [فارسی](README.fa.md)

```text
$ persianprobe --runtimes python,node,sqlite,go --probes parse-int,digit-regex,length,equal-ye,sort-default
persianprobe 0.1.0 · LC_ALL=C.UTF-8
  python  Python 3.13.5
  node    v20.19.2
  sqlite  SQLite 3.46.1
  go      go version go1.27.3 linux/amd64

probe         expected       python            node              sqlite            go
-----------------------------------------------------------------------------------------------------
parse-int     123            123 ✓             NaN ✗             0 ✗               error ✗
digit-regex   true           true ✓            false ✗           false ✗           false ✗
length        7              7 ✓               7 ✓               7 ✓               15 ✗
equal-ye      true           false ✗           false ✗           false ✗           false ✗
sort-default  alef be pe te  alef be te pe ✗   alef be te pe ✗   alef be te pe ✗   alef be te pe ✗
```

(Persian values are shown as ASCII views so the table stays aligned in any terminal; `--raw` prints the raw values. The full,
unedited output of all 8 runtimes is in [docs/demo.txt](docs/demo.txt).)

## Why

Persian text breaks software quietly. The same validation regex passes in Python and fails in JavaScript; `parseInt("۱۲۳")` is
`NaN`, `int("۱۲۳")` is `123`, SQLite's `CAST` returns `0` without a word; a default `sort` puts `پ` after `ت`; Go's `len`
returns bytes; a user types `علي` (Arabic yeh) and your unique index now has two "علی". Each team rediscovers these one
bug report at a time, and AI coding assistants write the English-language version of the code. `persianprobe` puts the facts
for *your* installed versions in one place, produced by running real interpreters instead of quoting a blog post.

## Install

Python 3.9+, no dependencies. Tested on Linux; the other runtimes are optional and used when found on `PATH`. Windows and macOS are
not tested yet (the adapters are plain subprocess calls).

```sh
pipx install git+https://github.com/mrzroot/persianprobe      # PyPI release not published yet
uvx --from git+https://github.com/mrzroot/persianprobe persianprobe
pip install -e .                                              # from a clone
```

## Usage

```sh
persianprobe                                  # all probes, all runtimes found
persianprobe --runtimes python,node,sqlite    # only these
persianprobe --probes parse-int,sort-default  # only these probes
persianprobe --list                           # the probes and the exact idiom used per runtime
persianprobe --json                           # machine-readable
persianprobe --strict                         # exit 1 if any probe is a trap or wrong everywhere (CI)
persianprobe --raw                            # raw values instead of ASCII views
persianprobe --locale en_US.UTF-8             # LC_ALL for the child processes (default C.UTF-8)

persianprobe xray "علي  كتاب‌ها ٤٥٦"           # which characters are look-alike / invisible
persianprobe xray -f pasted.txt --fix --digits en   # also print the normalized text
```

## The probes

| probe | what it asks |
|---|---|
| `parse-int`, `parse-int-sep`, `parse-float-dot`, `parse-float-fa-sep` | parse `۱۲۳`, `۱٬۲۳۴`, `۱.۵`, `۱٫۵` with the runtime's own parser |
| `digit-regex`, `word-regex` | does `\d` match `۵`, does `\w` match `ک` |
| `length` | length of `نامه‌ها` (7 characters, 15 bytes) |
| `equal-ye` | is Persian `علی` equal to Arabic `علي` |
| `sort-default`, `sort-fa-locale` | sort `ت پ ب ا` with the default sort / the runtime's Persian collation |
| `json-encode` | does JSON keep `سلام` as UTF-8 or escape it |
| `nfkc` | does NFKC fold the presentation form `ﻻ` to `لا` |
| `jalali-format`, `number-format-fa` | Persian calendar date and `fa-IR` number formatting |

Each runtime uses the idiom a developer would naturally write (`parseInt(s)`, `int(s)`, `/\d/`, `len(s)`, `ORDER BY`), not a
workaround; `persianprobe --list` shows them. A probe that a runtime cannot do prints `n/a` and is **not** counted as a
disagreement. Verdicts: **portability traps** (some runtimes are right, some are wrong), **no runtime gets it right**, and
capability gaps (only some runtimes have it at all).

### `xray`

`persianprobe xray TEXT` lists, with positions and code points, the characters that look right but are not: Arabic `ي ى ك`, Arabic-Indic digits
(`٤٥٦` vs `۴۵۶`), tatweel, presentation forms from PDF/Word, invisible bidi marks, BOM, no-break spaces, mixed digit systems. `--fix`
prints a normalized copy (`--digits keep|fa|en`). The same function is available as a library: `from persianprobe.xray import normalize`.

### Use it as a step for agents

Paste [docs/AGENTS.snippet.md](docs/AGENTS.snippet.md) into `AGENTS.md` / `CLAUDE.md` / Cursor rules so an assistant checks Persian
behaviour before it writes the English-shaped version of a validator or a sort.

## Limits (please read)

- "Expected" is what a Persian-speaking user usually expects, which is a *judgement*. For example, `equal-ye` returning false is correct Unicode;
  it is listed because it surprises users and splits data. `json-encode` is a style preference more than a bug. Read `why:` before acting.
- It reports what the interpreters installed **on this machine** do, with `LC_ALL` set to `C.UTF-8` by default (Python runs with `-X utf8`).
  Other versions, locales or ICU builds can differ; change `--locale` and rerun.
- Ruby and PHP adapters are not provided (not available on the development machine, so they could not be tested). Adapters for more runtimes are welcome.
- `sort-fa-locale` for Python depends on an OS `fa_IR.UTF-8` locale, which most systems do not have: it shows `-`.
- SQLite is exercised through Python's `sqlite3` module (same engine, no `sqlite3` CLI needed).
- It runs only local interpreters, sends nothing over the network, and writes only to a temp directory.

## Development

```sh
pip install -e ".[test]" && pytest     # 25 tests; tests for other runtimes are skipped if they are missing
```

MIT licensed · by [Mohammadreza Zare (mrzroot)](https://github.com/mrzroot) · landing page: https://mrzroot.github.io/persianprobe/

## Contributing

Bug reports and ideas are welcome: open an [issue](../../issues/new/choose) (the templates ask for the steps and version we need). For code, read [CONTRIBUTING.md](CONTRIBUTING.md) first, keep each pull request to one change, and run the tests before you open it.

## License

MIT, see [LICENSE](LICENSE).
