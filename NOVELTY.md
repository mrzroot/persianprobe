# Novelty check: persianprobe

Done 2026-10-24 before building. Wording is deliberately modest: **no existing tool found as of October 2026** that runs
the *same* Persian-text probes through several programming runtimes and prints where they disagree; this is not a claim
that none exists anywhere.

What it does that was searched for: a cross-runtime *behaviour matrix* for Persian text (digits, `\d`/`\w`, length,
ی/ي equality, default sort, JSON encoding, normalization, Jalali/fa-IR formatting), as opposed to a normalization
*library* for one language.

## GitHub repository search queries (API, total results)

| query | total |
|---|---|
| `persian digits parseInt` | 0 |
| `persian digits compatibility` | 0 |
| `persian digits test` | 1 |
| `unicode digits runtime matrix` | 0 |
| `arabic-indic digits regex` | 0 |
| `persian digits python node` | 0 |
| `farsi numerals bug` | 0 |
| `persian probe` | 3 |
| `farsi probe` | 0 |
| `persian digits matrix` | 0 |
| `persian digits sqlite` | 0 |
| `persian unicode runtime differences` | 0 |
| `arabic yeh kaf matrix` | 0 |
| `persian locale test suite` | 0 |
| `fa-IR intl python node differences` | 0 |
| `persian sort order python` | 0 |
| `unicode text behavior matrix` | 0 |
| `persian text runtime` | 4 |
| `zwnj bug` | 0 |
| `zwnj detection` | 0 |
| `persian regex \w` | 0 |
| `persian sort collation` | 0 |
| `arabic yeh persian yeh database` | 0 |
| `persian normalize database` | 4 |
| `persian sql normalize` | 2 |

Search is AND-of-terms and noisy; most hits were unrelated. Also checked: name `persianprobe` is free on GitHub (for
this account), PyPI and npm.

## Closest existing work (all different in kind)

| project | what it is | difference |
|---|---|---|
| persian-normalize (npm) | normalizes Persian/Arabic text: ZWNJ, ي/ك, three digit sets, diacritics | a library for one runtime; does not compare runtimes |
| perso-match (GitHub) | Persian/Arabic search normalization with highlight ranges | a library for search |
| persian-tabular-cleaner, paksaz | clean Persian CSV / Excel data | data cleaning apps |
| anynum (npm) | any Unicode digit to ASCII | one function, one runtime |
| abzar-php | Persian utility toolkit for PHP | a library |
| hazm, parsivar and similar NLP toolkits (known from their documentation) | Persian NLP including normalizers | libraries; they assume you already chose Python |
| Unicode CLDR / ICU data and test suites | define the correct behaviour | specifications and data, not a per-machine runtime comparison |

The `xray` subcommand overlaps with the normalizers above; it is a small helper for *explaining* what is wrong with a
string, not the reason this project exists.

## Verdict

Distinct combination: **the same probes through every installed runtime + a machine-checked "expected" value + a
per-runtime fix**. The individual facts (Python's `int()` accepts Persian digits, JavaScript's `\d` does not) are known to
people who have been bitten; collecting them into one runnable, versioned matrix does not appear to exist. If you know of
one, please open an issue.

## Rejected during the same brainstorm (for the record)

- Cross-library Jalali date disagreement checker: jdatetime and persiantools agree 100 % with ICU for 1900-2100, so there is no real problem to solve.
- Database connection staged diagnoser: `holdon` already covers it.
- Flaky-test statistics, GRIM-style metric checks, McNemar CLIs, SMS segment calculators, Windows to Linux compatibility checkers: close tools exist.
