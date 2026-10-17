"""Data loading, provenance, de-duplication. Reads only de-identified files."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .features import FEATURES

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN = "unknown_source"


def load_config(name: str = "data") -> dict:
    with open(ROOT / "configs" / f"{name}.yaml") as fh:
        return yaml.safe_load(fh)


def vector_key(df: pd.DataFrame, cols: list[str] = FEATURES) -> pd.Series:
    """Hashable key of a feature vector (rounded: CSV floats are 15-17 digits)."""
    return pd.Series(list(map(tuple, df[cols].round(6).to_numpy())), index=df.index)


def assign_group(user_hash: pd.Series, n_users: pd.Series) -> pd.Series:
    """User hash if the vector has exactly one provenance user, else unknown."""
    g = user_hash.fillna("").astype(str)
    ok = (n_users == 1) & (g != "")
    return g.where(ok, UNKNOWN)


def dedupe_exact(df: pd.DataFrame, cols: list[str] = FEATURES) -> tuple[pd.DataFrame, int]:
    """Drop rows whose feature vector already appeared (first occurrence kept)."""
    dup = vector_key(df, cols).duplicated(keep="first")
    return df.loc[~dup].reset_index(drop=True), int(dup.sum())


def load_normals(reading: str, cfg: dict | None = None, dedupe: bool = True
                 ) -> tuple[pd.DataFrame, dict]:
    """Normal-class rows for a reading ('A' = final1, 'B' = final), with groups.

    Returns (frame, stats). Frame columns: FEATURES + group + n_users.
    """
    cfg = cfg or load_config()
    d = ROOT / cfg["deid_dir"]
    if reading == "A":
        df = pd.read_csv(d / "normal_final1_deid.csv")
    elif reading == "B":
        raw = pd.read_csv(d / "telemetry_raw_deid.csv")
        nu = raw.assign(_k=vector_key(raw)).groupby("_k")["user_hash"].nunique()
        df = raw[FEATURES + ["user_hash"]].copy()
        df["n_users"] = vector_key(raw).map(nu).to_numpy()
    else:
        raise ValueError(f"unknown reading {reading!r}")
    df["group"] = assign_group(df["user_hash"], df["n_users"])
    df = df[FEATURES + ["group", "n_users"]]
    stats = {"reading": reading, "rows_before": len(df)}
    if dedupe:
        df, n = dedupe_exact(df)
        stats["duplicates_dropped"] = n
    stats["rows_after"] = len(df)
    stats["group_sizes"] = df["group"].value_counts().to_dict()
    return df, stats


def load_friend_synthetic(cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    return pd.read_csv(ROOT / cfg["deid_dir"] / "synthetic_anomalies.csv")[FEATURES]
