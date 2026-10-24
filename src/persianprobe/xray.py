"""Character X-ray for Persian text: find the invisible and look-alike characters that break search and joins."""
from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Tuple

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

# char -> (code, label, replacement or None, severity)
SPECIAL = {
    "\u064a": ("arabic-yeh", "Arabic yeh ي: looks like ی but is a different character", "\u06cc"),
    "\u0649": ("alef-maksura", "Alef maksura ى (often typed instead of ی)", "\u06cc"),
    "\u0643": ("arabic-kaf", "Arabic kaf ك: looks like ک but is a different character", "\u06a9"),
    "\u06be": ("heh-doachashmee", "Heh doachashmee ھ (Urdu) instead of ه", "\u0647"),
    "\u0629": ("teh-marbuta", "Teh marbuta ة is Arabic, not Persian (left as is, check the word)", None),
    "\u0640": ("tatweel", "Tatweel ـ (kashida): stretches a word, breaks matching", ""),
    "\u200c": ("zwnj", "ZWNJ (نیم‌فاصله): correct in Persian, but invisible and ignored by many tools", None),
    "\u200d": ("zwj", "ZWJ: rarely wanted in Persian text", None),
    "\u200e": ("lrm", "LRM direction mark (invisible)", ""),
    "\u200f": ("rlm", "RLM direction mark (invisible)", ""),
    "\u202a": ("bidi", "bidi embedding control (invisible)", ""),
    "\u202b": ("bidi", "bidi embedding control (invisible)", ""),
    "\u202c": ("bidi", "bidi embedding control (invisible)", ""),
    "\u202d": ("bidi", "bidi override (invisible)", ""),
    "\u202e": ("bidi", "bidi override (invisible, can reverse text)", ""),
    "\u2066": ("bidi", "bidi isolate (invisible)", ""),
    "\u2067": ("bidi", "bidi isolate (invisible)", ""),
    "\u2068": ("bidi", "bidi isolate (invisible)", ""),
    "\u2069": ("bidi", "bidi isolate (invisible)", ""),
    "\ufeff": ("bom", "byte order mark / zero width no-break space", ""),
    "\u00a0": ("nbsp", "no-break space, looks like a space but != ' '", " "),
    "\u202f": ("nnbsp", "narrow no-break space", " "),
    "\u061f": ("arabic-qmark", "Arabic question mark ؟ (valid Persian; note it is not '?')", None),
    "\u066a": ("arabic-percent", "Arabic percent sign ٪", "%"),
    "\u066b": ("fa-decimal", "Persian decimal separator ٫: not parsed by number parsers", "."),
    "\u066c": ("fa-thousands", "Persian thousands separator ٬: not parsed by number parsers", ","),
}
DIACRITICS = set(chr(c) for c in list(range(0x064B, 0x0660)) + [0x0670])


@dataclass
class Hit:
    index: int
    char: str
    code: str
    label: str
    replacement: Optional[str]


def _digit_kind(ch: str) -> Optional[str]:
    if ch in FA_DIGITS:
        return "persian-digit"
    if ch in AR_DIGITS:
        return "arabic-indic-digit"
    if "0" <= ch <= "9":
        return "ascii-digit"
    return None


def scan(s: str) -> Tuple[List[Hit], Counter]:
    hits: List[Hit] = []
    kinds: Counter = Counter()
    for i, ch in enumerate(s):
        o = ord(ch)
        dk = _digit_kind(ch)
        if dk:
            kinds[dk] += 1
            if dk == "arabic-indic-digit":
                fa = FA_DIGITS[AR_DIGITS.index(ch)]
                look = f" (shaped differently from Persian {fa})" if ch in "٤٥٦" else ""
                hits.append(Hit(i, ch, dk, f"Arabic-Indic digit {ch}{look}", fa))
            continue
        if ch in SPECIAL:
            code, label, rep = SPECIAL[ch]
            kinds[code] += 1
            if code in ("zwnj", "arabic-qmark"):
                continue            # legitimate: counted, not reported as a problem
            hits.append(Hit(i, ch, code, label, rep))
        elif ch in DIACRITICS:
            kinds["diacritic"] += 1
            hits.append(Hit(i, ch, "diacritic", f"diacritic {unicodedata.name(ch, '?').title()} (harari/aerab): breaks matching", ""))
        elif 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF:
            kinds["presentation-form"] += 1
            folded = unicodedata.normalize("NFKC", ch)
            hits.append(Hit(i, ch, "presentation-form", f"Arabic presentation form {unicodedata.name(ch, 'U+%04X' % o)}: pasted from PDF/Word", folded))
        elif unicodedata.category(ch) in ("Cf", "Cc") and ch not in "\n\r\t":
            kinds["invisible"] += 1
            hits.append(Hit(i, ch, "invisible", f"invisible character U+{o:04X} {unicodedata.name(ch, '')}", ""))
        elif 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F:
            kinds["persian-arabic-letter"] += 1
        elif ch.isspace():
            kinds["space"] += 1
        elif ch.isascii() and ch.isalpha():
            kinds["latin"] += 1
        else:
            kinds["other"] += 1
    return hits, kinds


def normalize(s: str, digits: str = "keep", strip_diacritics: bool = True) -> str:
    """digits: 'keep' | 'fa' (-> ۰-۹) | 'en' (-> 0-9)."""
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF:
            ch = unicodedata.normalize("NFKC", ch)
        for c in ch:
            if c in SPECIAL and SPECIAL[c][2] is not None and c not in "\u066b\u066c\u066a":
                c = SPECIAL[c][2]
            elif c in DIACRITICS and strip_diacritics:
                c = ""
            if not c:
                continue
            if c in AR_DIGITS:
                c = FA_DIGITS[AR_DIGITS.index(c)]
            if digits == "en" and c in FA_DIGITS:
                c = str(FA_DIGITS.index(c))
            elif digits == "fa" and "0" <= c <= "9":
                c = FA_DIGITS[int(c)]
            out.append(c)
    return "".join(out)


def mixed_digits(kinds: Counter) -> bool:
    return sum(1 for k in ("persian-digit", "arabic-indic-digit", "ascii-digit") if kinds.get(k)) > 1


def render(s: str, fix: bool = False, digits: str = "keep") -> str:
    hits, kinds = scan(s)
    lines = [f"persianprobe xray · {len(s)} characters · {len(s.encode('utf-8'))} UTF-8 bytes"]
    summary = ", ".join(f"{n} {k}" for k, n in kinds.most_common())
    lines.append(f"contains: {summary or 'nothing'}")
    if not hits and not mixed_digits(kinds):
        lines.append("no look-alike or invisible characters found")
    for h in hits:
        rep = ""
        if h.replacement is not None:
            rep = " → delete" if h.replacement == "" else f" → {h.replacement} U+{ord(h.replacement[0]):04X}"
        shown = h.char if h.char.isprintable() and not unicodedata.combining(h.char) else "·"
        lines.append(f"  [{h.index}] {shown} U+{ord(h.char):04X}  {h.label}{rep}")
    if mixed_digits(kinds):
        lines.append("  ! mixed digit systems (" + ", ".join(k for k in ("persian-digit", "arabic-indic-digit", "ascii-digit") if kinds.get(k)) + "): sorting, equality and parsing will treat them as different")
    if fix:
        lines.append("normalized: " + normalize(s, digits=digits))
    return "\n".join(lines) + "\n"
