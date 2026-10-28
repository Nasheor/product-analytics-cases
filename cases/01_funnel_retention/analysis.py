"""Case 1: order funnel and cohort retention on the Olist marketplace.

Runs the named queries in ``sql/``, derives the conversion rates, the cohort matrix, the repeat
rates and the lateness-to-review relation, writes ``results/case1.json``, three figures and the
derived aggregates under ``data/derived/olist/``. Every number in the results file names the query
or the function that produced it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from product_analytics_cases.common import Results, connect, run_sql, write_derived
from product_analytics_cases.plotting import SEQUENTIAL, SERIES, TEXT_2, plt, save, style

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
WINDOW = ("2017-01", "2018-08")        # months with a full month of orders
COHORTS_COMPLETE = ("2017-01", "2018-02")  # cohorts with 180 days of follow-up before the data end
MATRIX_COHORTS = ("2017-03", "2018-02")  # twelve cohorts shown in the matrix
STEPS = ["created", "approved", "handed_to_carrier", "delivered", "reviewed"]


def funnel_conversions(funnel: pd.DataFrame) -> pd.DataFrame:
    """Conversion of each step from the previous one, per month and over the window."""
    out = funnel.copy()
    for prev, step in zip(STEPS[:-1], STEPS[1:]):
        out[f"{step}_pct"] = 100.0 * out[step] / out[prev]
    out["cancel_pct"] = 100.0 * (out["canceled"] + out["unavailable"]) / out["created"]
    return out


def window_totals(funnel: pd.DataFrame) -> dict[str, float]:
    """Step conversions pooled over the window months, and the step with the largest loss."""
    w = funnel[(funnel["month"] >= WINDOW[0]) & (funnel["month"] <= WINDOW[1])]
    tot = w[STEPS + ["canceled", "unavailable"]].sum()
    conv = {f"{step}_pct": 100.0 * tot[step] / tot[prev] for prev, step in zip(STEPS[:-1], STEPS[1:])}
    losses = {step: 100.0 - v for step, v in conv.items()}
    worst = max(losses, key=losses.get)
    conv["cancel_pct"] = 100.0 * (tot["canceled"] + tot["unavailable"]) / tot["created"]
    conv["orders"] = int(tot["created"])
    conv["worst_step"] = worst.replace("_pct", "")
    conv["worst_step_loss_pct"] = losses[worst]
    conv["end_to_end_pct"] = 100.0 * tot["reviewed"] / tot["created"]
    return conv


def cohort_matrix(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Twelve cohorts by six months, cumulative share of customers with a second order."""
    m = cohorts[(cohorts["cohort"] >= MATRIX_COHORTS[0]) & (cohorts["cohort"] <= MATRIX_COHORTS[1])].copy()
    for k in range(1, 7):
        m[f"month_{k}_pct"] = 100.0 * m[f"m{k}"] / m["customers"]
    return m[["cohort", "customers"] + [f"month_{k}_pct" for k in range(1, 7)]].reset_index(drop=True)


def pooled_repeat(cohorts: pd.DataFrame) -> dict[str, float]:
    """Repeat rates pooled over the cohorts with a complete 180-day window."""
    c = cohorts[(cohorts["cohort"] >= COHORTS_COMPLETE[0]) & (cohorts["cohort"] <= COHORTS_COMPLETE[1])]
    n = c["customers"].sum()
    return {"customers": int(n), "repeat_1m_pct": 100.0 * c["m1"].sum() / n,
            "repeat_3m_pct": 100.0 * c["m3"].sum() / n, "repeat_6m_pct": 100.0 * c["m6"].sum() / n}


def plot_funnel(conv: pd.DataFrame) -> Path:
    w = conv[(conv["month"] >= WINDOW[0]) & (conv["month"] <= WINDOW[1])]
    fig, ax = plt.subplots(figsize=(8, 4))
    labels = {"approved_pct": "approved", "handed_to_carrier_pct": "handed to carrier",
              "delivered_pct": "delivered", "reviewed_pct": "reviewed"}
    x = np.arange(len(w))
    for i, (col, lab) in enumerate(labels.items()):
        ax.plot(x, w[col], color=SERIES[i], label=lab)
        ax.annotate(lab, (x[-1], w[col].iloc[-1]), xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=TEXT_2, va="center")
    ax.set_xticks(x[::3])
    ax.set_xticklabels(w["month"].iloc[::3], rotation=0)
    ax.set_ylabel("conversion from the previous step, %")
    ax.set_title("Olist order funnel: step conversion by purchase month")
    ax.legend(loc="lower left", ncol=4, fontsize=8)
    return save(fig, FIG / "funnel_conversion_by_month.png")


def plot_cohorts(matrix: pd.DataFrame) -> Path:
    vals = matrix[[f"month_{k}_pct" for k in range(1, 7)]].to_numpy()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.grid(False)
    im = ax.imshow(vals, cmap=SEQUENTIAL, aspect="auto", vmin=0, vmax=max(3.0, float(vals.max())))
    ax.set_yticks(range(len(matrix)))
    ax.set_yticklabels(matrix["cohort"])
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"{k} mo" for k in range(1, 7)])
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            ax.text(j, i, f"{vals[i, j]:.1f}", ha="center", va="center", fontsize=8,
                    color="white" if vals[i, j] > 0.6 * vals.max() else TEXT_2)
    ax.set_title("Share of customers with a second order within k months, %")
    fig.colorbar(im, ax=ax, shrink=0.8, label="%")
    return save(fig, FIG / "cohort_retention_matrix.png")


def plot_lateness(buckets: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    y = np.arange(len(buckets))
    ax.barh(y, buckets["mean_score"], color=SERIES[0], height=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(buckets["bucket"])
    ax.invert_yaxis()
    ax.set_xlim(0, 5)
    ax.set_xlabel("mean review score (1 to 5)")
    for i, (v, n) in enumerate(zip(buckets["mean_score"], buckets["orders"])):
        ax.text(v + 0.05, i, f"{v:.2f}  (n = {n:,})", va="center", fontsize=8, color=TEXT_2)
    ax.set_title("Review score falls with delivery lateness")
    return save(fig, FIG / "lateness_vs_review.png")


def main() -> None:
    style()
    con = connect("olist")
    res = Results("case1")
    res.note("dataset", "Olist Brazilian E-Commerce (orders, customers, reviews, payments)")
    res.note("licence", "CC BY-NC-SA 4.0")

    rows_read = int(run_sql(con, HERE, "rows_read.sql").iloc[0, 0])
    res.number("rows_read", rows_read, "sql/rows_read.sql")

    funnel = run_sql(con, HERE, "funnel_by_month.sql")
    conv = funnel_conversions(funnel)
    write_derived("olist", "funnel_by_month.csv", conv)
    res.table("funnel_by_month", conv.round(3), "sql/funnel_by_month.sql + funnel_conversions()")
    totals = window_totals(funnel)
    for k, v in totals.items():
        res.number(f"window_{k}", v, "sql/funnel_by_month.sql + window_totals()", "%" if k.endswith("pct") else "")

    hours = run_sql(con, HERE, "step_hours.sql")
    overall = hours[hours["month"].isna()].iloc[0]
    res.number("median_hours_to_approve", float(overall["approve_hours"]), "sql/step_hours.sql", "hours")
    res.number("median_hours_approve_to_carrier", float(overall["carrier_hours"]), "sql/step_hours.sql", "hours")
    res.number("median_hours_carrier_to_delivery", float(overall["deliver_hours"]), "sql/step_hours.sql", "hours")
    res.number("median_days_carrier_to_delivery", float(overall["deliver_hours"]) / 24.0, "sql/step_hours.sql", "days")
    res.table("step_hours_by_month", hours.dropna(subset=["month"]).round(2), "sql/step_hours.sql")

    cohorts = run_sql(con, HERE, "cohort_retention.sql")
    write_derived("olist", "cohort_retention.csv", cohorts)
    matrix = cohort_matrix(cohorts)
    res.table("cohort_matrix_12x6", matrix.round(3), "sql/cohort_retention.sql + cohort_matrix()")
    pooled = pooled_repeat(cohorts)
    for k, v in pooled.items():
        res.number(k, v, "sql/cohort_retention.sql + pooled_repeat()", "%" if k.endswith("pct") else "")
    res.number("customers_total", int(cohorts["customers"].sum()), "sql/cohort_retention.sql")
    res.number("customers_ever_repeat_pct", 100.0 * cohorts["ever"].sum() / cohorts["customers"].sum(),
               "sql/cohort_retention.sql", "%")

    seg = run_sql(con, HERE, "repeat_by_segment.sql", {"cohort_from": COHORTS_COMPLETE[0], "cohort_to": COHORTS_COMPLETE[1]})
    write_derived("olist", "repeat_by_segment.csv", seg)
    states = seg[seg["split"] == "state"].head(8)
    pay = seg[seg["split"] == "payment_type"]
    res.table("repeat_6m_by_state_top8", states.round(3), "sql/repeat_by_segment.sql")
    res.table("repeat_6m_by_payment_type", pay.round(3), "sql/repeat_by_segment.sql")
    big = states[states["customers"] >= 1000]
    res.number("repeat_6m_state_max_pct", float(big["repeat_6m_pct"].max()), "sql/repeat_by_segment.sql", "%")
    res.number("repeat_6m_state_max", str(big.loc[big["repeat_6m_pct"].idxmax(), "segment"]), "sql/repeat_by_segment.sql")
    res.number("repeat_6m_state_min_pct", float(big["repeat_6m_pct"].min()), "sql/repeat_by_segment.sql", "%")
    res.number("repeat_6m_state_min", str(big.loc[big["repeat_6m_pct"].idxmin(), "segment"]), "sql/repeat_by_segment.sql")
    for _, row in pay.iterrows():
        if row["customers"] >= 1000:
            res.number(f"repeat_6m_{row['segment']}_pct", float(row["repeat_6m_pct"]), "sql/repeat_by_segment.sql", "%")

    buckets = run_sql(con, HERE, "lateness_review.sql")
    res.table("lateness_buckets", buckets.round(3), "sql/lateness_review.sql")
    summary = run_sql(con, HERE, "lateness_summary.sql")
    res.table("lateness_summary", summary.round(3), "sql/lateness_summary.sql")
    late = summary[summary["delivery"] == "late"].iloc[0]
    ontime = summary[summary["delivery"] == "on time"].iloc[0]
    res.number("late_share_pct", float(late["share_pct"]), "sql/lateness_summary.sql", "%")
    res.number("mean_score_on_time", float(ontime["mean_score"]), "sql/lateness_summary.sql")
    res.number("mean_score_late", float(late["mean_score"]), "sql/lateness_summary.sql")
    res.number("score_gap_late", float(ontime["mean_score"]) - float(late["mean_score"]), "sql/lateness_summary.sql")
    res.number("one_star_on_time_pct", float(ontime["one_star_pct"]), "sql/lateness_summary.sql", "%")
    res.number("one_star_late_pct", float(late["one_star_pct"]), "sql/lateness_summary.sql", "%")
    worst = buckets.iloc[-1]
    res.number("mean_score_more_than_14_days_late", float(worst["mean_score"]), "sql/lateness_review.sql")
    res.number("one_star_more_than_14_days_late_pct", float(worst["one_star_pct"]), "sql/lateness_review.sql", "%")

    res.figure("funnel_conversion_by_month", plot_funnel(conv), "sql/funnel_by_month.sql + plot_funnel()")
    res.figure("cohort_retention_matrix", plot_cohorts(matrix), "sql/cohort_retention.sql + plot_cohorts()")
    res.figure("lateness_vs_review", plot_lateness(buckets), "sql/lateness_review.sql + plot_lateness()")

    res.note("headline", f"six-month repeat rate {pooled['repeat_6m_pct']:.1f} %, largest funnel loss at "
                         f"{totals['worst_step'].replace('_', ' ')} ({totals['worst_step_loss_pct']:.1f} %)")
    res.note("recommendation", "do not fund a loyalty programme yet, fix delivery lateness and instrument repeat intent")
    out = res.write()
    print(f"case1: {out}")
    print(f"  repeat 6m {pooled['repeat_6m_pct']:.2f} %, worst step {totals['worst_step']} "
          f"{totals['worst_step_loss_pct']:.2f} %, late share {late['share_pct']:.2f} %, score gap {res.numbers['score_gap_late']['value']:.2f}")


if __name__ == "__main__":
    main()
