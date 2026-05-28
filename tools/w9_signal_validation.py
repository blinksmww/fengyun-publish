"""
w9_signal_validation.py — W9 信号分 held-out ρ 验收 harness(F1 用户拍板)

⚠️ 诚实声明(反 p-hacking,memory feedback_no_p_hacking):
  W2 删 Track A 数字分后,critic 是 B+C 二元投票(无数字可算 ROC);被砍/调的是
  写作侧 harness 信号维度,不卡 ship。本 repo 唯一可 join read_pct 的是 parquet
  预抽特征(proxy),不是信号工具精确输出。本 harness 验的是「这些维度瞄准的物理
  构念跟互动相不相关」(= Round 13 方法论,memory feedback_data_first_design_loop
  已验证可行),不是「critic ROC」。
  ⭐ 砍维度的主证据是 B4 零方差(命中率 100%/0% = 零判别力),ρ 只是佐证;
     本 harness 只读 + 报告,绝不据此挑改动(改动出处全在 B4/PHASE1,见 spec §4)。

方法:
  - join:targets.parquet(read_pct)+ features.parquet + hook_power_features.parquet,on aid
  - 5-fold:KFold(n_splits=5, shuffle=True, random_state=42)(沿用 PHASE1 5-fold + xhs critic_v3 KFold(5))
  - held-out 50:固定 seed 抽 50 aid,完全不参与任何折/任何阈值检视,单独报 ρ(防过拟合)
  - 跨账号 Spearman ρ(proxy vs read_pct)

用法:python tools/w9_signal_validation.py  → 打印 JSON 报告
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
HELDOUT_N = 50
SEED = 42

# W9 维度 → parquet proxy 列 + 动作(cut=砍维 / cut_gate=砍坏掉的 gate / tune=调阈值 / keep=保留)
PROXY_MAP = [
    ("opening 真实首段字数 (tune ≥50→≥25)", "b_first_para_chars", "tune"),
    ("title 致命组合 tb_ratio (cut risk 门)", "tb_ratio", "cut_gate"),
    ("title 7钩子-反共识 (tune hard→soft)", "title_hook_anti_consensus", "tune"),
    ("title 7钩子-情绪 (tune hard→soft)", "title_hook_emotion", "tune"),
    ("opening 第一人称 (keep)", "first_para_first_person_open", "keep"),
    ("opening 反差/事件引入 (cut proxy)", "first_para_event_intro", "cut"),
    ("opening 情绪开头 (cut 动词维 proxy)", "first_para_emotional_open", "cut"),
]


def load_joined() -> pd.DataFrame:
    feats = pd.read_parquet(ROOT / "features.parquet")
    hook = pd.read_parquet(ROOT / "hook_power_features.parquet")
    tgt = pd.read_parquet(ROOT / "targets.parquet")[["aid", "account_slug", "read_pct"]]
    df = (tgt.merge(feats, on=["aid", "account_slug"], how="inner")
             .merge(hook, on=["aid", "account_slug"], how="inner"))
    return df


def spearman_safe(x, y):
    """去 NaN + 常数保护的 Spearman ρ. Returns (rho, p, n) or (None, None, n)."""
    x = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy()
    y = pd.to_numeric(pd.Series(y), errors="coerce").to_numpy()
    m = (~np.isnan(x)) & (~np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return None, None, int(len(x))
    rho, p = spearmanr(x, y)
    return float(rho), float(p), int(len(x))


def run() -> dict:
    df = load_joined()
    rng = np.random.default_rng(SEED)
    idx = np.arange(len(df))
    rng.shuffle(idx)
    held_idx, train_idx = idx[:HELDOUT_N], idx[HELDOUT_N:]
    df_train = df.iloc[train_idx].reset_index(drop=True)
    df_held = df.iloc[held_idx].reset_index(drop=True)

    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    report = {
        "method": "5-fold KFold(seed=42) + held-out 50 cross-account Spearman ρ vs read_pct (proxy)",
        "caveat": "proxy ≠ 信号工具精确输出;砍维度主证据是 B4 零方差,ρ 只佐证;只读不据此调参",
        "n_total": int(len(df)),
        "n_train": int(len(df_train)),
        "n_heldout": int(len(df_held)),
        "dims": {},
    }

    for label, col, action in PROXY_MAP:
        if col not in df.columns:
            report["dims"][label] = {"col": col, "error": "column missing"}
            continue
        fold_rhos = []
        for _, test_i in kf.split(df_train):
            r, _, _ = spearman_safe(df_train.iloc[test_i][col], df_train.iloc[test_i]["read_pct"])
            if r is not None:
                fold_rhos.append(r)
        overall_rho, overall_p, _ = spearman_safe(df_train[col], df_train["read_pct"])
        held_rho, held_p, _ = spearman_safe(df_held[col], df_held["read_pct"])
        per_acct = {}
        for acct, g in df_train.groupby("account_slug"):
            r, pp, n = spearman_safe(g[col], g["read_pct"])
            if r is not None:
                per_acct[acct] = {"rho": round(r, 3), "p": round(pp, 4), "n": n}
        report["dims"][label] = {
            "col": col,
            "action": action,
            "overall_rho": round(overall_rho, 3) if overall_rho is not None else None,
            "overall_p": round(overall_p, 4) if overall_p is not None else None,
            "fold_rho_mean": round(float(np.mean(fold_rhos)), 3) if fold_rhos else None,
            "fold_rho_std": round(float(np.std(fold_rhos)), 3) if fold_rhos else None,
            "heldout_rho": round(held_rho, 3) if held_rho is not None else None,
            "heldout_p": round(held_p, 4) if held_p is not None else None,
            "per_account": per_acct,
        }

    # 中性判读(不据此调参):砍掉的维度 proxy 若 |ρ| 强且显著 = 可能误砍真信号 → flag
    flags = []
    for label, d in report["dims"].items():
        if d.get("action") in ("cut",) and d.get("overall_rho") is not None:
            if abs(d["overall_rho"]) >= 0.15 and (d.get("overall_p") or 1) < 0.05:
                flags.append(f"{label}: overall_rho={d['overall_rho']} p={d['overall_p']} — 砍前复核")
    report["cut_dim_strong_signal_flags"] = flags or ["none — 砍掉的维度 proxy 均无强显著正相关"]
    return report


def main(argv=None) -> int:
    print(json.dumps(run(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
