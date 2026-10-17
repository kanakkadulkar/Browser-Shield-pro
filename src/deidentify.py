"""One-time de-identification of the friend's data (the ONLY reader of the source).

Drops user_id / domain / timestamp (and cpu_cores / memory_available, which
fingerprint a machine). Keeps salted hashes of user and domain, used only to
build group splits, plus time relative to each user's first snapshot.

The source folder is read-only: its file hashes are recorded before and after
and the script aborts if they differ.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import shutil

import pandas as pd

from .data import ROOT, load_config, vector_key
from .features import FEATURES


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _salt(path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_hex(16))
    return path.read_text().strip()


def main() -> None:
    cfg = load_config()
    src = (ROOT / cfg["source_dir"]).resolve()
    files = {k: src / v for k, v in cfg["source_files"].items()}
    before = {k: _sha256(p) for k, p in files.items()}
    salt = _salt(ROOT / cfg["salt_path"])
    h = lambda s: hashlib.sha256(f"{salt}:{s}".encode()).hexdigest()[:10]
    out = ROOT / cfg["deid_dir"]
    out.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(files["raw"])
    raw["user_hash"] = raw["user_id"].map(h)
    raw["domain_hash"] = raw["domain"].map(h)
    raw["t_rel_s"] = (raw["timestamp"] - raw.groupby("user_id")["timestamp"].transform("min")) / 1000.0
    keep = ["user_hash", "domain_hash", "t_rel_s"] + [
        c for c in raw.columns if c not in cfg["dropped_columns"]
        and c not in ("user_hash", "domain_hash", "t_rel_s")]
    raw[keep].to_csv(out / "telemetry_raw_deid.csv", index=False)

    # Reading A: map each normal vector to the users whose raw rows contain it.
    users_of = raw.assign(_k=vector_key(raw)).groupby("_k")["user_hash"].agg(lambda s: sorted(set(s)))
    a = pd.read_csv(files["normal_a"])
    ul = vector_key(a).map(users_of)
    a["n_users"] = ul.map(lambda x: len(x) if isinstance(x, list) else 0)
    a["user_hash"] = ul.map(lambda x: x[0] if isinstance(x, list) and len(x) == 1 else "")
    a[FEATURES + ["user_hash", "n_users"]].to_csv(out / "normal_final1_deid.csv", index=False)

    syn = pd.read_csv(files["synthetic"])
    assert not {"user_id", "domain", "timestamp"} & set(syn.columns)
    syn[FEATURES].to_csv(out / "synthetic_anomalies.csv", index=False)

    after = {k: _sha256(p) for k, p in files.items()}
    assert before == after, "source folder changed during de-identification!"
    manifest = {
        "note": "SHA-256 of the friend's source files (unchanged by this run) and output row counts.",
        "source_sha256": before,
        "rows": {"telemetry_raw_deid": len(raw), "normal_final1_deid": len(a), "synthetic_anomalies": len(syn)},
        "dropped_columns": cfg["dropped_columns"],
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest["rows"]), "| source unchanged:", before == after)


if __name__ == "__main__":
    main()
