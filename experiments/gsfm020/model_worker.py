"""Portable frozen forwards, preserving exact shipped defaults and raw returns.

Prepared-feature interventions are diagnostic only and never replace native runs.
No training, solver, PF completion, or output repair is performed here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "microsoft-v1.1": ("1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6", "f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831"),
    "newer-base-v2": ("517a07531ea55a11bd81a89a6c6879695a2ba4b4", "9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def serial(value):
    if hasattr(value, "detach"):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(v) for v in value]
    return value


def case_variant(case, order):
    c = copy.deepcopy(case)
    fields = {"original": (), "bus-reverse": ("bus",),
              "branch-reverse": ("branch",),
              "all-reverse": ("bus", "gen", "gencost", "branch")}[order]
    for field in fields:
        c[field].reverse()
    maps = {key: list(reversed(range(len(case[key])))) if key in fields
            else list(range(len(case[key]))) for key in ("bus", "gen", "branch")}
    for key in maps:
        assert all(c[key][i] == case[key][j] for i, j in enumerate(maps[key]))
    if "gen" in fields:
        assert all(c["gencost"][i] == case["gencost"][j] for i, j in enumerate(maps["gen"]))
    return c, maps


class FrozenWorker:
    def __init__(self, release, source, checkpoint, cache):
        self.release = release
        self.source = Path(source).resolve()
        self.checkpoint = Path(checkpoint).resolve()
        self.commit, expected_ckpt = PINS[release]
        assert sha(self.checkpoint) == expected_ckpt, "Checkpoint SHA256 mismatch"
        self.source_hashes = {}
        # Check actual imported files against immutable git objects, not only HEAD.
        for file in sorted((self.source / "model" / "gridsfm").rglob("*.py")):
            relative = file.relative_to(self.source).as_posix()
            original = subprocess.check_output(["git", "-C", str(self.source), "show", self.commit + ":" + relative])
            assert file.read_bytes() == original, (relative, "source differs from pin")
            self.source_hashes[relative] = sha(file)
        self.requested_cache = str(Path(cache).resolve())
        # PyTorch's Windows C++ ZIP writer cannot open the deepest absolute
        # diagnostic cache filenames. Keep per-run isolation using a short key.
        cache_key = hashlib.sha256(self.requested_cache.encode("utf-8")).hexdigest()[:12]
        self.effective_cache = (ROOT.parent / "runtime" / "cache" / cache_key).resolve()
        os.environ.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="4",
                          OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                          XDG_CACHE_HOME=str(self.effective_cache))
        sys.path[:0] = [str(self.source / "model"), str(ROOT / "scripts" / "python")]
        import torch
        import torch_geometric
        import numpy
        import scipy
        import gridsfm
        import gridsfm.model as model_module
        from gridsfm_convert import convert
        self.torch, self.gridsfm, self.model_module, self.convert = torch, gridsfm, model_module, convert
        torch.set_num_threads(4)
        torch.manual_seed(0)
        self.model = gridsfm.load_model(self.checkpoint, device="cpu")
        self.model.eval()
        blob = torch.load(self.checkpoint, weights_only=True, map_location="cpu")
        self.model.load_state_dict(blob["state_dict"], strict=True)
        assert self.model.leaky_alpha == 0 and getattr(self.model, "clip_mode", "clamp") == "clamp"
        self.checkpoint_metadata = serial(blob["metadata"])
        self.versions = {"python": platform.python_version(), "platform": platform.platform(),
                         "torch": torch.__version__, "torch_geometric": torch_geometric.__version__,
                         "numpy": numpy.__version__, "scipy": scipy.__version__,
                         "torch_threads": torch.get_num_threads(), "seed": 0}
        self.base_prepared = None
        self.base_obj = None

    def object_for(self, case):
        obj = self.convert(case)
        if self.release == "newer-base-v2":
            for rows in obj["grid"]["nodes"].values():
                for row in rows:
                    row.append(1.0)
            for fam in ("ac_line", "transformer"):
                for row in obj["grid"]["edges"][fam]["features"]:
                    row.append(1.0)
        assert "solution" not in obj
        assert obj["metadata"]["bus_external_ids"] == [int(b[0]) for b in case["bus"]]
        assert obj["metadata"]["gen_source_rows"] == [i for i, g in enumerate(case["gen"]) if g[7] > 0]
        return obj

    def _branch_maps(self, obj, maps):
        result = {}
        for fam, nt in (("ac_line", "branch_ac"), ("transformer", "branch_tr")):
            base_rows = self.base_obj["metadata"][fam + "_source_rows"]
            base_lookup = {row: i for i, row in enumerate(base_rows)}
            target_rows = obj["metadata"][fam + "_source_rows"]
            target_to_base = [base_lookup[maps["branch"][row]] for row in target_rows]
            base_to_target = [0] * len(target_to_base)
            for target, base in enumerate(target_to_base):
                base_to_target[base] = target
            result[nt] = (target_to_base, base_to_target)
        return result

    def _intervene(self, data, obj, maps, intervention):
        if intervention == "none":
            return
        assert self.base_prepared is not None, "Run original baseline before interventions"
        t = self.torch
        base = self.base_prepared
        branch_maps = self._branch_maps(obj, maps)
        if "cycles" in intervention:
            # Replace cycle nodes, cycle features and ALL cycle relations together.
            for key in list(data.edge_types):
                if key[0] == "cycle" or key[2] == "cycle":
                    del data[key]
            for key, value in base["cycle"].items():
                data["cycle"][key] = value.clone() if t.is_tensor(value) else copy.deepcopy(value)
            for edge_type in base.edge_types:
                if edge_type[0] != "cycle" and edge_type[2] != "cycle":
                    continue
                for key, value in base[edge_type].items():
                    copied = value.clone() if t.is_tensor(value) else copy.deepcopy(value)
                    if key == "edge_index":
                        for dim, node in ((0, edge_type[0]), (1, edge_type[2])):
                            if node in branch_maps:
                                index = t.tensor(branch_maps[node][1], dtype=t.long)
                                copied[dim] = index[copied[dim]]
                    data[edge_type][key] = copied
        if "landmarks" in intervention:
            assert self.release == "microsoft-v1.1"
            assert data["bus"].x.shape[1] == 16
            # Exactly five resistance-landmark moment columns; other bus features stay native.
            data["bus"].x[:, 4:9] = base["bus"].x[maps["bus"], 4:9].clone()
        if "transformer" in intervention:
            assert self.release == "microsoft-v1.1"
            assert data["branch_tr"].x.shape[1] == 15
            # Keep baseline physical association, including its shipped defect.
            # This tests representation mediation, not corrected electrical features.
            target_to_base = branch_maps["branch_tr"][0]
            data["branch_tr"].x[:, -4:] = base["branch_tr"].x[target_to_base, -4:].clone()

    def run(self, case, output, order="original", intervention="none", poison=False, remember_baseline=False):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        prefix = output / self.release
        assert not Path(str(prefix) + "-returned.json").exists(), "Refusing to overwrite a forward"
        c, maps = case_variant(case, order)
        obj = self.object_for(c)
        mapping = copy.deepcopy(obj["metadata"])
        if poison:
            obj["solution"] = {"nodes": {"bus": [[999.0, -123.0]] * len(c["bus"]),
                                           "generator": [[999.0, -123.0]] * len(c["gen"])}}
            obj["metadata"]["objective"] = 9.99e90
        if (output / "input.json").exists():
            assert json.loads((output / "input.json").read_text(encoding="utf-8")) == c, "Existing input differs"
        else:
            save(output / "input.json", c)
        input_path = Path(str(prefix) + "-input.pyg.json")
        save(input_path, obj)
        t = self.torch
        captures = []
        prepared = []
        learned_inputs = {}
        hodge_outputs = []
        original_prepare = self.gridsfm.prepare_for_inference
        original_clip = self.model_module._leaky_clip

        def observed_prepare(data):
            data = original_prepare(data)
            before = data.clone()
            self._intervene(data, obj, maps, intervention)
            prepared.append(data.clone())
            # Save only tensors/plain metadata, allowing weights_only=True inspection.
            t.save(before.to_dict(), str(prefix) + "-prepared-default.pt")
            t.save(data.to_dict(), str(prefix) + "-prepared-used.pt")
            return data

        def observed_clip(value, lo, hi, **kwargs):
            out = original_clip(value, lo, hi, **kwargs)
            captures.append({"input": serial(value), "lo": serial(lo), "hi": serial(hi), "output": serial(out)})
            return out

        def observed_hodge(module, inputs, outputs):
            hodge_outputs.append({key: value.detach().cpu().clone() for key, value in outputs.items()})

        def observe_projection(name):
            def observer(module, inputs):
                learned_inputs[name] = inputs[0].detach().cpu().clone()
            return observer

        hooks = [self.model.hodge_pe.register_forward_hook(observed_hodge)]
        hooks += [module.register_forward_pre_hook(observe_projection(name))
                  for name, module in self.model.input_proj.items()]

        self.gridsfm.prepare_for_inference = observed_prepare
        self.model_module._leaky_clip = observed_clip
        status = {"release": self.release, "order": order, "intervention": intervention,
                  "label_poison_control": poison, "status": "attempted",
                  "started_unix": time.time(), "input_sha256": sha(output / "input.json")}
        save(Path(str(prefix) + "-attempt.json"), status)
        start = time.perf_counter()
        try:
            returned = self.gridsfm.predict(self.model, input_path, fmt="pyg")
            # Preserve raw returned tensors FIRST, before conversions or physics scoring.
            t.save(returned, str(prefix) + "-returned.pt")
            raw = serial(returned)
            save(Path(str(prefix) + "-returned.json"), raw)
        except Exception as exc:
            status.update(status="FAILED", error=repr(exc), elapsed_seconds=time.perf_counter() - start)
            save(Path(str(prefix) + "-attempt.json"), status)
            raise
        finally:
            self.gridsfm.prepare_for_inference = original_prepare
            self.model_module._leaky_clip = original_clip
            for hook in hooks:
                hook.remove()
        elapsed = time.perf_counter() - start
        assert len(prepared) == 1
        assert len(hodge_outputs) == 1
        t.save(hodge_outputs[0], str(prefix) + "-hodge-output.pt")
        t.save(learned_inputs, str(prefix) + "-projection-inputs.pt")
        native = {"vm": raw["V"], "va_deg": [math.degrees(v) for v in raw["theta"]],
                  "pg_mw": [0.0] * len(c["gen"]), "qg_mvar": [0.0] * len(c["gen"])}
        for source, key in (("Pg", "pg_mw"), ("Qg", "qg_mvar")):
            assert len(raw[source]) == len(mapping["gen_source_rows"])
            for row, value in zip(mapping["gen_source_rows"], raw[source]):
                native[key][row] = value * c["baseMVA"]
        assert len(native["vm"]) == len(c["bus"])
        save(Path(str(prefix) + "-native.json"), native)
        assert len(captures) == 3, "Unexpected clamp call count"
        for capture, variable in zip(captures, ("Pg", "Qg", "V")):
            capture["variable"] = variable
            assert capture["output"] == raw[variable]
            assert t.isfinite(t.tensor(capture["input"])).all()
        save(Path(str(prefix) + "-clamps.json"), {"captures": captures,
             "semantics": "Observed unchanged shipped clamp; Pg/Qg include midpoint offsets; theta uses clipped Pg."})
        if remember_baseline:
            assert order == "original" and intervention == "none" and not poison
            self.base_prepared, self.base_obj = prepared[0].clone(), copy.deepcopy(obj)
        metadata = {**status, "status": "PASS", "source_commit": self.commit,
                    "source_hashes": self.source_hashes, "checkpoint_path": str(self.checkpoint),
                    "checkpoint_sha256": sha(self.checkpoint), "checkpoint_metadata": self.checkpoint_metadata,
                    "versions": self.versions, "clip_mode": getattr(self.model, "clip_mode", "clamp"),
                    "requested_cache": self.requested_cache, "effective_cache": str(self.effective_cache),
                    "leaky_alpha": self.model.leaky_alpha, "model_input_has_solution": poison,
                    "native_saved_before_evaluation": True, "additional_PF_or_OPF": False,
                    "mapping": mapping, "variant_to_original_rows": maps,
                    "inference_seconds_descriptive_only": elapsed,
                    "prepared_default_sha256": sha(str(prefix) + "-prepared-default.pt"),
                    "prepared_used_sha256": sha(str(prefix) + "-prepared-used.pt"),
                    "worker_sha256": sha(__file__)}
        save(Path(str(prefix) + "-metadata.json"), metadata)
        status.update(status="PASS", elapsed_seconds=elapsed)
        save(Path(str(prefix) + "-attempt.json"), status)
        print(self.release, order, intervention, "native saved", flush=True)
        return {"raw": raw, "native": native, "maps": maps, "metadata": metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, choices=PINS)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    case = json.loads(args.input.read_text(encoding="utf-8"))
    worker = FrozenWorker(args.release, args.source, args.checkpoint, args.out / "cache")
    worker.run(case, args.out)


if __name__ == "__main__":
    main()
