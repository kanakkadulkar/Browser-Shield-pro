"""Write the locked evaluation protocol (sizes, groups, fingerprints) to reports/stage_a/."""
import json

from .data import ROOT, load_normals
from .splits import build_protocol


def main() -> dict:
    a, sa = load_normals("A"); b, sb = load_normals("B")
    p = build_protocol(a, b)
    out = {"test_groups": p["test_groups"], "dedupe": {"A": {k: v for k, v in sa.items() if k != "group_sizes"},
                                                       "B": {k: v for k, v in sb.items() if k != "group_sizes"}},
           "readings": {}}
    for r, st in (("A", sa), ("B", sb)):
        d = p["readings"][r]
        out["readings"][r] = {
            "normal_unique_rows": st["rows_after"], "group_sizes_all": st["group_sizes"],
            "dev_rows": len(d["dev"]), "test_rows": len(d["test"]),
            "dev_group_sizes": d["dev"]["group"].value_counts().to_dict(),
            "validation_folds": d["val_groups"], "test_fingerprint": d["test_fingerprint"],
        }
    path = ROOT / "reports" / "stage_a" / "protocol.json"
    path.write_text(json.dumps(out, indent=2)); return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
