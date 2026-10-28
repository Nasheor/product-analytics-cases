"""Case 3: metric-definition review on the Olist marketplace.

Builds one order-grain base table (``sql/base_orders.sql``), computes six metrics under three
plausible SQL definitions each, measures how far the monthly series diverge, writes the spec sheet
with a recommended definition and owner per metric, and lists the ambiguities in the source with
their counts. Writes ``results/case3.json``, ``spec_sheet.md``, two figures and the derived series.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from product_analytics_cases.common import Results, connect, run_sql, sql_text, write_derived
from product_analytics_cases.plotting import SERIES, TEXT_2, plt, save, style

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
WINDOW = ("2017-03", "2018-08")  # the months with at least 2,000 orders, after the two-month ramp

METRICS = [
    {"key": "gmv", "name": "GMV", "sql": "metric_gmv.sql", "unit": "BRL per month",
     "definitions": {"a": "item price plus freight, every order whatever its status",
                     "b": "payments received at face value, every order",
                     "c": "item price without freight, orders not cancelled or unavailable"},
     "recommended": "a", "owner": "finance analytics",
     "reason": "GMV is demand placed, so it takes every order at the value the customer agreed to. Payments carry "
               "voucher and rounding noise, and dropping freight changes the number by a sixth."},
    {"key": "delivered_revenue", "name": "Delivered revenue net of cancellations", "sql": "metric_delivered_revenue.sql",
     "unit": "BRL per month",
     "definitions": {"a": "delivered orders, item value plus freight, by purchase month",
                     "b": "delivered orders, item value plus freight, by delivery month",
                     "c": "payments of every order not cancelled or unavailable, by purchase month"},
     "recommended": "a", "owner": "finance analytics",
     "reason": "Product and marketing compare months by when the order was placed, and the last two months are "
               "restated as deliveries complete. Finance keeps definition b for recognition, labelled as such."},
    {"key": "on_time", "name": "On-time delivery rate", "sql": "metric_on_time.sql", "unit": "% of orders",
     "definitions": {"a": "delivered orders received on or before the estimated day",
                     "b": "delivered orders received before the estimated day's midnight",
                     "c": "every live order, with orders never delivered counted as not on time"},
     "recommended": "a", "owner": "logistics",
     "reason": "The promise to the customer is a day, not a midnight. Orders still in transit belong in a separate "
               "backlog metric rather than in the denominator."},
    {"key": "review_score", "name": "Average review score", "sql": "metric_review_score.sql", "unit": "stars (1 to 5)",
     "definitions": {"a": "every review row, by the month the review was created",
                     "b": "latest review per order, by purchase month",
                     "c": "latest review per delivered order, by purchase month"},
     "recommended": "b", "owner": "customer experience",
     "reason": "One vote per order, attributed to the purchase month so it lines up with the other metrics. "
               "Undelivered orders are kept because their reviews are the complaint signal."},
    {"key": "active_customers", "name": "Active customers", "sql": "metric_active_customers.sql", "unit": "customers per month",
     "definitions": {"a": "distinct customer_unique_id with any order in the month",
                     "b": "distinct customer_unique_id with a delivered order placed in the month",
                     "c": "distinct customer_id, the per-order key"},
     "recommended": "a", "owner": "growth",
     "reason": "customer_unique_id is the person. customer_id is issued per order and counts orders, which is the "
               "mistake the source invites."},
    {"key": "repeat_rate", "name": "Repeat rate", "sql": "metric_repeat_rate.sql", "unit": "% of customers or orders",
     "definitions": {"a": "share of the month's orders placed by a customer with an earlier order",
                     "b": "share of the month's customers with more than one order anywhere in the data",
                     "c": "share of the month's first-time customers back within 90 days"},
     "recommended": "c", "owner": "growth",
     "reason": "A fixed 90-day window gives every cohort the same chance to return, so months are comparable. "
               "Definition b changes every time the data are refreshed. Definition a stays as a monitoring series.",
     "window": ("2017-03", "2018-05")},
]


def divergence(series: pd.DataFrame, window: tuple[str, str]) -> pd.DataFrame:
    """Largest monthly gap between each pair of definitions, as a percent of their mean."""
    cols = [c for c in series.columns if c != "month"]
    w = series[(series["month"] >= window[0]) & (series["month"] <= window[1])].copy()
    rows = []
    for a, b in combinations(cols, 2):
        x, y = w[a].astype(float), w[b].astype(float)
        rel = 100.0 * (x - y).abs() / ((x.abs() + y.abs()) / 2.0)
        rel = rel.replace([np.inf, -np.inf], np.nan)
        i = rel.idxmax()
        rows.append({"definition_1": a, "definition_2": b, "max_divergence_pct": float(rel.max()),
                     "month": str(w.loc[i, "month"]), "value_1": float(x.loc[i]), "value_2": float(y.loc[i]),
                     "mean_divergence_pct": float(rel.mean())})
    return pd.DataFrame(rows).sort_values("max_divergence_pct", ascending=False).reset_index(drop=True)


def letter(col: str) -> str:
    return col.split("_", 1)[0]


def spec_sheet(rows: list[dict], ambiguities: pd.DataFrame) -> str:
    lines = ["# Metric spec sheet (generated by analysis.py)", "",
             "Every definition is a column of the named SQL file, computed from `sql/base_orders.sql`. "
             f"Divergence is the largest monthly gap between two definitions as a percent of their mean, over {WINDOW[0]} to {WINDOW[1]}.",
             "", "| Metric | Definitions | Largest divergence | Recommended | Why | Owner |", "|---|---|---|---|---|---|"]
    for r in rows:
        defs = "<br>".join(f"**{k}**: {v}" for k, v in r["definitions"].items())
        div = f"{r['max_divergence_pct']:.1f} % ({letter(r['max_pair'][0])} vs {letter(r['max_pair'][1])}, {r['max_month']})"
        lines.append(f"| {r['name']} (`sql/{r['sql']}`) | {defs} | {div} | **{r['recommended']}** | {r['reason']} | {r['owner']} |")
    lines += ["", "## Ambiguities in the source", "", "| Ambiguity | Count |", "|---|---|"]
    for _, a in ambiguities.iterrows():
        lines.append(f"| {a['ambiguity']} | {int(a['n']):,} |")
    lines += ["", "## The single table", "",
              "`sql/base_orders.sql` holds one row per order with purchase month, status flags, item value, freight, "
              "payments, the latest review score and the customer's order number. Every recommended definition is a "
              "GROUP BY over that table, so the six metrics reconcile to the same order count."]
    return "\n".join(lines) + "\n"


def plot_series(all_series: dict[str, pd.DataFrame]) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5))
    for ax, m in zip(axes.ravel(), METRICS):
        s = all_series[m["key"]]
        win = m.get("window", WINDOW)
        w = s[(s["month"] >= WINDOW[0]) & (s["month"] <= WINDOW[1])]
        x = np.arange(len(w))
        for i, col in enumerate([c for c in s.columns if c != "month"]):
            y = w[col].astype(float).copy()
            if m.get("window") and col.startswith("c_"):
                y[w["month"] > win[1]] = np.nan
            ax.plot(x, y, color=SERIES[i], label=letter(col))
        ax.set_xticks(x[::6])
        ax.set_xticklabels(w["month"].iloc[::6], fontsize=8)
        ax.set_title(m["name"], fontsize=10)
        ax.set_ylabel(m["unit"], fontsize=8)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle("Six metrics under three definitions each, by month", x=0.01, ha="left", fontweight="bold")
    return save(fig, FIG / "definitions_small_multiples.png")


def plot_divergence(rows: list[dict]) -> Path:
    fig, ax = plt.subplots(figsize=(8, 3.8))
    order = sorted(rows, key=lambda r: r["max_divergence_pct"])
    y = np.arange(len(order))
    ax.barh(y, [r["max_divergence_pct"] for r in order], color=SERIES[0], height=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels([r["name"] for r in order], fontsize=9)
    for i, r in enumerate(order):
        ax.text(r["max_divergence_pct"] + 1, i, f"{r['max_divergence_pct']:.1f} %  ({letter(r['max_pair'][0])} vs {letter(r['max_pair'][1])}, {r['max_month']})",
                va="center", fontsize=8, color=TEXT_2)
    ax.set_xlim(0, max(r["max_divergence_pct"] for r in rows) * 1.5)
    ax.set_xlabel("largest monthly divergence between two definitions, % of their mean")
    ax.set_title("How far plausible definitions of the same metric disagree")
    return save(fig, FIG / "max_divergence_by_metric.png")


def main() -> None:
    style()
    con = connect("olist")
    res = Results("case3")
    res.note("dataset", "Olist Brazilian E-Commerce (orders, customers, order items, payments, reviews)")
    res.note("licence", "CC BY-NC-SA 4.0")
    res.number("rows_read", int(run_sql(con, HERE, "rows_read.sql").iloc[0, 0]), "sql/rows_read.sql")
    con.execute("CREATE VIEW base_orders AS " + sql_text(HERE, "base_orders.sql"))
    res.number("base_orders_rows", int(con.execute("SELECT COUNT(*) FROM base_orders").fetchone()[0]), "sql/base_orders.sql")

    all_series: dict[str, pd.DataFrame] = {}
    rows = []
    for m in METRICS:
        s = run_sql(con, HERE, m["sql"]).sort_values("month").reset_index(drop=True)
        all_series[m["key"]] = s
        write_derived("olist", f"{m['key']}_by_definition.csv", s)
        res.table(f"{m['key']}_series", s.round(4), f"sql/{m['sql']}")
        d = divergence(s, m.get("window", WINDOW))
        res.table(f"{m['key']}_divergence", d.round(4), f"sql/{m['sql']} + divergence()")
        top = d.iloc[0]
        row = {**m, "max_divergence_pct": float(top["max_divergence_pct"]),
               "max_pair": (top["definition_1"], top["definition_2"]), "max_month": top["month"],
               "max_value_1": float(top["value_1"]), "max_value_2": float(top["value_2"]),
               "mean_divergence_pct": float(top["mean_divergence_pct"])}
        rows.append(row)
        src = f"sql/{m['sql']} + divergence()"
        res.number(f"{m['key']}_max_divergence_pct", row["max_divergence_pct"], src, "%")
        res.number(f"{m['key']}_max_pair", f"{letter(top['definition_1'])} vs {letter(top['definition_2'])}", src)
        res.number(f"{m['key']}_max_month", row["max_month"], src)
        res.number(f"{m['key']}_max_value_1", row["max_value_1"], src)
        res.number(f"{m['key']}_max_value_2", row["max_value_2"], src)
        res.number(f"{m['key']}_mean_divergence_of_max_pair_pct", row["mean_divergence_pct"], src, "%")
        res.number(f"{m['key']}_recommended", m["recommended"], "sql/" + m["sql"])
        res.number(f"{m['key']}_definitions", len(m["definitions"]), "sql/" + m["sql"])

    amb = run_sql(con, HERE, "ambiguities.sql")
    res.table("ambiguities", amb, "sql/ambiguities.sql")
    for _, a in amb.iterrows():
        key = "amb_" + "".join(ch if ch.isalnum() else "_" for ch in a["ambiguity"].lower())[:60].strip("_")
        res.number(key, int(a["n"]), "sql/ambiguities.sql")

    (HERE / "spec_sheet.md").write_text(spec_sheet(rows, amb), encoding="utf-8")
    res.figure("definitions_small_multiples", plot_series(all_series), "sql/base_orders.sql + plot_series()")
    res.figure("max_divergence_by_metric", plot_divergence(rows), "divergence() + plot_divergence()")

    worst = max(rows, key=lambda r: r["max_divergence_pct"])
    res.number("headline_metric", worst["name"], "divergence()")
    res.number("headline_divergence_pct", worst["max_divergence_pct"], "divergence()", "%")
    res.number("headline_pair", f"{letter(worst['max_pair'][0])} vs {letter(worst['max_pair'][1])}", "divergence()")
    res.number("headline_month", worst["max_month"], "divergence()")
    res.number("metrics_reviewed", len(METRICS), "divergence()")
    res.note("headline", f"{worst['name']}: definitions differ by up to {worst['max_divergence_pct']:.0f} % in a month "
                         f"({letter(worst['max_pair'][0])} vs {letter(worst['max_pair'][1])}, {worst['max_month']})")
    res.note("recommendation", "adopt the six definitions in spec_sheet.md and compute them all from base_orders")
    out = res.write()
    print(f"case3: {out}")
    for r in rows:
        print(f"  {r['name']}: max {r['max_divergence_pct']:.1f} % ({r['max_pair'][0]} vs {r['max_pair'][1]}, {r['max_month']}), mean {r['mean_divergence_pct']:.1f} %")


if __name__ == "__main__":
    main()
