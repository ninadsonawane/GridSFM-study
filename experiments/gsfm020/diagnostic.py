"""Bounded same-input representation mediation: 8 v2 + 11 v1.1 forwards.

This uses one existing electrical input only. Altered prepared-feature returns
are diagnostic outputs, never replacements for the frozen shipped-default point.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from model_worker import FrozenWorker, PINS, save, sha


def differences(a, b, maps=None):
    import numpy as np
    result = {}
    for key in ("vm", "va_deg", "pg_mw", "qg_mvar"):
        av = np.asarray(a[key], dtype=float)
        bv = np.asarray(b[key], dtype=float)
        if maps is not None:
            mapping = maps["bus" if key in ("vm", "va_deg") else "gen"]
            bv = bv[np.argsort(mapping)]
        delta = np.abs(av - bv)
        result[key] = {"max_abs": float(delta.max()), "mean_abs": float(delta.mean()),
                       "nonzero_count": int(np.count_nonzero(delta))}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", choices=PINS, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=1800)
    args = parser.parse_args()
    assert not args.out.exists(), "Choose a new diagnostic output directory"
    args.out.mkdir(parents=True)
    schedule = [
        ("baseline-cold", "original", "none", False),
        ("baseline-warm", "original", "none", False),
        ("label-poison", "original", "none", True),
        ("branch-reverse-default", "branch-reverse", "none", False),
        ("branch-reverse-cycles", "branch-reverse", "cycles", False),
        ("bus-reverse-default", "bus-reverse", "none", False),
        ("bus-reverse-cycles", "bus-reverse", "cycles", False),
    ]
    if args.release == "microsoft-v1.1":
        schedule += [
            ("bus-reverse-landmarks", "bus-reverse", "landmarks", False),
            ("branch-reverse-transformer", "branch-reverse", "transformer", False),
            ("branch-reverse-cycles-transformer", "branch-reverse", "cycles+transformer", False),
        ]
    schedule.append(("independent-cold", "original", "independent-process", False))
    protocol = {"scope": "Existing electrical input; feature mediation only, no OPF/PF solves",
                "input_sha256": sha(args.input), "release": args.release,
                "max_forwards": len(schedule), "max_seconds": args.max_seconds,
                "schedule_before_outcomes": schedule, "started_unix": time.time(),
                "hypotheses": ["Identical input has repeatable native outputs and is label invariant.",
                               "Replacing only mapped cycle nodes/features/all relations reduces branch-order output dependence.",
                               "v1 landmark moments and misplaced transformer DC features separately mediate row-order effects."],
                "interpretation": "Feature substitution measures mediation, not a corrected release or physical repair.",
                "script_sha256": sha(__file__)}
    save(args.out / "protocol.json", protocol)
    case = json.loads(args.input.read_text(encoding="utf-8"))
    worker = FrozenWorker(args.release, args.source, args.checkpoint, args.out / "cache")
    start = time.monotonic()
    records = []
    runs = {}
    for name, order, intervention, poison in schedule:
        if time.monotonic() - start >= args.max_seconds:
            records.append({"name": name, "status": "NOT_ATTEMPTED_TIME_LIMIT"})
            break
        record = {"name": name, "status": "ATTEMPTED", "started_unix": time.time()}
        records.append(record)
        save(args.out / "ledger.json", records)
        try:
            if name == "independent-cold":
                target = args.out / name
                target.mkdir()
                command = [sys.executable, "-B", str(Path(__file__).with_name("model_worker.py")),
                           "--release", args.release, "--source", str(args.source),
                           "--checkpoint", str(args.checkpoint), "--input", str(args.input),
                           "--out", str(target)]
                record["argv"] = command
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=max(1.0, args.max_seconds - (time.monotonic() - start)))
                (target / "worker.log").write_text(result.stdout + "\nSTDERR\n" + result.stderr, encoding="utf-8")
                record["returncode"] = result.returncode
                assert result.returncode == 0, "Independent cold-process forward failed"
                prefix = target / args.release
                read = lambda suffix: json.loads(Path(str(prefix) + suffix).read_text(encoding="utf-8"))
                metadata = read("-metadata.json")
                run = {"raw": read("-returned.json"), "native": read("-native.json"),
                       "metadata": metadata, "maps": metadata["variant_to_original_rows"]}
            else:
                run = worker.run(case, args.out / name, order, intervention, poison,
                                 remember_baseline=name == "baseline-cold")
            runs[name] = run
            record.update(status="PASS", elapsed_seconds=run["metadata"]["inference_seconds_descriptive_only"])
            if name != "baseline-cold":
                record["native_difference_vs_original_baseline"] = differences(
                    runs["baseline-cold"]["native"], run["native"], run["maps"])
            if name in ("baseline-warm", "label-poison", "independent-cold"):
                record["exact_all_returned_values_equal_baseline"] = run["raw"] == runs["baseline-cold"]["raw"]
                assert record["exact_all_returned_values_equal_baseline"], "Repeatability/label-invariance gate failed"
        except Exception as exc:
            record.update(status="FAILED", error=repr(exc))
            save(args.out / "ledger.json", records)
            save(args.out / "summary.json", {"status": "STOPPED_CORRECTNESS_GATE", "records": records})
            raise
        save(args.out / "ledger.json", records)
    save(args.out / "summary.json", {"status": "COMPLETE" if len(runs) == len(schedule) else "TIME_LIMIT",
         "attempted_forwards": sum(r["status"] != "NOT_ATTEMPTED_TIME_LIMIT" for r in records),
         "new_electrical_inputs": 0, "records": records,
         "limitations": "Raw angle differences are not gauge-aligned; use physical evaluation separately. Source corrections were not applied. Fixed-order electrical comparisons retain shipped defects."})


if __name__ == "__main__":
    main()
