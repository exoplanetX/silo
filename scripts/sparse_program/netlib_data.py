"""Reproducible Netlib import for validation only, independent of SILO.

Official compressed originals are decoded by the Netlib-distributed EMPS utility.
The resulting fixed-field MPS is independently read by HiGHS's file reader; no
optimization method is called in this module. Raw, decoded and converted bytes
are retained, with independent coefficient/bound/objective equality checks.
"""

import gzip
import hashlib
import importlib.metadata
import json
import math
import subprocess
import time
import urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = (
    "AFIRO",
    "ADLITTLE",
    "BLEND",
    "SC50A",
    "SC50B",
    "SC105",
    "SC205",
    "SHARE2B",
    "SCAGR7",
    "SCFXM1",
    "BANDM",
    "DEGEN2",
)
PUBLISHED = {
    "AFIRO": (28, 32, 88),
    "ADLITTLE": (57, 97, 465),
    "BLEND": (75, 83, 521),
    "SC50A": (51, 48, 131),
    "SC50B": (51, 48, 119),
    "SC105": (106, 103, 281),
    "SC205": (206, 203, 552),
    "SHARE2B": (97, 79, 730),
    "SCAGR7": (130, 140, 553),
    "SCFXM1": (331, 457, 2612),
    "BANDM": (306, 472, 2659),
    "DEGEN2": (445, 534, 4449),
}
BASE_URL = "https://netlib.org/lp/data/"
EMPS_GZIP_SHA256 = "0b9225b250610e6e3fd65d0e1a90673cea6cb568c3db390465d39fd4c100c77b"
EMPS_SOURCE_SHA256 = "fee41f544f6873a5e12bc598947828dc9964ef0676162e4df55e915760e2be22"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def number(token):
    value = Decimal(token.replace("D", "E").replace("d", "e"))
    if not value.is_finite():
        raise ValueError("Nonfinite MPS coefficient")
    converted = float(value)
    if not math.isfinite(converted) or (value and converted == 0):
        raise ValueError("MPS coefficient over/underflows float64")
    return int(value) if value == value.to_integral_value() else converted


def parse_fixed_mps(text):
    """Read actual fixed MPS positions, independently of SILO's free MPS reader."""
    row_types, columns, rhs, ranges, bounds = {}, {}, {}, {}, {}
    objective, name, section = None, "netlib", None
    selected_rhs, selected_ranges, selected_bounds = None, None, None
    integer_mode, integer_columns = False, set()
    for raw in text.splitlines():
        if not raw.strip() or raw.startswith("*"):
            continue
        if not raw[0].isspace():
            header = raw.split()
            section = header[0]
            if section == "NAME":
                name = header[1] if len(header) > 1 else "netlib"
            if section == "ENDATA":
                break
            continue
        line = raw.ljust(61)
        tag, first = line[1:3].strip(), line[4:12].strip()
        second, value = line[14:22].strip(), line[24:36].strip()
        third, value2 = line[39:47].strip(), line[49:61].strip()
        if section == "ROWS":
            if first in row_types:
                raise ValueError("Duplicate fixed MPS row")
            row_types[first] = tag
            if tag == "N" and objective is None:
                objective = first
        elif section == "COLUMNS":
            if "MARKER" in second:
                integer_mode = "INTORG" in third
                continue
            column = columns.setdefault(first, {})
            if integer_mode:
                integer_columns.add(first)
            for row_name, token in ((second, value), (third, value2)):
                if row_name:
                    if row_name not in row_types:
                        raise ValueError("Unknown fixed MPS row")
                    column[row_name] = column.get(row_name, 0) + number(token)
        elif section in ("RHS", "RANGES"):
            if section == "RHS":
                if selected_rhs is None:
                    selected_rhs = first
                if first != selected_rhs:
                    continue
                target = rhs
            else:
                if selected_ranges is None:
                    selected_ranges = first
                if first != selected_ranges:
                    continue
                target = ranges
            for row_name, token in ((second, value), (third, value2)):
                if row_name:
                    if row_name in target:
                        raise ValueError("Duplicate fixed MPS vector entry")
                    target[row_name] = number(token)
        elif section == "BOUNDS":
            if selected_bounds is None:
                selected_bounds = first
            if first != selected_bounds:
                continue
            lower, upper, kind = bounds.get(second, (0, None, "continuous"))
            v = number(value) if value else None
            if tag == "LO":
                lower = v
            elif tag == "UP":
                upper = v
            elif tag == "FX":
                lower = upper = v
            elif tag == "FR":
                lower = upper = None
            elif tag == "MI":
                lower = None
            elif tag == "PL":
                upper = None
            elif tag == "BV":
                lower, upper, kind = 0, 1, "binary"
            elif tag in ("LI", "UI"):
                kind = "integer"
                if tag == "LI":
                    lower = v
                else:
                    upper = v
            else:
                raise ValueError(f"Unsupported MPS bound type {tag}")
            bounds[second] = lower, upper, kind
    if objective is None:
        raise ValueError("MPS has no objective row")
    variables = []
    for column_name in columns:
        lower, upper, kind = bounds.get(column_name, (0, None, "continuous"))
        if column_name in integer_columns:
            kind = "integer"
        variables.append({"name": column_name, "lower": lower, "upper": upper, "type": kind})
    rows = []
    for row_name, kind in row_types.items():
        if kind == "N":
            continue
        value = rhs.get(row_name, 0)
        lower = value if kind in ("E", "G") else None
        upper = value if kind in ("E", "L") else None
        if row_name in ranges:
            width = ranges[row_name]
            if kind == "L":
                lower = value - abs(width)
            elif kind == "G":
                upper = value + abs(width)
            elif width >= 0:
                upper = value + width
            else:
                lower = value + width
        rows.append(
            {
                "name": row_name,
                "coefficients": {n: c[row_name] for n, c in columns.items() if c.get(row_name, 0)},
                "lower": lower,
                "upper": upper,
            }
        )
    payload = {
        "name": name,
        "sense": "minimize",
        "variables": variables,
        "constraints": rows,
        "objective": {
            "coefficients": {n: c[objective] for n, c in columns.items() if c.get(objective, 0)},
            "constant": -rhs.get(objective, 0),
        },
    }
    metadata = {
        "objective_row": objective,
        "rows_including_objective": len(row_types),
        "nonzeros_including_objective": sum(bool(v) for c in columns.values() for v in c.values()),
        "rhs_vector": selected_rhs,
        "range_vector": selected_ranges,
        "bound_vector": selected_bounds,
        "ignored_free_rows": [n for n, kind in row_types.items() if kind == "N" and n != objective],
    }
    return payload, metadata


def independent_read_check(path, payload):
    """Compare every original item to the independent HiGHS MPS file reader only."""
    from scipy.optimize._highspy._core import HighsStatus, _Highs

    reader = _Highs()
    reader.setOptionValue("output_flag", False)
    status = reader.readModel(str(path))
    if status not in (HighsStatus.kOk, HighsStatus.kWarning):
        raise ValueError(f"Independent reader rejected {path}: {status}")
    lp = reader.getLp()
    assert lp.num_col_ == len(payload["variables"])
    assert lp.num_row_ == len(payload["constraints"])
    assert list(lp.col_names_) == [v["name"] for v in payload["variables"]]
    assert list(lp.row_names_) == [r["name"] for r in payload["constraints"]]
    assert int(lp.sense_) == 1
    assert float(lp.offset_) == float(payload["objective"]["constant"])
    for j, variable in enumerate(payload["variables"]):
        lower, upper = variable["lower"], variable["upper"]
        assert float(lp.col_lower_[j]) == (-math.inf if lower is None else float(lower))
        assert float(lp.col_upper_[j]) == (math.inf if upper is None else float(upper))
        assert float(lp.col_cost_[j]) == float(
            payload["objective"]["coefficients"].get(variable["name"], 0)
        )
    for i, row in enumerate(payload["constraints"]):
        assert float(lp.row_lower_[i]) == (
            -math.inf if row["lower"] is None else float(row["lower"])
        )
        assert float(lp.row_upper_[i]) == (
            math.inf if row["upper"] is None else float(row["upper"])
        )
    matrix = lp.a_matrix_
    actual = {}
    for j, variable in enumerate(payload["variables"]):
        for k in range(matrix.start_[j], matrix.start_[j + 1]):
            value = float(matrix.value_[k])
            if value:
                actual[(matrix.index_[k], variable["name"])] = value
    expected = {
        (i, n): float(v)
        for i, row in enumerate(payload["constraints"])
        for n, v in row["coefficients"].items()
        if v
    }
    assert actual == expected
    return {
        "reader": "scipy.optimize._highspy._core._Highs.readModel/getLp",
        "reader_scipy_version": importlib.metadata.version("scipy"),
        "optimization_calls": 0,
        "equal_items": [
            "row_names",
            "column_names",
            "coefficient_positions_and_values",
            "row_sides",
            "variable_bounds",
            "objective_coefficients",
            "objective_constant",
            "objective_sense",
        ],
        "independent_reader_status": str(status),
        "matrix_nonzeros": len(actual),
    }


def _fetch(url, path, receipts, timeout=20):
    if path.exists():
        data = path.read_bytes()
        receipts.append(
            {
                "url": url,
                "status": "cached",
                "bytes": len(data),
                "sha256": digest(data),
                "seconds": 0,
            }
        )
        return data
    for attempt in range(2):
        started = time.perf_counter()
        try:
            data = urllib.request.urlopen(url, timeout=timeout).read()
            path.write_bytes(data)
            receipts.append(
                {
                    "url": url,
                    "status": "downloaded",
                    "attempt": attempt + 1,
                    "bytes": len(data),
                    "sha256": digest(data),
                    "seconds": time.perf_counter() - started,
                }
            )
            return data
        except Exception as exc:
            receipts.append(
                {
                    "url": url,
                    "status": "failed",
                    "attempt": attempt + 1,
                    "error": f"{type(exc).__name__}: {exc}",
                    "seconds": time.perf_counter() - started,
                }
            )
            if attempt:
                raise
    raise AssertionError("Unreachable download loop")


def fetch_sources(root=ROOT):
    """Acquire the fixed twelve IDs once, decode, cross-read and write small identities."""
    root = Path(root)
    folder = root / "outputs/sparse_lp_program_20261024/inputs/netlib"
    folder.mkdir(parents=True, exist_ok=True)
    receipts, sources = [], []
    started = time.perf_counter()
    source = _fetch(BASE_URL + "emps.c", folder / "emps.c", receipts)
    packed = _fetch(BASE_URL + "emps.exe.gz", folder / "emps.exe.gz", receipts)
    assert digest(source) == EMPS_SOURCE_SHA256
    assert digest(packed) == EMPS_GZIP_SHA256
    executable = folder / "emps.exe"
    executable.write_bytes(gzip.decompress(packed))
    readme = _fetch(BASE_URL + "readme", folder / "readme", receipts)
    try:
        for name in NAMES:
            raw = _fetch(BASE_URL + name.lower(), folder / name.lower(), receipts)
            decoded_path = folder / (name.lower() + ".mps")
            step = time.perf_counter()
            process = subprocess.run(
                [str(executable.resolve()), "-b", str((folder / name.lower()).resolve())],
                capture_output=True,
                timeout=10,
                check=False,
            )
            receipts.append(
                {
                    "command": ["emps.exe", "-b", name.lower()],
                    "exit_code": process.returncode,
                    "seconds": time.perf_counter() - step,
                    "optimization_calls": 0,
                }
            )
            if process.returncode:
                raise ValueError(process.stderr.decode(errors="replace"))
            (folder / (name.lower() + ".decoded.raw")).write_bytes(process.stdout)
            # Preserve original stdout bytes above, and make only EOL transport canonical.
            decoded = (
                "\n".join(line for line in process.stdout.decode("ascii").splitlines() if line)
                + "\n"
            )
            decoded_path.write_bytes(decoded.encode())
            payload, parsed = parse_fixed_mps(decoded)
            assert (
                parsed["rows_including_objective"],
                len(payload["variables"]),
                parsed["nonzeros_including_objective"],
            ) == PUBLISHED[name]
            check = independent_read_check(decoded_path, payload)
            converted = json_bytes(payload)
            (folder / (name.lower() + ".json")).write_bytes(converted)
            sources.append(
                {
                    "id": "NETLIB-" + name,
                    "source_url": BASE_URL + name.lower(),
                    "raw_path": str((folder / name.lower()).relative_to(root)).replace("\\", "/"),
                    "raw_sha256": digest(raw),
                    "decoded_raw_sha256": digest(process.stdout),
                    "decoded_sha256": digest(decoded.encode()),
                    "converted_sha256": digest(converted),
                    "decoded_path": str(decoded_path.relative_to(root)).replace("\\", "/"),
                    "decoded_raw_path": str(
                        (folder / (name.lower() + ".decoded.raw")).relative_to(root)
                    ).replace("\\", "/"),
                    "converted_path": str(
                        (folder / (name.lower() + ".json")).relative_to(root)
                    ).replace("\\", "/"),
                    "row_count_excludes_objective": len(payload["constraints"]),
                    "columns": len(payload["variables"]),
                    "published_counts": PUBLISHED[name],
                    "parsed_mps": parsed,
                    "independent_import_check": check,
                }
            )
    finally:
        (folder / "fetch_decode_receipts.json").write_bytes(json_bytes(receipts))
    result = {
        "program": "SILO-SPARSE-LP-20261024",
        "schema": 1,
        "source_readme_url": BASE_URL + "readme",
        "source_readme_sha256": digest(readme),
        "published_count_convention": (
            "rows/nonzeros include objective row, exclude slack/surplus/RHS"
        ),
        "decoder": {
            "url": BASE_URL + "emps.exe.gz",
            "compressed_sha256": digest(packed),
            "executable_sha256": digest(executable.read_bytes()),
            "source_url": BASE_URL + "emps.c",
            "source_sha256": digest(source),
            "role": "validation-only official EMPS decoder; no product/native solver code",
        },
        "models": sources,
        "optimization_calls": 0,
    }
    (root / "tests/fixtures/sparse_program_sources.json").write_bytes(json_bytes(result))
    summary = {
        "models": len(sources),
        "elapsed_seconds": time.perf_counter() - started,
        "optimization_calls": 0,
        "all_independent_read_checks_pass": True,
    }
    (folder / "source_summary.json").write_bytes(json_bytes(summary))
    return result, summary


def load_external_cases(root=ROOT):
    root = Path(root)
    source = json.loads((root / "tests/fixtures/sparse_program_sources.json").read_text())
    cases = []
    for record in source["models"]:
        raw = (root / record["converted_path"]).read_bytes()
        assert digest(raw) == record["converted_sha256"]
        cases.append(
            {
                "id": record["id"],
                "group": "netlib",
                "recipe": {"kind": "netlib", "name": record["id"][7:]},
                "payload": json.loads(raw),
                "options": {"time_limit": 120, "lp_iteration_limit": 100000},
                "expected_statuses": ["optimal"],
                "metadata": {
                    "source_record": record["id"],
                    "sp2_smoke": record["id"]
                    in ("NETLIB-AFIRO", "NETLIB-ADLITTLE", "NETLIB-SC50A", "NETLIB-SC50B"),
                    "baseline_overlap": record["id"] in tuple("NETLIB-" + n for n in NAMES[:8]),
                },
            }
        )
    return cases
