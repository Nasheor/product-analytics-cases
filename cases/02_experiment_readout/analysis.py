"""Case 2: experiment read-out on the Upworthy Research Archive.

Selects the worked example by the rule in README.md, reports its click-through rates, difference,
interval, z-test, retrospective minimum detectable effect and the stopping points of two sequential
rules on a seeded reconstruction of the impression stream. Across all qualifying tests it reports the
distribution of observed lifts, the false-positive rate of peeking against an O'Brien-Fleming
boundary under null re-labelling, and the winner's curse from a seeded split of each test. Writes
``results/case2.json``, three figures and the derived per-test summaries.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from product_analytics_cases.common import Results, connect, run_sql, write_derived
from product_analytics_cases.plotting import SERIES, TEXT_2, plt, save, style
from product_analytics_cases.sequential import (
    cumulative_counts,
    diff_wilson_interval,
    mde_absolute,
    msprt_on_stream,
    null_false_positive_rates,
    obf_boundaries,
    obf_on_stream,
    reconstruct_stream,
    two_proportion_ztest,
    wilson_interval,
)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
SEED = 20261028
DRAWS = 1000
LOOKS = 5
ALPHA = 0.05


def test_summary(arms: pd.DataFrame) -> pd.DataFrame:
    """One row per qualifying test: control rate, best non-control arm, its relative lift and z-test."""
    rows = []
    for test_id, g in arms.groupby("test_id", sort=True):
        g = g.sort_values("arm_rank")
        n = g["impressions"].to_numpy()
        k = g["clicks"].to_numpy()
        ctr = k / n
        best = 1 + int(np.argmax(ctr[1:]))
        z, p = two_proportion_ztest(int(k[0]), int(n[0]), int(k[best]), int(n[best]))
        lift = 100.0 * (ctr[best] / ctr[0] - 1) if ctr[0] > 0 else np.nan
        rows.append({"test_id": test_id, "arms": len(g), "control_ctr": ctr[0], "best_arm": best, "best_ctr": ctr[best],
                     "lift_pct": lift, "abs_diff": ctr[best] - ctr[0], "z": z, "p_value": p,
                     "significant": p < ALPHA, "control_best": bool(np.argmax(ctr) == 0),
                     "test_impressions": int(n.sum())})
    return pd.DataFrame(rows)


def lift_distribution(summary: pd.DataFrame) -> dict[str, float]:
    s = summary["lift_pct"].dropna()
    return {"tests": int(len(summary)), "lift_p10_pct": float(s.quantile(0.10)), "lift_p25_pct": float(s.quantile(0.25)),
            "lift_median_pct": float(s.median()), "lift_p75_pct": float(s.quantile(0.75)), "lift_p90_pct": float(s.quantile(0.90)),
            "significant_share_pct": 100.0 * float(summary["significant"].mean()),
            "control_best_share_pct": 100.0 * float(summary["control_best"].mean())}


def tau_squared(arms: pd.DataFrame) -> float:
    """Mixing variance for the mSPRT: the variance of arm-minus-control differences across tests."""
    diffs = []
    for _, g in arms.groupby("test_id", sort=True):
        g = g.sort_values("arm_rank")
        ctr = (g["clicks"] / g["impressions"]).to_numpy()
        diffs.extend((ctr[1:] - ctr[0]).tolist())
    return float(np.var(diffs))


def winners_curse(arms: pd.DataFrame, seed: int) -> dict[str, float]:
    """Pick the winner on a seeded half of each arm's impressions, measure it on the other half."""
    rng = np.random.default_rng(seed)
    rows = []
    for test_id, g in arms.groupby("test_id", sort=True):
        g = g.sort_values("arm_rank")
        n = g["impressions"].to_numpy()
        k = g["clicks"].to_numpy()
        n1 = n // 2
        k1 = rng.hypergeometric(k, n - k, n1)
        n2, k2 = n - n1, k - k1
        c1, c2 = k1 / n1, k2 / n2
        if c1[0] == 0 or c2[0] == 0:
            continue
        best = 1 + int(np.argmax(c1[1:]))
        rows.append({"test_id": test_id, "best_arm": best, "lift_first_half_pct": 100.0 * (c1[best] / c1[0] - 1),
                     "lift_second_half_pct": 100.0 * (c2[best] / c2[0] - 1)})
    df = pd.DataFrame(rows)
    return {"tests": int(len(df)),
            "mean_lift_first_half_pct": float(df["lift_first_half_pct"].mean()),
            "mean_lift_second_half_pct": float(df["lift_second_half_pct"].mean()),
            "median_lift_first_half_pct": float(df["lift_first_half_pct"].median()),
            "median_lift_second_half_pct": float(df["lift_second_half_pct"].median()),
            "shrinkage_points": float((df["lift_first_half_pct"] - df["lift_second_half_pct"]).mean()),
            "lower_in_second_half_share_pct": 100.0 * float((df["lift_second_half_pct"] < df["lift_first_half_pct"]).mean())}


def plot_worked_example(obf: dict, msprt: dict, bounds: np.ndarray) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 6.5))
    looks = [row["look"] for row in obf["looks"]]
    z = [abs(row["z"]) for row in obf["looks"]]
    ax1.plot(looks, bounds, color=SERIES[1], marker="o", markersize=5, label="O'Brien-Fleming boundary")
    ax1.plot(looks, z, color=SERIES[0], marker="o", markersize=5, label="|z| observed")
    ax1.axhline(1.96, color=TEXT_2, linewidth=1, linestyle=":", label="fixed-sample 1.96")
    ax1.set_xticks(looks)
    ax1.set_xlabel("look (equally spaced in impressions)")
    ax1.set_ylabel("|z|")
    ax1.set_title("Worked example: group-sequential looks")
    ax1.legend(fontsize=8)
    n = [p[0] for p in msprt["path"]]
    lam = [p[1] for p in msprt["path"]]
    ax2.plot(n, lam, color=SERIES[0], label="mixture likelihood ratio")
    ax2.axhline(msprt["threshold"], color=SERIES[1], linewidth=1.5, label=f"stop at 1/alpha = {msprt['threshold']:.0f}")
    ax2.set_yscale("log")
    ax2.set_xlabel("impressions seen")
    ax2.set_ylabel("likelihood ratio (log scale)")
    ax2.set_title("Worked example: mixture SPRT path")
    ax2.legend(fontsize=8)
    return save(fig, FIG / "worked_example_sequential.png")


def plot_lifts(exp: pd.DataFrame, conf: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7.5, 4))
    bins = np.arange(-50, 101, 5)
    for df, color, label in ((exp, SERIES[0], "exploratory file"), (conf, SERIES[1], "confirmatory file")):
        s = df["lift_pct"].clip(-50, 100).dropna()
        ax.hist(s, bins=bins, histtype="step", linewidth=2, color=color, density=True, label=f"{label} (n = {len(s):,})")
    ax.axvline(0, color=TEXT_2, linewidth=1, linestyle=":")
    ax.set_xlabel("observed relative lift of the best arm against the control arm, % (clipped at -50 and 100)")
    ax.set_ylabel("density")
    ax.set_title("Observed lifts across qualifying tests")
    ax.legend(fontsize=8)
    return save(fig, FIG / "lift_distribution.png")


def plot_fpr(fpr: dict) -> Path:
    fig, ax = plt.subplots(figsize=(7, 3.6))
    rules = ["peeking", "obf", "fixed"]
    labels = ["z-test at every 1,000 impressions", "O'Brien-Fleming, five looks", "one fixed-sample test"]
    y = np.arange(len(rules))
    ax.barh(y - 0.18, [fpr[r] for r in rules], height=0.34, color=SERIES[0], label="all qualifying tests")
    ax.barh(y + 0.18, [fpr["two_arm"][r] for r in rules], height=0.34, color=SERIES[1], label="two-arm tests")
    for i, r in enumerate(rules):
        ax.text(fpr[r] + 0.4, i - 0.18, f"{fpr[r]:.1f} %", va="center", fontsize=8, color=TEXT_2)
        ax.text(fpr["two_arm"][r] + 0.4, i + 0.18, f"{fpr['two_arm'][r]:.1f} %", va="center", fontsize=8, color=TEXT_2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("false-positive rate under the null, %")
    ax.set_title("Stopping rule and false positives under the null")
    ax.legend(fontsize=8, loc="lower right")
    return save(fig, FIG / "false_positive_rates.png")


def main() -> None:
    style()
    con = connect("upworthy")
    res = Results("case2")
    res.note("dataset", "Upworthy Research Archive (exploratory and confirmatory packages)")
    res.note("licence", "CC BY 4.0")
    res.number("rows_read", int(run_sql(con, HERE, "rows_read.sql").iloc[0, 0]), "sql/rows_read.sql")

    counts = run_sql(con, HERE, "candidate_count.sql").iloc[0]
    for c in counts.index:
        res.number(f"exploratory_{c}", int(counts[c]), "sql/candidate_count.sql")
    res.number("shared_tests_between_files", int(run_sql(con, HERE, "overlap.sql").iloc[0, 0]), "sql/overlap.sql")

    arms_e = run_sql(con, HERE, "qualifying_arms.sql", {"source": "exploratory"})
    arms_c = run_sql(con, HERE, "qualifying_arms.sql", {"source": "confirmatory"})
    summ_e = test_summary(arms_e)
    summ_c = test_summary(arms_c)
    write_derived("upworthy", "test_summary_exploratory.csv", summ_e)
    write_derived("upworthy", "test_summary_confirmatory.csv", summ_c)
    for prefix, s in (("exploratory", summ_e), ("confirmatory", summ_c)):
        for k, v in lift_distribution(s).items():
            res.number(f"{prefix}_{k}", v, "sql/qualifying_arms.sql + test_summary() + lift_distribution()",
                       "%" if k.endswith("pct") else "")

    # worked example
    we = run_sql(con, HERE, "worked_example.sql")
    res.table("worked_example_arms", we, "sql/worked_example.sql")
    ctrl, var = we.iloc[0], we.iloc[1]
    nA, kA, nB, kB = int(ctrl["impressions"]), int(ctrl["clicks"]), int(var["impressions"]), int(var["clicks"])
    ctr_a, ctr_b = kA / nA, kB / nB
    lo_a, hi_a = wilson_interval(kA, nA)
    lo_b, hi_b = wilson_interval(kB, nB)
    d_lo, d_hi = diff_wilson_interval(kA, nA, kB, nB)
    z, p = two_proportion_ztest(kA, nA, kB, nB)
    pooled = (kA + kB) / (nA + nB)
    mde = mde_absolute(pooled, nA, nB)
    src = "sql/worked_example.sql + worked_example_stats()"
    res.number("we_test_id", str(ctrl["test_id"]), "sql/worked_example.sql")
    res.number("we_control_headline", str(ctrl["headline"]), "sql/worked_example.sql")
    res.number("we_variant_headline", str(var["headline"]), "sql/worked_example.sql")
    res.number("we_control_impressions", nA, "sql/worked_example.sql")
    res.number("we_variant_impressions", nB, "sql/worked_example.sql")
    res.number("we_control_clicks", kA, "sql/worked_example.sql")
    res.number("we_variant_clicks", kB, "sql/worked_example.sql")
    res.number("we_total_impressions", nA + nB, "sql/worked_example.sql")
    res.number("we_control_ctr_pct", 100 * ctr_a, src, "%")
    res.number("we_variant_ctr_pct", 100 * ctr_b, src, "%")
    res.number("we_control_ctr_wilson_lo_pct", 100 * lo_a, src, "%")
    res.number("we_control_ctr_wilson_hi_pct", 100 * hi_a, src, "%")
    res.number("we_variant_ctr_wilson_lo_pct", 100 * lo_b, src, "%")
    res.number("we_variant_ctr_wilson_hi_pct", 100 * hi_b, src, "%")
    res.number("we_diff_points", 100 * (ctr_b - ctr_a), src, "percentage points")
    res.number("we_diff_wilson_lo_points", 100 * d_lo, src, "percentage points")
    res.number("we_diff_wilson_hi_points", 100 * d_hi, src, "percentage points")
    res.number("we_relative_lift_pct", 100 * (ctr_b / ctr_a - 1), src, "%")
    res.number("we_z", z, src)
    res.number("we_p_value", p, src)
    res.number("we_mde_points", 100 * mde, src, "percentage points")
    res.number("we_mde_relative_pct", 100 * mde / pooled, src, "%")
    res.number("alpha_pct", 100 * ALPHA, src, "%")
    res.number("confidence_pct", 100 * (1 - ALPHA), src, "%")
    res.number("power_pct", 80.0, src, "%")

    bounds = obf_boundaries(LOOKS, ALPHA)
    res.table("obf_boundaries", pd.DataFrame({"look": range(1, LOOKS + 1), "z_boundary": bounds}), "sequential.obf_boundaries()")
    arm_ids, clicks = reconstruct_stream([(nA, kA), (nB, kB)], SEED)
    imps, clk = cumulative_counts(arm_ids, clicks, 2)
    obf = obf_on_stream(imps, clk, bounds)
    res.table("we_obf_looks", pd.DataFrame(obf["looks"]), "sequential.reconstruct_stream() + sequential.obf_on_stream()")
    res.number("we_obf_stop_look", obf["stop_look"] if obf["stop_look"] else "none", "sequential.reconstruct_stream() + sequential.obf_on_stream()")
    tau2 = tau_squared(arms_e)
    res.number("msprt_tau", float(np.sqrt(tau2)), "sql/qualifying_arms.sql + tau_squared()")
    ms = msprt_on_stream(imps, clk, tau2, ALPHA, every=100)
    res.number("we_msprt_stop_impressions", ms["stop_impressions"] if ms["stop_impressions"] else "none",
               "sequential.reconstruct_stream() + sequential.msprt_on_stream()")
    res.number("we_msprt_final_lambda", ms["final_lambda"], "sequential.reconstruct_stream() + sequential.msprt_on_stream()")
    res.number("we_msprt_threshold", ms["threshold"], "sequential.msprt_on_stream()")

    # across tests: false positives under the null
    sizes = [g.sort_values("arm_rank")["impressions"].astype(int).tolist() for _, g in arms_e.groupby("test_id", sort=True)]
    ctrs = [float(g["pooled_ctr"].iloc[0]) for _, g in arms_e.groupby("test_id", sort=True)]
    fpr = null_false_positive_rates(sizes, ctrs, DRAWS, SEED, bounds, peek_every=1000, alpha=ALPHA)
    fsrc = "sql/qualifying_arms.sql + sequential.null_false_positive_rates()"
    res.number("fpr_peeking_pct", fpr["peeking"], fsrc, "%")
    res.number("fpr_obf_pct", fpr["obf"], fsrc, "%")
    res.number("fpr_fixed_pct", fpr["fixed"], fsrc, "%")
    res.number("fpr_two_arm_peeking_pct", fpr["two_arm"]["peeking"], fsrc, "%")
    res.number("fpr_two_arm_obf_pct", fpr["two_arm"]["obf"], fsrc, "%")
    res.number("fpr_two_arm_fixed_pct", fpr["two_arm"]["fixed"], fsrc, "%")
    res.number("fpr_tests", fpr["tests"], fsrc)
    res.number("fpr_two_arm_tests", fpr["two_arm"]["tests"], fsrc)
    res.number("fpr_draws", fpr["draws"], fsrc)

    curse = winners_curse(arms_e, SEED)
    for k, v in curse.items():
        res.number(f"curse_{k}", v, "sql/qualifying_arms.sql + winners_curse()", "%" if k.endswith("pct") else "")

    res.figure("worked_example_sequential", plot_worked_example(obf, ms, bounds), "sequential.reconstruct_stream() + plot_worked_example()")
    res.figure("lift_distribution", plot_lifts(summ_e, summ_c), "test_summary() + plot_lifts()")
    res.figure("false_positive_rates", plot_fpr(fpr), "sequential.null_false_positive_rates() + plot_fpr()")

    ship = p < ALPHA and d_lo > 0
    verdict = "ship the variant headline" if ship else "do not ship the variant, keep the control headline"
    res.note("recommendation", verdict)
    res.note("headline", f"worked example lift {100 * (ctr_b / ctr_a - 1):+.1f} % (p = {p:.2f}), "
                         f"peeking false positives {fpr['peeking']:.1f} % vs {fpr['obf']:.1f} % with the boundary")
    out = res.write()
    print(f"case2: {out}")
    print(f"  example {ctrl['test_id']}: ctr {100*ctr_a:.3f} vs {100*ctr_b:.3f} %, diff {100*(ctr_b-ctr_a):+.3f} "
          f"[{100*d_lo:+.3f}, {100*d_hi:+.3f}], p={p:.3f}, mde {100*mde:.3f} pts, obf stop {obf['stop_look']}, "
          f"msprt stop {ms['stop_impressions']}, tau {np.sqrt(tau2):.4f}")
    print(f"  fpr {fpr}")
    print(f"  curse {curse}")


def worked_example_stats() -> None:
    """Name holder for the per-arm statistics computed inline in main(): Wilson intervals, Newcombe
    interval for the difference, pooled z-test, retrospective minimum detectable effect."""


if __name__ == "__main__":
    main()
