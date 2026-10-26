"""Conversion is model I/O only; optimize retains schema2 and its old fallback."""

import json

import pytest

from silo.cli.main import main


@pytest.mark.parametrize("suffix", ["json", "mps", "lp"])
def test_convert_does_not_solve(tmp_path, monkeypatch, suffix):
    import silo

    def forbidden(*args, **kwargs):
        raise AssertionError("convert called solver")

    monkeypatch.setattr(silo, "solve", forbidden)
    source = tmp_path / "source.json"
    source.write_text('{"variables":[{"name":"x","upper":2}]}', encoding="utf-8")
    target = tmp_path / ("target." + suffix)
    assert main(["convert", str(source), "--output", str(target)]) == 0
    assert target.is_file()


def test_unknown_suffix_and_same_path_are_safe(tmp_path):
    source = tmp_path / "source.data"
    source.write_text('{"variables":[{"name":"x"}]}', encoding="utf-8")
    target = tmp_path / "target.lp"
    assert main(["convert", str(source), "--output", str(target)]) == 1
    assert not target.exists()
    assert main(["convert", str(source), "--format", "json", "--output", str(target)]) == 0
    assert main(["convert", str(source), "--format", "json", "--output", str(source)]) == 1
    assert main(["convert", str(target), "--output", str(tmp_path / "out.bad")]) == 1


@pytest.mark.parametrize("suffix,format_arg", [("lp", []), ("weird", ["--format", "lp"]),
                                             ("data", ["--format", "json"])])
def test_optimize_lp_and_old_json_fallback(tmp_path, capsys, suffix, format_arg):
    source = tmp_path / ("model." + suffix)
    if format_arg == ["--format", "json"]:
        text = '{"variables":[{"name":"x","upper":2}],"objective":{"coefficients":{"x":-1}}}'
    else:
        text = "Min\n - x\nST\nBounds\n x <= 2\nEnd"
    source.write_text(text, encoding="utf-8")
    assert main(["optimize", str(source), *format_arg]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema_version"] == 2 and result["objective_value"] == -2
