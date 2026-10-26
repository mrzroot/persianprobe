"""Probe metadata: what is asked, what a Persian-speaking user expects, how to show it, how to fix it."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict

LETTER_NAMES = {"ا": "alef", "ب": "be", "پ": "pe", "ت": "te"}
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def _view_sort(v: str) -> str:
    return " ".join(LETTER_NAMES.get(x, x) for x in v.split())


def _view_json(v: str) -> str:
    return "\\u escapes" if "\\u" in v else ("raw UTF-8" if re.search(r"[^\x00-\x7f]", v) else v)


def _view_cps(v: str) -> str:
    return " ".join(f"U+{ord(c):04X}" for c in v)


def _view_digits(v: str) -> str:
    out = v.translate({ord(c): str(i) for i, c in enumerate(FA_DIGITS)})
    out = out.replace("٬", ",").replace("٫", ".")
    return out + " (fa)" if out != v else out


@dataclass
class Probe:
    id: str
    title: str
    idiom: Dict[str, str]          # runtime -> the idiom that was run
    expect: str                    # raw value a Persian-speaking user expects
    view: callable = lambda v: v
    expect_view: str = ""
    why: str = ""
    fix: Dict[str, str] = field(default_factory=dict)  # runtime or "*" -> snippet


P = Probe
PROBES = [
    P("parse-int", "parse the integer ۱۲۳ (Persian digits)",
      {"python": 'int("۱۲۳")', "node": 'parseInt("۱۲۳")', "bun": 'parseInt("۱۲۳")', "perl": '"۱۲۳" + 0', "sqlite": "CAST('۱۲۳' AS INTEGER)",
       "jq": 'tonumber', "go": 'strconv.Atoi("۱۲۳")', "awk": '"۱۲۳" + 0'},
      "123",
      why="Only Python's int() accepts non-ASCII digits. Everything else returns NaN/0/error, silently in JS, Perl, SQLite and awk.",
      fix={"node": 'const toEn = s => s.replace(/[۰-۹]/g, d => d.charCodeAt(0) - 1776).replace(/[٠-٩]/g, d => d.charCodeAt(0) - 1632);\ntoEn("۱۲۳") // "123"',
           "bun": 'same as node: map ۰-۹ (U+06F0..) and ٠-٩ (U+0660..) to ASCII before parseInt',
           "perl": 'tr/۰-۹٠-٩/0-90-9/ on the string before numeric use',
           "sqlite": "do it in the application: SQLite CAST stops at the first non-ASCII character and returns 0 without an error",
           "go": 'strings.Map(func(r rune) rune { if r >= 0x06F0 && r <= 0x06F9 { return r - 0x06F0 + \'0\' }; return r }, s)',
           "jq": 'explode | map(if . >= 1776 and . <= 1785 then . - 1728 else . end) | implode | tonumber',
           "awk": "convert in the shell first, e.g. sed 'y/۰۱۲۳۴۵۶۷۸۹/0123456789/'",
           "*": "map Persian (U+06F0..06F9) and Arabic-Indic (U+0660..0669) digits to ASCII at the system boundary"}),
    P("parse-int-sep", "parse ۱٬۲۳۴ (Persian thousands separator U+066C)",
      {"python": 'int("۱٬۲۳۴")', "node": 'parseInt("۱٬۲۳۴")', "bun": 'parseInt("۱٬۲۳۴")', "perl": '"۱٬۲۳۴" + 0', "sqlite": "CAST('۱٬۲۳۴' AS INTEGER)",
       "jq": 'tonumber', "go": 'strconv.Atoi', "awk": '+ 0'},
      "1234",
      why="Even Python fails once the separator ٬ (U+066C) is present, which is exactly what Intl/fa-IR formatting produces.",
      fix={"*": "strip ٬ (U+066C) and ، and replace ٫ (U+066B) with '.', then map the digits; do it before parsing"}),
    P("parse-float-dot", "parse ۱.۵ (Persian digits, ASCII dot)",
      {"python": 'float("۱.۵")', "node": 'parseFloat("۱.۵")', "bun": 'parseFloat("۱.۵")', "perl": '"۱.۵" + 0', "sqlite": "CAST('۱.۵' AS REAL)",
       "jq": 'tonumber', "go": 'strconv.ParseFloat', "awk": '+ 0'},
      "1.5",
      why="Python accepts it, JavaScript returns NaN, Perl/SQLite/awk return 0.",
      fix={"*": "map the digits to ASCII first"}),
    P("parse-float-fa-sep", "parse ۱٫۵ (Persian decimal separator U+066B)",
      {"python": 'float("۱٫۵")', "node": 'parseFloat("۱٫۵")', "bun": 'parseFloat("۱٫۵")', "perl": '"۱٫۵" + 0', "sqlite": "CAST('۱٫۵' AS REAL)",
       "jq": 'tonumber', "go": 'strconv.ParseFloat', "awk": '+ 0'},
      "1.5",
      why="No standard library understands ٫ (U+066B) as a decimal point.",
      fix={"*": "replace ٫ with '.' and ٬ with '' after mapping digits"}),
    P("digit-regex", r"does the regex \d match the digit ۵?",
      {"python": r're.match(r"\d", s)', "node": r"/\d/.test(s)", "bun": r"/\d/.test(s)", "perl": r"=~ /\d/", "sqlite": "GLOB '[0-9]'",
       "jq": r'test("\\d")', "go": r"regexp \d", "awk": "~ /[0-9]/"},
      "true",
      why=r"Python, Perl and jq (Unicode-aware \d) say yes; JavaScript, Go, SQLite GLOB and awk say no. The same validation regex gives different answers per language.",
      fix={"node": r"/[\d۰-۹٠-٩]/ or /\p{Nd}/u", "bun": r"/[\d۰-۹٠-٩]/ or /\p{Nd}/u", "go": r"regexp.MustCompile(`\p{Nd}`)",
           "sqlite": "GLOB has no Unicode classes: validate in the application",
           "awk": "awk cannot do this portably: normalise digits first",
           "*": r"use an explicit class: [0-9۰-۹٠-٩] or \p{Nd}"}),
    P("word-regex", r"does the regex \w match the letter ک?",
      {"python": r're.match(r"\w", s)', "node": r"/\w/.test(s)", "bun": r"/\w/.test(s)", "perl": r"=~ /\w/", "jq": r'test("\\w")', "go": r"regexp \w"},
      "true",
      why=r"JavaScript and Go define \w as [A-Za-z0-9_], so a Persian word is not a 'word'. Python, Perl and jq are Unicode-aware.",
      fix={"node": r"/[\p{L}\p{N}_]/u", "bun": r"/[\p{L}\p{N}_]/u", "go": r"regexp.MustCompile(`[\p{L}\p{N}_]`)", "*": r"use \p{L}\p{N} instead of \w"}),
    P("length", "length of نامه‌ها (6 letters + 1 ZWNJ = 7 characters)",
      {"python": "len(s)", "node": "s.length", "bun": "s.length", "perl": "length($s) (use utf8)", "sqlite": "length(s)", "jq": "length", "go": "len(s)", "awk": "length(s)"},
      "7",
      why="Go's len() and awk (without multibyte support) count UTF-8 bytes: 15 instead of 7.",
      fix={"go": "utf8.RuneCountInString(s)", "awk": "use gawk in a UTF-8 locale, or do the length check in another tool",
           "*": "count characters (code points), not bytes"}),
    P("equal-ye", "is علی (Persian ی U+06CC) equal to علي (Arabic ي U+064A)?",
      {"python": "==", "node": "===", "bun": "===", "perl": "eq", "sqlite": "=", "jq": "==", "go": "==", "awk": "=="},
      "true",
      why="Every runtime says they differ. Search, login names and unique keys silently split in two unless you fold Arabic ي ى ك to ی ک at input.",
      fix={"python": 's.translate({0x064A: "ی", 0x0649: "ی", 0x0643: "ک"})',
           "node": 's.replace(/[يى]/g, "ی").replace(/ك/g, "ک")',
           "bun": 's.replace(/[يى]/g, "ی").replace(/ك/g, "ک")',
           "sqlite": "REPLACE(REPLACE(REPLACE(x, 'ي', 'ی'), 'ى', 'ی'), 'ك', 'ک') in a generated column or trigger",
           "*": "fold ي (U+064A) and ى (U+0649) to ی (U+06CC), ك (U+0643) to ک (U+06A9) before storing and before comparing"}),
    P("sort-default", "sort the letters ت پ ب ا with the default sort",
      {"python": "sorted(l)", "node": "l.sort()", "bun": "l.sort()", "perl": "sort @l", "sqlite": "ORDER BY x", "jq": "sort", "go": "sort.Strings(l)"},
      "ا ب پ ت", view=_view_sort, expect_view="alef be pe te",
      why="Every default sort is by code point. پ چ ژ گ are encoded after the Arabic letters, so پ lands after ت instead of between ب and ت.",
      fix={"node": 'l.sort(new Intl.Collator("fa").compare)', "bun": 'l.sort(new Intl.Collator("fa").compare)',
           "perl": 'Unicode::Collate::Locale->new(locale => "fa")->sort(@l)',
           "python": "PyICU Collator.createInstance(Locale('fa')), or a key function built from the Persian alphabet order",
           "sqlite": "load the ICU extension and use COLLATE, or sort in the application with a Persian collator",
           "go": "golang.org/x/text/collate with language.Persian",
           "*": "use a Persian collator (ICU 'fa'), never the default sort"}),
    P("sort-fa-locale", "sort the same letters with the runtime's own Persian collation",
      {"python": "locale.strxfrm after setlocale('fa_IR.UTF-8')", "node": 'Intl.Collator("fa")', "bun": 'Intl.Collator("fa")', "perl": "Unicode::Collate::Locale('fa')"},
      "ا ب پ ت", view=_view_sort, expect_view="alef be pe te",
      why="Availability differs: JS (via ICU) and Perl ship Persian collation; Python depends on an OS locale that is usually not installed; Go/SQLite/jq/awk have none.",
      fix={"python": "install the fa_IR.UTF-8 locale on the OS, or use PyICU", "*": "ship a collator (ICU) with the app instead of relying on the OS"}),
    P("json-encode", "JSON-encode the string سلام",
      {"python": "json.dumps(s)", "node": "JSON.stringify(s)", "bun": "JSON.stringify(s)", "perl": "JSON::PP->new->encode(s)", "sqlite": "json_quote(s)", "jq": "tojson", "go": "json.Marshal(s)"},
      "raw UTF-8", view=_view_json, expect_view="raw UTF-8",
      why="Python's json.dumps escapes everything to \\u0633\\u0644...: valid JSON, but unreadable in logs, diffs and databases, and different bytes from every other runtime.",
      fix={"python": "json.dumps(obj, ensure_ascii=False)", "*": "keep UTF-8 raw (or escape consistently everywhere)"}),
    P("nfkc", "NFKC-normalize the presentation form ﻻ (U+FEFB) to لا",
      {"python": 'unicodedata.normalize("NFKC")', "node": 's.normalize("NFKC")', "bun": 's.normalize("NFKC")', "perl": "Unicode::Normalize::NFKC"},
      "U+0644 U+0627", view=_view_cps, expect_view="U+0644 U+0627",
      why="Text pasted from PDFs and old Word files contains Arabic presentation forms. Python, JS and Perl can fold them; Go, SQLite, jq and awk have no built-in normalization.",
      fix={"go": "golang.org/x/text/unicode/norm.NFKC.String(s)", "sqlite": "normalise in the application before INSERT",
           "*": "normalise to NFKC at the system boundary"}),
    P("jalali-format", "format 2026-10-24 as a Persian-calendar date",
      {"node": 'Intl.DateTimeFormat("fa-IR")', "bun": 'Intl.DateTimeFormat("fa-IR")'},
      "۱۴۰۵/۸/۲", view=_view_digits, expect_view="1405/8/2 (fa)",
      why="Only the JavaScript runtimes (through ICU) know the Persian calendar. Everywhere else you need a library.",
      fix={"python": "jdatetime or persiantools", "perl": "DateTime::Calendar::Persian (CPAN)", "sqlite": "store Gregorian, convert in the application",
           "*": "use a Jalali library, or store Gregorian and convert at the edge"}),
    P("number-format-fa", "format 1234567.5 for fa-IR",
      {"node": '(1234567.5).toLocaleString("fa-IR")', "bun": '(1234567.5).toLocaleString("fa-IR")'},
      "۱٬۲۳۴٬۵۶۷٫۵", view=_view_digits, expect_view="1,234,567.5 (fa)",
      why="Only JS ships fa-IR number formatting. Its output (Persian digits, ٬ and ٫) cannot be parsed back by parseInt/parseFloat: see parse-int-sep.",
      fix={"python": "Babel: format_decimal(1234567.5, locale='fa_IR')", "*": "format with ICU/Babel at the UI edge, store plain numbers"}),
]
BY_ID = {p.id: p for p in PROBES}
