"""Independent analysis of saved diagnostic outputs; no inference or solvers."""
from pathlib import Path
import json
import numpy as np
import torch
from electrical import score
from prepare import O, read, save


def aligned(state, maps):
    return {key: np.asarray(values)[np.argsort(maps["bus" if key in ("vm", "va_deg") else "gen"])].tolist()
            for key, values in state.items()}


def delta(first, second, slack):
    output = {}
    for key in ("vm", "va_deg", "pg_mw", "qg_mvar"):
        a, b = np.asarray(first[key]), np.asarray(second[key])
        if key == "va_deg":
            a, b = a - a[slack], b - b[slack]
            difference = (b - a + 180.0) % 360.0 - 180.0
        else:
            difference = b - a
        output[key] = {"mean_absolute_difference": float(np.abs(difference).mean()),
                       "maximum_absolute_difference": float(np.abs(difference).max()),
                       "exactly_different_count": int(np.count_nonzero(difference))}
    return output


def prepared_changes(path, release, intervention):
    original = torch.load(path / (release + "-prepared-default.pt"), weights_only=True)
    used = torch.load(path / (release + "-prepared-used.pt"), weights_only=True)
    changes = []
    assert set(original) == set(used)
    for store in original:
        assert set(original[store]) == set(used[store])
        for attribute, first in original[store].items():
            second = used[store][attribute]
            equal = torch.equal(first, second) if torch.is_tensor(first) else first == second
            if equal:
                continue
            changes.append({"store": str(store), "attribute": attribute})
            allowed = ("cycles" in intervention and (store == "cycle" or isinstance(store, tuple) and "cycle" in (store[0], store[2])))
            if "landmarks" in intervention and store == "bus" and attribute == "x":
                assert torch.equal(first[:, :4], second[:, :4])
                assert torch.equal(first[:, 9:], second[:, 9:])
                allowed = True
            if "transformer" in intervention and store == "branch_tr" and attribute == "x":
                assert torch.equal(first[:, :-4], second[:, :-4])
                allowed = True
            assert allowed, (store, attribute, "Unintended prepared tensor change")
    return {"no_unintended_tensor_changes": True, "changed_attributes": changes}


def main():
    case = read(O / "bases/300/input.json")
    reference = read(O / "recovered-base/AC-reference-DERIVED-state.json")["state"]
    slack = next(i for i, bus in enumerate(case["bus"]) if bus[1] == 3)
    output = {"scope": "Saved-artifact review only; zero forwards/solves/new electrical inputs", "releases": {}}
    for release in ("microsoft-v1.1", "newer-base-v2"):
        directory = O / "diagnostic" / release
        original_summary = read(directory / "summary.json")
        result = {"original_schedule_status": original_summary["status"], "runs": {}}
        names = [r["name"] for r in original_summary["records"]]
        if (directory / "cold-retry" / (release + "-returned.json")).exists():
            names.append("cold-retry")
        states = {}
        baseline_raw = read(directory / "baseline-cold" / (release + "-returned.json"))
        baseline_clamps = read(directory / "baseline-cold" / (release + "-clamps.json"))["captures"]
        for name in names:
            path = directory / name
            if not (path / (release + "-native.json")).exists():
                result["runs"][name] = {"native_return_present": False}
                continue
            state = read(path / (release + "-native.json"))
            metadata = read(path / (release + "-metadata.json"))
            physical = aligned(state, metadata["variant_to_original_rows"])
            states[name] = physical
            clamps = []
            for original, capture in zip(baseline_clamps, read(path / (release + "-clamps.json"))["captures"]):
                variable = capture["variable"]
                values, clipped = np.asarray(capture["input"]), np.asarray(capture["output"])
                scale = 1 if variable == "V" else case["baseMVA"]
                tolerance = 1e-4 if variable == "V" else 1e-3
                order = np.argsort(metadata["variant_to_original_rows"]["bus" if variable == "V" else "gen"])
                preclip_difference = np.abs(values[order] - np.asarray(original["input"])) * scale
                clamps.append({"variable": variable,
                               "strict_clipped_count": int(np.count_nonzero(values != clipped)),
                               "material_clipped_count": int(np.count_nonzero(np.abs(values - clipped) * scale > tolerance)),
                               "preclip_maximum_difference_from_baseline_physical_units": float(preclip_difference.max()),
                               "preclip_mean_difference_from_baseline_physical_units": float(preclip_difference.mean())})
            # Score aligned states against original matrices, independently of their variant file.
            scoring, _, _, _ = score(case, physical, release, reference)
            variant_scoring, _, _, _ = score(read(path / "input.json"), state, release)
            for component in ("P", "Q"):
                for statistic in ("mean", "median", "p95", "max"):
                    assert abs(scoring[component][statistic] - variant_scoring[component][statistic]) < 1e-6
            result["runs"][name] = {
                "native_return_present": True,
                "all_raw_return_values_exactly_equal_baseline": read(path / (release + "-returned.json")) == baseline_raw,
                "mapped_vs_variant_physics_agree_below_1e-6": True,
                "state_difference_vs_baseline": delta(states["baseline-cold"], physical, slack),
                "physical_score": scoring,
                "actual_clamping": clamps,
                "prepared_intervention_audit": prepared_changes(path, release, metadata["intervention"]),
            }
        historical = read(O / "recovered-base" / (release + "-DERIVED-state.json"))["state"]
        old_score, _, _, _ = score(case, historical, release, reference)
        result["cross_platform_replay"] = {
            "fresh_vs_recovered_historical_state": delta(historical, states["baseline-cold"], slack),
            "historical_physical_score": old_score,
            "historical_raw_return_dictionary_available": False,
            "note": "Historical states are checksum-verified recovered derivatives; raw returned dictionaries remain unavailable.",
        }
        if release == "microsoft-v1.1":
            result["landmark_only_prediction_movement"] = delta(states["bus-reverse-default"], states["bus-reverse-landmarks"], slack)
            result["transformer_only_prediction_movement"] = delta(states["branch-reverse-default"], states["branch-reverse-transformer"], slack)
        output["releases"][release] = result
    save(O / "diagnostic" / "independent-differences.json", output)
    print(json.dumps({release: {"cross_platform": result["cross_platform_replay"]["fresh_vs_recovered_historical_state"],
                               "landmark_only": result.get("landmark_only_prediction_movement"),
                               "native_joint_feasible_count": sum(run.get("physical_score", {}).get("AC_joint_feasible", False) for run in result["runs"].values())}
                      for release, result in output["releases"].items()}, indent=2))


if __name__ == "__main__":
    main()
