from persianprobe import cli, xray


def kinds(s):
    return {h.code for h in xray.scan(s)[0]}


def test_arabic_yeh_and_kaf_detected():
    assert {"arabic-yeh", "arabic-kaf"} <= kinds("علي كتاب")


def test_clean_persian_has_no_hits():
    hits, _ = xray.scan("علی کتاب‌ها ۱۲۳")
    assert hits == []


def test_zwnj_is_counted_not_reported():
    hits, k = xray.scan("کتاب\u200cها")
    assert hits == [] and k["zwnj"] == 1


def test_invisible_marks_and_bom():
    assert {"rlm", "bom", "bidi"} <= kinds("a\u200fb\ufeffc\u202ed")


def test_presentation_form_folds():
    assert xray.normalize("\ufefb") == "لا"
    assert xray.normalize("\ufb8a") == "ژ"


def test_digits_modes():
    s = "٤٥٦ ۱۲۳ 789"
    assert xray.normalize(s, "keep") == "۴۵۶ ۱۲۳ 789"
    assert xray.normalize(s, "fa") == "۴۵۶ ۱۲۳ ۷۸۹"
    assert xray.normalize(s, "en") == "456 123 789"


def test_removal_does_not_corrupt_digits():
    # regression: deleting a char must not turn into a digit
    assert xray.normalize("۷ـ") == "۷"
    assert xray.normalize("ـ") == ""


def test_mixed_digits_warning():
    _, k = xray.scan("1 ۲ ٣")
    assert xray.mixed_digits(k)
    assert not xray.mixed_digits(xray.scan("12")[1])


def test_nbsp_becomes_space_and_diacritics_removed():
    assert xray.normalize("a\u00a0b") == "a b"
    assert xray.normalize("كَتَبَ") == "کتب"


def test_separators_are_reported_but_not_rewritten_by_normalize():
    assert "fa-thousands" in kinds("۱٬۲۳۴")
    assert xray.normalize("۱٬۲۳۴") == "۱٬۲۳۴"


def test_normalize_is_idempotent():
    s = "علي  كتاب‌ها ٤٥٦ 123 ۷ـ ﻻ\u200f"
    once = xray.normalize(s, "fa")
    assert xray.normalize(once, "fa") == once


def test_cli_xray(capsys):
    assert cli.main(["xray", "علي", "--fix"]) == 0
    out = capsys.readouterr().out
    assert "U+064A" in out and "normalized: علی" in out
