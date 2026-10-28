# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Case 3: metric-definition review on Olist
#
# Reads `results/case3.json` written by `analysis.py`, builds the base order table live and runs
# one metric query against it, then shows the divergence tables and the figures. The spec sheet
# is `spec_sheet.md`, the memo is `memo.md`.

# %%
import json
from pathlib import Path

import pandas as pd
from IPython.display import Image, display

from product_analytics_cases.common import CASES, RESULTS, connect, run_sql, sql_text

HERE = CASES / "03_metric_definition_review"
res = json.loads((RESULTS / "case3.json").read_text(encoding="utf-8"))
numbers = pd.DataFrame([{"key": k, **v} for k, v in res["numbers"].items()]).set_index("key")
numbers.head(60)

# %% [markdown]
# ## The base order table and one metric under three definitions

# %%
con = connect("olist")
con.execute("CREATE VIEW base_orders AS " + sql_text(HERE, "base_orders.sql"))
run_sql(con, HERE, "metric_repeat_rate.sql").tail(8)

# %%
print(Path(HERE / "sql" / "metric_repeat_rate.sql").read_text(encoding="utf-8"))

# %% [markdown]
# ## Largest monthly divergence per metric

# %%
rows = []
for key in ["gmv", "delivered_revenue", "on_time", "review_score", "active_customers", "repeat_rate"]:
    t = res["tables"][f"{key}_divergence"]
    d = pd.DataFrame(t["rows"], columns=t["columns"])
    d.insert(0, "metric", key)
    rows.append(d)
pd.concat(rows).round(2).reset_index(drop=True)

# %%
t = res["tables"]["ambiguities"]
pd.DataFrame(t["rows"], columns=t["columns"])

# %%
for key, fig in res["figures"].items():
    print(key, "from", fig["source"])
    display(Image(filename=str(RESULTS.parent / fig["file"])))
