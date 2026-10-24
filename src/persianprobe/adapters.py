"""One small program per runtime. Each prints `probe-id<TAB>value` lines.

Every program implements the *idiom a developer would naturally write* for the
probe (``int(s)``, ``parseInt(s)``, ``/\\d/``, ``len(s)`` ...), not a workaround.
Unsupported probes print ``n/a:<reason>``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

# ------------------------------------------------------------------ python
PYTHON = r'''
import re, json, unicodedata, locale, sys
def out(i, v): print(i + "\t" + str(v))
def b(x): return "true" if x else "false"
def t(i, f):
    try: out(i, f())
    except Exception: out(i, "error")
t("parse-int", lambda: int("۱۲۳"))
t("parse-int-sep", lambda: int("۱٬۲۳۴"))
t("parse-float-dot", lambda: float("۱.۵"))
t("parse-float-fa-sep", lambda: float("۱٫۵"))
t("digit-regex", lambda: b(re.match(r"\d", "۵")))
t("word-regex", lambda: b(re.match(r"\w", "ک")))
t("length", lambda: len("نامه\u200cها"))
t("equal-ye", lambda: b("علی" == "علي"))
t("sort-default", lambda: " ".join(sorted(["ت", "پ", "ب", "ا"])))
def fa():
    try:
        locale.setlocale(locale.LC_COLLATE, "fa_IR.UTF-8")
    except Exception:
        return "n/a:no fa_IR locale installed"
    return " ".join(sorted(["ت", "پ", "ب", "ا"], key=locale.strxfrm))
t("sort-fa-locale", fa)
t("json-encode", lambda: json.dumps("سلام"))
t("nfkc", lambda: unicodedata.normalize("NFKC", "\ufefb"))
out("jalali-format", "n/a:no Persian calendar in the standard library")
out("number-format-fa", "n/a:no fa-IR number formatting in the standard library")
'''

# ---------------------------------------------------------------- node/bun
JS = r'''
const out = (i, v) => console.log(i + "\t" + v);
const t = (i, f) => { try { out(i, f()); } catch (e) { out(i, "error"); } };
t("parse-int", () => parseInt("۱۲۳"));
t("parse-int-sep", () => parseInt("۱٬۲۳۴"));
t("parse-float-dot", () => parseFloat("۱.۵"));
t("parse-float-fa-sep", () => parseFloat("۱٫۵"));
t("digit-regex", () => /\d/.test("۵"));
t("word-regex", () => /\w/.test("ک"));
t("length", () => "نامه\u200cها".length);
t("equal-ye", () => "علی" === "علي");
t("sort-default", () => ["ت", "پ", "ب", "ا"].sort().join(" "));
t("sort-fa-locale", () => ["ت", "پ", "ب", "ا"].sort(new Intl.Collator("fa").compare).join(" "));
t("json-encode", () => JSON.stringify("سلام"));
t("nfkc", () => "\ufefb".normalize("NFKC"));
t("jalali-format", () => new Intl.DateTimeFormat("fa-IR", {timeZone: "UTC", year: "numeric", month: "numeric", day: "numeric"}).format(new Date(Date.UTC(2026, 9, 24, 12))));
t("number-format-fa", () => (1234567.5).toLocaleString("fa-IR"));
'''

# -------------------------------------------------------------------- perl
PERL = r'''
use utf8; use strict; no warnings;
binmode(STDOUT, ":utf8");
use Unicode::Normalize; use JSON::PP; use Unicode::Collate::Locale;
sub o { print "$_[0]\t$_[1]\n" }
sub b { $_[0] ? "true" : "false" }
o("parse-int", "۱۲۳" + 0);
o("parse-int-sep", "۱٬۲۳۴" + 0);
o("parse-float-dot", "۱.۵" + 0);
o("parse-float-fa-sep", "۱٫۵" + 0);
o("digit-regex", b("۵" =~ /\d/));
o("word-regex", b("ک" =~ /\w/));
o("length", length("نامه\x{200c}ها"));
o("equal-ye", b("علی" eq "علي"));
o("sort-default", join(" ", sort ("ت", "پ", "ب", "ا")));
my $c = eval { Unicode::Collate::Locale->new(locale => "fa") };
o("sort-fa-locale", $c ? join(" ", $c->sort("ت", "پ", "ب", "ا")) : "n/a:Unicode::Collate::Locale has no fa");
o("json-encode", JSON::PP->new->allow_nonref->encode("سلام"));
o("nfkc", NFKC("\x{fefb}"));
o("jalali-format", "n/a:no Persian calendar in core Perl");
o("number-format-fa", "n/a:no fa-IR number formatting in core Perl");
'''

# ------------------------------------------------------------------ sqlite
SQLITE_SQL = [
    ("parse-int", "SELECT CAST('۱۲۳' AS INTEGER)"),
    ("parse-int-sep", "SELECT CAST('۱٬۲۳۴' AS INTEGER)"),
    ("parse-float-dot", "SELECT CAST('۱.۵' AS REAL)"),
    ("parse-float-fa-sep", "SELECT CAST('۱٫۵' AS REAL)"),
    ("digit-regex", "SELECT '۵' GLOB '[0-9]'"),
    ("length", "SELECT length('نامه' || char(8204) || 'ها')"),
    ("equal-ye", "SELECT 'علی' = 'علي'"),
    ("json-encode", "SELECT json_quote('سلام')"),
]

# --------------------------------------------------------------------- jq
JQ = r'''
def t(i; f): "\(i)\t" + (try (f | tostring) catch "error");
t("parse-int"; "۱۲۳" | tonumber),
t("parse-int-sep"; "۱٬۲۳۴" | tonumber),
t("parse-float-dot"; "۱.۵" | tonumber),
t("parse-float-fa-sep"; "۱٫۵" | tonumber),
t("digit-regex"; "۵" | test("\\d")),
t("word-regex"; "ک" | test("\\w")),
t("length"; "نامه\u200cها" | length),
t("equal-ye"; "علی" == "علي"),
t("sort-default"; ["ت", "پ", "ب", "ا"] | sort | join(" ")),
"sort-fa-locale\tn/a:jq has no collation",
t("json-encode"; "سلام" | tojson),
"nfkc\tn/a:jq has no Unicode normalization",
"jalali-format\tn/a:jq strftime is Gregorian only",
"number-format-fa\tn/a:jq has no locale formatting"
'''

# --------------------------------------------------------------------- go
GO = r'''package main

import (
	"encoding/json"
	"fmt"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

func o(id string, v interface{}) { fmt.Printf("%s\t%v\n", id, v) }

func main() {
	if v, err := strconv.Atoi("۱۲۳"); err == nil { o("parse-int", v) } else { o("parse-int", "error") }
	if v, err := strconv.Atoi("۱٬۲۳۴"); err == nil { o("parse-int-sep", v) } else { o("parse-int-sep", "error") }
	if v, err := strconv.ParseFloat("۱.۵", 64); err == nil { o("parse-float-dot", v) } else { o("parse-float-dot", "error") }
	if v, err := strconv.ParseFloat("۱٫۵", 64); err == nil { o("parse-float-fa-sep", v) } else { o("parse-float-fa-sep", "error") }
	m, _ := regexp.MatchString(`\d`, "۵")
	o("digit-regex", m)
	w, _ := regexp.MatchString(`\w`, "ک")
	o("word-regex", w)
	o("length", len("نامه\u200cها"))
	o("equal-ye", "علی" == "علي")
	l := []string{"ت", "پ", "ب", "ا"}
	sort.Strings(l)
	o("sort-default", strings.Join(l, " "))
	o("sort-fa-locale", "n/a:needs golang.org/x/text/collate (not in the standard library)")
	j, _ := json.Marshal("سلام")
	o("json-encode", string(j))
	o("nfkc", "n/a:needs golang.org/x/text/unicode/norm (not in the standard library)")
	o("jalali-format", "n/a:no Persian calendar in the standard library")
	o("number-format-fa", "n/a:no fa-IR number formatting in the standard library")
}
'''

# -------------------------------------------------------------------- mawk
AWK = r'''BEGIN {
  zw = "\342\200\214"
  print "parse-int\t" ("۱۲۳" + 0)
  print "parse-int-sep\t" ("۱٬۲۳۴" + 0)
  print "parse-float-dot\t" ("۱.۵" + 0)
  print "parse-float-fa-sep\t" ("۱٫۵" + 0)
  print "digit-regex\t" (("۵" ~ /[0-9]/) ? "true" : "false")
  print "word-regex\tn/a:awk has no \\w (POSIX classes depend on locale)"
  print "length\t" length("نامه" zw "ها")
  print "equal-ye\t" (("علی" == "علي") ? "true" : "false")
  print "sort-default\tn/a:awk has no sort"
  print "sort-fa-locale\tn/a:awk has no collation"
  print "json-encode\tn/a:awk has no JSON"
  print "nfkc\tn/a:awk has no Unicode normalization"
  print "jalali-format\tn/a:no Persian calendar in awk"
  print "number-format-fa\tn/a:no fa-IR number formatting in awk"
}
'''


@dataclass
class Runtime:
    key: str
    label: str
    detect: Callable[[], Optional[str]]          # returns version string or None
    run: Callable[[float, Dict[str, str]], str]  # returns stdout


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _sh(args: List[str], timeout: float, env: Dict[str, str], inp: Optional[str] = None) -> str:
    p = subprocess.run(args, input=inp, capture_output=True, timeout=timeout, env=env)
    return p.stdout.decode("utf-8", "replace")


def _first(cmd: List[str], env=None) -> Optional[str]:
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=10, env=env)
        s = (p.stdout or p.stderr).decode("utf-8", "replace").strip().splitlines()
        return s[0] if s else ""
    except Exception:
        return None


def _tmp(text: str, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _run_file(args_before: List[str], text: str, suffix: str, timeout: float, env) -> str:
    path = _tmp(text, suffix)
    try:
        return _sh(args_before + [path], timeout, env)
    finally:
        os.unlink(path)


def _py_version() -> Optional[str]:
    return "Python " + sys.version.split()[0]


def _sqlite_run(timeout: float, env) -> str:
    import sqlite3
    con = sqlite3.connect(":memory:")
    lines = []
    for pid, sql in SQLITE_SQL:
        try:
            v = con.execute(sql).fetchone()[0]
            if pid in ("digit-regex", "equal-ye"):
                v = "true" if v else "false"
            lines.append(f"{pid}\t{v}")
        except Exception:
            lines.append(f"{pid}\terror")
    # sort via ORDER BY
    con.execute("CREATE TABLE t(x TEXT)")
    con.executemany("INSERT INTO t VALUES (?)", [("ت",), ("پ",), ("ب",), ("ا",)])
    lines.append("sort-default\t" + " ".join(r[0] for r in con.execute("SELECT x FROM t ORDER BY x")))
    lines.append("word-regex\tn/a:SQLite has no regex engine built in (REGEXP is not defined)")
    lines.append("sort-fa-locale\tn/a:COLLATE only knows BINARY/NOCASE/RTRIM unless an ICU extension is loaded")
    lines.append("nfkc\tn/a:SQLite has no Unicode normalization")
    lines.append("jalali-format\tn/a:strftime is Gregorian only")
    lines.append("number-format-fa\tn/a:no locale number formatting")
    return "\n".join(lines) + "\n"


def runtimes() -> List[Runtime]:
    return [
        Runtime("python", "python", _py_version,
                lambda to, env: _run_file([sys.executable, "-X", "utf8"], PYTHON, ".py", to, env)),
        Runtime("node", "node", lambda: (_first(["node", "--version"]) if _which("node") else None),
                lambda to, env: _run_file(["node"], JS, ".js", to, env)),
        Runtime("bun", "bun", lambda: ("bun " + _first(["bun", "--version"])) if _which("bun") else None,
                lambda to, env: _run_file(["bun", "run"], JS, ".js", to, env)),
        Runtime("perl", "perl", lambda: (_first(["perl", "-e", "print $^V"]) if _which("perl") else None),
                lambda to, env: _run_file(["perl"], PERL, ".pl", to, env)),
        Runtime("sqlite", "sqlite", lambda: "SQLite " + __import__("sqlite3").sqlite_version,
                _sqlite_run),
        Runtime("jq", "jq", lambda: (_first(["jq", "--version"]) if _which("jq") else None),
                lambda to, env: _sh(["jq", "-nr", JQ], to, env)),
        Runtime("go", "go", lambda: (_first(["go", "version"]) if _which("go") else None),
                lambda to, env: _run_file(["go", "run"], GO, ".go", max(to, 120), env)),
        Runtime("awk", "awk", lambda: (_first(["awk", "-W", "version"]) or _first(["awk", "--version"])) if _which("awk") else None,
                lambda to, env: _run_file(["awk", "-f"], AWK, ".awk", to, env)),
    ]
