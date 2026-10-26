import json
import shutil

import pytest

from persianprobe import cli, matrix, render
from persianprobe.adapters import Runtime
from persianprobe.probes import PROBES


def fake(key, lines):
    return Runtime(key, key, lambda: f"{key} 1.0", lambda t, e: "\n".join(lines))


GOOD = ["parse-int\t123", "sort-default\tا ب پ ت", "length\t7", "json-encode\tسلام", "nfkc\tلا"]
BAD = ["parse-int\tNaN", "sort-default\tا ب ت پ", "length\t15", "json-encode\t\"\\u0633\"", "nfkc\tn/a:no normalization"]


def test_probe_table_is_consistent():
    ids = [p.id for p in PROBES]
    assert len(ids) == len(set(ids)) == 14
    for p in PROBES:
        assert p.idiom, p.id
        assert p.expect and p.why and p.fix, p.id


def test_parse_lines_and_statuses():
    res = matrix.run(rts=[fake("python", GOOD), fake("node", BAD)])
    assert res.cells["parse-int"]["python"].status == "ok"
    assert res.cells["parse-int"]["node"].status == "miss"
    assert res.cells["sort-default"]["python"].view == "alef be pe te"
    assert res.cells["sort-default"]["node"].view == "alef be te pe"
    assert res.cells["length"]["node"].status == "miss"
    assert res.cells["json-encode"]["node"].view == "\\u escapes"
    assert res.cells["nfkc"]["node"].status == "na"


def test_verdicts():
    res = matrix.run(rts=[fake("python", GOOD), fake("node", BAD)])
    assert res.verdict("parse-int") == "disagree"
    res2 = matrix.run(rts=[fake("node", BAD), fake("perl", BAD)])
    assert res2.verdict("parse-int") == "all-miss"
    res3 = matrix.run(rts=[fake("python", GOOD)])
    assert res3.verdict("parse-int") == "ok"
    # n/a is not a disagreement: only b reports nfkc as n/a
    res4 = matrix.run(rts=[fake("python", GOOD), fake("node", BAD)])
    assert res4.verdict("nfkc") == "ok"


def test_na_only_probe_has_na_verdict():
    res = matrix.run(rts=[fake("node", ["nfkc\tn/a:x"])])
    assert res.verdict("nfkc") == "n/a"


def test_failed_runtime_is_reported_not_fatal():
    def boom(t, e):
        raise OSError("nope")
    rt = Runtime("go", "go", lambda: "go 1", boom)
    res = matrix.run(rts=[rt, fake("python", GOOD)])
    assert "go" in res.failed and "python" not in res.failed


def test_empty_output_is_failure():
    res = matrix.run(rts=[fake("python", [])])
    assert res.failed["python"] == "produced no output"


def test_runtime_filter():
    res = matrix.run(only=["python"], rts=[fake("python", GOOD), fake("node", BAD)])
    assert list(res.versions) == ["python"]


def test_render_text_and_json():
    res = matrix.run(rts=[fake("python", GOOD), fake("node", BAD)])
    out = render.text(res)
    assert "PORTABILITY TRAPS" in out and "parse-int" in out and "wrong:  node" in out
    assert "fix:" in out
    data = json.loads(render.as_json(res))
    assert data["tool"] == "persianprobe"
    assert {p["id"]: p["verdict"] for p in data["probes"]}["parse-int"] == "disagree"


def test_listing_mentions_every_probe():
    out = render.listing()
    assert all(p.id in out for p in PROBES)


def test_cli_list_and_unknown_probe(capsys):
    assert cli.main(["--list"]) == 0
    assert "parse-int" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["--probes", "nope"])


def test_cli_real_python_runtime(capsys):
    assert cli.main(["--runtimes", "python", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    p = {x["id"]: x for x in data["probes"]}
    assert p["parse-int"]["results"]["python"]["value"] == "123"
    assert p["sort-default"]["results"]["python"]["status"] == "miss"


def test_cli_strict_exit_code():
    assert cli.main(["--runtimes", "python", "--strict", "--json"]) == 1


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_real_node_gets_nan_for_persian_digits():
    res = matrix.run(only=["node"])
    assert res.cells["parse-int"]["node"].raw == "NaN"
    assert res.cells["jalali-format"]["node"].status == "ok"
